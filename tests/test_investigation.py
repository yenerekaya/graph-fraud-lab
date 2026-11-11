import csv
import json
import subprocess
import sys
import pytest
from graph_fraud_lab.data import generate
from graph_fraud_lab.detect import analyze
from graph_fraud_lab.investigate import filter_transactions, trace_route
from graph_fraud_lab.neo4j import export_neo4j
from test_detection import fixture


def test_filter_inclusive_start_exclusive_end_and_amount():
    data=fixture([("a","b",100,0),("a","c",500,5),("b","c",800,10)])
    rows=filter_transactions(data["transactions"],start="2026-01-01T00:05:00Z",end="2026-01-01T00:10:00Z",min_amount=500,query=" A ")
    assert [r["id"] for r in rows] == ["1"]
    assert filter_transactions(data["transactions"],query="missing") == []


@pytest.mark.parametrize("options", [{"start":"2026-01-01"},{"start":"2026-01-02T00:00:00Z","end":"2026-01-01T00:00:00Z"},{"min_amount":-1},{"min_amount":float("nan")}])
def test_invalid_filters(options):
    with pytest.raises(ValueError):
        filter_transactions([],**options)


def test_route_requires_time_order_and_honors_hop_limit():
    data=fixture([("a","b",100,5),("b","c",90,2),("b","c",80,6)])
    assert [r["id"] for r in trace_route(data,"a","c")["transactions"]] == ["0","2"]
    assert not trace_route(data,"a","c",max_hops=1)["found"]
    assert not trace_route(data,"c","a")["found"]


def test_route_prefers_earlier_arrival_over_fewer_hops():
    data=fixture([("a","c",100,10),("a","b",100,1),("b","c",100,2)])
    assert trace_route(data,"a","c")["accounts"] == ["a","b","c"]


def test_simultaneous_transfers_cannot_form_route():
    data=fixture([("a","b",100,1),("b","c",100,1)])
    assert not trace_route(data,"a","c")["found"]


@pytest.mark.parametrize("source,target,hops", [("missing","a",6),("a","a",6),("a","b",0),("a","b",13)])
def test_invalid_route_inputs(source,target,hops):
    with pytest.raises(ValueError):
        trace_route(fixture([("a","b",100,0)]),source,target,max_hops=hops)


def test_neo4j_export_roundtrip_preserves_parallel_transfers_and_quoted_ids(tmp_path):
    data=fixture([('a,"quoted"','b',100,0),('a,"quoted"','b',200,1)])
    result=analyze(data);export_neo4j(result,tmp_path)
    accounts=list(csv.DictReader((tmp_path/"gfl_accounts.csv").open()))
    transfers=list(csv.DictReader((tmp_path/"gfl_transfers.csv").open()))
    assert {r["id"] for r in accounts} == set(data["accounts"])
    assert [r["id"] for r in transfers] == ["0","1"]
    assert transfers[0]["source"] == 'a,"quoted"'
    assert sum(float(r["amount"]) for r in transfers) == 300
    assert "MERGE (t:GFLTransfer {id: row.id})" in (tmp_path/"import.cypher").read_text()
    assert (tmp_path/"queries.cypher").is_file()


def test_cli_route_and_packaged_assets(tmp_path):
    subprocess.run([sys.executable,"-m","graph_fraud_lab.cli","--trace","R0","R4","--output",str(tmp_path)],check=True,capture_output=True)
    route=json.loads((tmp_path/"route.json").read_text())
    assert route["accounts"] == ["R0","R1","R2","R3","R4"]
    html=(tmp_path/"index.html").read_text()
    assert "__CORE__" not in html and "__PAYLOAD__" not in html
    assert "function traceRoute" in html
    assert len(list(csv.DictReader((tmp_path/"neo4j/gfl_transfers.csv").open()))) == 444


def test_reused_output_removes_stale_route(tmp_path):
    (tmp_path/"route.json").write_text("{}")
    subprocess.run([sys.executable,"-m","graph_fraud_lab.cli","--output",str(tmp_path)],check=True,capture_output=True)
    assert not (tmp_path/"route.json").exists()
