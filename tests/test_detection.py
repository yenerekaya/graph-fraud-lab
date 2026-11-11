import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
import pytest
from graph_fraud_lab.data import generate
from graph_fraud_lab.detect import analyze, evaluate


def fixture(events):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [{"id": str(i), "source": a, "target": b, "amount": amount,
             "timestamp": (start+timedelta(minutes=minute)).isoformat()}
            for i,(a,b,amount,minute) in enumerate(events)]
    return {"accounts": sorted({x for row in events for x in row[:2]}), "transactions": rows}


def rules(result, account):
    return {s["rule"] for n in result["nodes"] if n["id"] == account for s in n["signals"]}


def test_seeded_reproducibility():
    assert generate(42) == generate(42)
    assert generate(42) != generate(43)


def test_chronological_ring_and_evidence():
    result = analyze(fixture([("a","b",100,0),("b","c",99,2),("c","a",98,4)]))
    assert all("rapid_cycle" in rules(result,a) for a in ["a","b","c"])
    assert len(result["nodes"][0]["signals"][0]["transaction_ids"]) == 3


@pytest.mark.parametrize("events", [
    [("a","b",100,0),("b","c",99,60),("c","a",98,120)],
    [("a","b",100,0),("b","c",99,4),("c","a",98,2)],
    [("a","b",100,0),("b","c",40,2),("c","a",30,4)],
])
def test_topological_cycle_alone_is_insufficient(events):
    assert all(not n["signals"] for n in analyze(fixture(events))["nodes"])


def test_distinct_counterparties_required():
    repeated = [("a","hub",800,i) for i in range(8)]
    assert "fan_in" not in rules(analyze(fixture(repeated)), "hub")
    unique = [(f"a{i}","hub",800,i) for i in range(8)]
    assert "fan_in" in rules(analyze(fixture(unique)), "hub")


def test_forwarding_and_refund_differ():
    assert "pass_through" in rules(analyze(fixture([("a","m",3000,0),("m","b",2900,10)])), "m")
    assert "pass_through" not in rules(analyze(fixture([("a","m",3000,0),("m","a",2900,10)])), "m")


def test_parallel_transfers_aggregate_without_losing_evidence():
    r = analyze(fixture([("a","b",10,0),("a","b",20,1)]))
    assert r["edges"] == [{"source":"a", "target":"b", "amount":30, "count":2}]
    assert len(r["transactions"]) == 2


@pytest.mark.parametrize("amount", [-1, 0, float("nan"), float("inf")])
def test_reject_bad_amount(amount):
    with pytest.raises(ValueError):
        analyze(fixture([("a","b",amount,0)]))


def test_reject_naive_timestamp():
    data=fixture([("a","b",100,0)])
    data["transactions"][0]["timestamp"]="2026-01-01T00:00:00"
    with pytest.raises(ValueError):
        analyze(data)


def test_labels_do_not_influence_detection_and_merchant_false_positive_is_reported():
    data, labels = generate()
    result = analyze(data)
    assert rules(result,"SHOP") == {"fan_in"}
    metrics = evaluate(result, labels)
    assert metrics["true_positive"] == 7
    assert metrics["false_positive"] >= 1
    assert metrics["true_positive"]+metrics["false_positive"]+metrics["true_negative"]+metrics["false_negative"] == len(data["accounts"])
    with pytest.raises(ValueError):
        evaluate(result,{})


def test_empty_graph():
    r=analyze({"accounts":[], "transactions":[]})
    assert r["summary"]["flagged"] == 0
    assert evaluate(r,{})["f1"] == 0


def test_cli_and_html_injection(tmp_path):
    data=fixture([("</script><script>alert(1)</script>","b",100,0)])
    source=tmp_path/"input.json";source.write_text(json.dumps(data))
    subprocess.run([sys.executable,"-m","graph_fraud_lab.cli","--input",str(source),"--output",str(tmp_path/"out")],check=True,capture_output=True)
    html=(tmp_path/"out/index.html").read_text()
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html
    assert json.loads((tmp_path/"out/evaluation.json").read_text())["metrics"] is None
