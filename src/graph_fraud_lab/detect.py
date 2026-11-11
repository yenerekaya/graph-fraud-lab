"""Deterministic graph and temporal rules. Scores are signals, not probabilities."""
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
import networkx as nx


@dataclass(frozen=True)
class Config:
    cycle_max_length: int = 5
    cycle_window_minutes: int = 30
    fan_window_minutes: int = 10
    fan_min_counterparties: int = 6
    fan_min_amount: float = 500
    pass_window_minutes: int = 30
    pass_min_amount: float = 2000
    pass_min_ratio: float = .9
    threshold: int = 50


def analyze(dataset, config=None):
    c = config or Config()
    accounts = dataset["accounts"]
    if len(accounts) != len(set(accounts)):
        raise ValueError("Account IDs must be unique")
    graph = nx.DiGraph()
    graph.add_nodes_from(accounts)
    incoming, outgoing, edge_rows = defaultdict(list), defaultdict(list), defaultdict(list)
    seen = set()
    for row in dataset["transactions"]:
        if row["id"] in seen:
            raise ValueError("Transaction IDs must be unique")
        seen.add(row["id"])
        a, b, amount = row["source"], row["target"], row["amount"]
        if a not in graph or b not in graph or a == b:
            raise ValueError("Transactions require two distinct, declared accounts")
        if not isfinite(amount) or amount <= 0:
            raise ValueError("Amounts must be positive and finite")
        dt = datetime.fromisoformat(row["timestamp"])
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("Timestamps must include a timezone")
        tx = dict(row, time=dt.timestamp())
        incoming[b].append(tx); outgoing[a].append(tx); edge_rows[a,b].append(tx)
        if graph.has_edge(a, b):
            graph[a][b]["amount"] += amount
            graph[a][b]["count"] += 1
        else:
            graph.add_edge(a, b, amount=amount, count=1)
    for values in [incoming, outgoing, edge_rows]:
        for rows in values.values():
            rows.sort(key=lambda x: (x["time"], x["id"]))
    signals = {a: [] for a in accounts}

    def signal(account, rule, points, reason, txs):
        if not any(s["rule"] == rule for s in signals[account]):
            signals[account].append({"rule": rule, "points": points, "reason": reason,
                                      "transaction_ids": [t["id"] for t in txs]})

    # Try each cycle rotation; require chronological, amount-preserving transfers.
    for cycle in nx.simple_cycles(graph, length_bound=c.cycle_max_length):
        if len(cycle) < 3:
            continue
        evidence = None
        for offset in range(len(cycle)):
            ring = cycle[offset:] + cycle[:offset]
            pairs = list(zip(ring, ring[1:] + ring[:1]))
            for first in edge_rows[pairs[0]]:
                path = [first]
                for pair in pairs[1:]:
                    match = next((t for t in edge_rows[pair]
                                  if path[-1]["time"] < t["time"] <= first["time"] + c.cycle_window_minutes*60
                                  and .9 <= t["amount"]/first["amount"] <= 1.1), None)
                    if match is None:
                        break
                    path.append(match)
                if len(path) == len(pairs):
                    evidence = path
                    break
            if evidence:
                break
        if evidence:
            for a in cycle:
                signal(a, "rapid_cycle", 65,
                       f"Chronological {len(cycle)}-account ring within {c.cycle_window_minutes} minutes; amounts within 10%.", evidence)

    for account in accounts:
        for direction, rows, peer in [("fan_in", incoming[account], "source"),
                                       ("fan_out", outgoing[account], "target")]:
            eligible = [r for r in rows if r["amount"] >= c.fan_min_amount]
            for i, first in enumerate(eligible):
                window = []
                for tx in eligible[i:]:
                    if tx["time"] - first["time"] > c.fan_window_minutes*60:
                        break
                    window.append(tx)
                peers = {r[peer] for r in window}
                if len(peers) >= c.fan_min_counterparties:
                    signal(account, direction, 55,
                           f"{len(peers)} distinct counterparties in {c.fan_window_minutes} minutes; each transfer >= {c.fan_min_amount:g} units.", window)
                    break
        for inc in incoming[account]:
            if inc["amount"] < c.pass_min_amount:
                continue
            match = next((out for out in outgoing[account]
                          if 0 < out["time"]-inc["time"] <= c.pass_window_minutes*60
                          and c.pass_min_ratio <= out["amount"]/inc["amount"] <= 1
                          and out["target"] != inc["source"]), None)
            if match:
                signal(account, "pass_through", 60,
                       f"Forwarded {match['amount']/inc['amount']:.1%} of an incoming transfer within {c.pass_window_minutes} minutes.", [inc, match])
                break
    nodes = [{"id": a, "score": min(100, sum(s["points"] for s in signals[a])),
              "signals": signals[a], "in_degree": graph.in_degree(a), "out_degree": graph.out_degree(a),
              "incoming": round(sum(t["amount"] for t in incoming[a]), 2),
              "outgoing": round(sum(t["amount"] for t in outgoing[a]), 2)} for a in accounts]
    nodes.sort(key=lambda n: (-n["score"], n["id"]))
    return {"config": asdict(c), "nodes": nodes,
            "edges": [{"source": a, "target": b, **d} for a,b,d in graph.edges(data=True)],
            "transactions": dataset["transactions"],
            "summary": {"accounts": len(nodes), "transactions": len(seen),
                        "edges": graph.number_of_edges(),
                        "flagged": sum(n["score"] >= c.threshold for n in nodes)}}


def evaluate(result, labels):
    predictions = {n["id"]: n["score"] >= result["config"]["threshold"] for n in result["nodes"]}
    if set(labels) != set(predictions):
        raise ValueError("Labels must match analyzed accounts exactly")
    tp=fp=tn=fn=0
    for account, flagged in predictions.items():
        positive = labels[account] != "benign"
        tp += int(flagged and positive); fp += int(flagged and not positive)
        tn += int(not flagged and not positive); fn += int(not flagged and positive)
    precision = tp/(tp+fp) if tp+fp else 0
    recall = tp/(tp+fn) if tp+fn else 0
    return {"unit": "account", "threshold": result["config"]["threshold"],
            "true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(2*precision*recall/(precision+recall), 4) if precision+recall else 0}
