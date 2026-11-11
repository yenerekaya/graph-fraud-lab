"""Export importable CSVs and static Cypher; no credentials or server required."""
import csv
from importlib.resources import files


def export_neo4j(result, output):
    output.mkdir(parents=True, exist_ok=True)
    with (output/"gfl_accounts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "score", "rules"])
        writer.writeheader()
        writer.writerows({"id": n["id"], "score": n["score"],
                          "rules": "|".join(s["rule"] for s in n["signals"])} for n in result["nodes"])
    with (output/"gfl_transfers.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "source", "target", "amount", "timestamp"])
        writer.writeheader()
        writer.writerows({k: r[k] for k in writer.fieldnames} for r in result["transactions"])
    for name in ["import.cypher", "queries.cypher"]:
        (output/name).write_text(files("graph_fraud_lab").joinpath(name).read_text(), encoding="utf-8")
