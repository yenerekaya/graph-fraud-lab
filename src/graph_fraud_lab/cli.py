import argparse
import csv
import json
from importlib.resources import files
from pathlib import Path
from .data import generate
from .detect import Config, analyze, evaluate
from .investigate import trace_route
from .neo4j import export_neo4j


def main():
    parser = argparse.ArgumentParser(description="Build a reproducible transaction graph investigation demo")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--input", type=Path, help="JSON with accounts and transactions; labels are not required")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--threshold", type=int, choices=range(1,101), metavar="1..100", default=50)
    parser.add_argument("--trace", nargs=2, metavar=("SOURCE", "TARGET"), help="Export an earliest-arrival chronological route")
    parser.add_argument("--max-hops", type=int, choices=range(1,13), default=6, metavar="1..12")
    args = parser.parse_args()
    if args.input:
        dataset = json.loads(args.input.read_text())
        labels = None
    else:
        dataset, labels = generate(args.seed)
    result = analyze(dataset, Config(threshold=args.threshold))
    metrics = evaluate(result, labels) if labels else None
    try:
        route = trace_route(dataset, *args.trace, max_hops=args.max_hops) if args.trace else None
    except ValueError as error:
        parser.error(str(error))
    args.output.mkdir(parents=True, exist_ok=True)
    def write_json(name, value):
        (args.output/name).write_text(json.dumps(value, indent=2)+"\n")
    write_json("transactions.json", dataset)
    write_json("analysis.json", result)
    export_neo4j(result, args.output/"neo4j")
    if route is not None:
        write_json("route.json", route)
    else:
        (args.output/"route.json").unlink(missing_ok=True)
    if labels:
        write_json("ground_truth.json", labels)
    else:
        (args.output/"ground_truth.json").unlink(missing_ok=True)
    write_json("evaluation.json", {"seed": args.seed if labels else None, "metrics": metrics,
        "note": "Synthetic fixture evaluation only; not evidence of real-world fraud detection performance."})
    with (args.output/"transactions.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "source", "target", "amount", "timestamp"])
        writer.writeheader(); writer.writerows(dataset["transactions"])
    payload = {**result, "evaluation": metrics, "seed": args.seed if labels else None}
    # Escape less-than so untrusted IDs cannot close the embedded JSON script element.
    raw = json.dumps(payload).replace("<", "\\u003c")
    template = files("graph_fraud_lab").joinpath("dashboard.html").read_text()
    core = files("graph_fraud_lab").joinpath("dashboard-core.js").read_text()
    template = template.replace("__CORE__", core)
    (args.output/"index.html").write_text(template.replace("__PAYLOAD__", raw))
    print(json.dumps({"summary": result["summary"], "evaluation": metrics}, indent=2))
    print(f"Dashboard: {(args.output/'index.html').resolve()}")


if __name__ == "__main__":
    main()
