"""Transaction filtering and bounded, strictly chronological route discovery."""
from datetime import datetime
from math import isfinite


def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Timestamps must include a timezone")
    return dt.timestamp()


def filter_transactions(rows, *, query="", start=None, end=None, min_amount=0):
    """Start is inclusive, end exclusive. Amounts use the dataset's shared unit."""
    if not isfinite(min_amount) or min_amount < 0:
        raise ValueError("Minimum amount must be finite and non-negative")
    low = timestamp(start) if start else float("-inf")
    high = timestamp(end) if end else float("inf")
    if low >= high:
        raise ValueError("Start must precede end")
    query = query.casefold().strip()
    return [r for r in rows if low <= timestamp(r["timestamp"]) < high
            and r["amount"] >= min_amount
            and (not query or any(query in str(r[k]).casefold() for k in ("id", "source", "target")))]


def trace_route(dataset, source, target, *, max_hops=6):
    """Earliest-arrival temporal walk, bounded by hops; not a claim of fund provenance.

    Dynamic programming keeps the earliest arrival at each (account, hop count).
    Earlier arrivals dominate later ones when waiting is allowed. An account may
    recur, but transaction timestamps must increase strictly.
    """
    if source not in dataset["accounts"] or target not in dataset["accounts"]:
        raise ValueError("Choose declared source and target accounts")
    if not isinstance(max_hops, int) or not 1 <= max_hops <= 12:
        raise ValueError("Max hops must be an integer between 1 and 12")
    if source == target:
        raise ValueError("Source and target must differ")
    rows = sorted(dataset["transactions"], key=lambda r: (timestamp(r["timestamp"]), r["id"]))
    states = {source: (float("-inf"), [])}
    candidates = []
    for _ in range(max_hops):
        next_states = {}
        for row in rows:
            previous = states.get(row["source"])
            at = timestamp(row["timestamp"])
            if previous is None or previous[0] >= at:
                continue
            incumbent = next_states.get(row["target"])
            if incumbent is None or at < incumbent[0]:
                next_states[row["target"]] = (at, previous[1] + [row])
        if target in next_states:
            candidates.append(next_states[target])
        states = next_states
        if not states:
            break
    path = min(candidates, key=lambda x: (x[0], len(x[1])))[1] if candidates else []
    return {"source": source, "target": target, "max_hops": max_hops,
            "found": bool(path), "hops": len(path), "transactions": path,
            "accounts": [source] + [r["target"] for r in path] if path else [],
            "note": "Earliest arrival with strictly increasing timestamps. Connectivity does not establish that the same funds moved along this route."}
