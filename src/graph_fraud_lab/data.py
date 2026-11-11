"""Seeded fixture generator. Ground truth never enters the detector."""
import random
from datetime import datetime, timedelta, timezone


def generate(seed=42):
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    normal = [f"A{i:03}" for i in range(72)]
    accounts = normal + [f"R{i}" for i in range(5)] + ["COLLECTOR", "MULE", "SHOP"]
    rows = []

    def add(source, target, amount, minute):
        rows.append({"id": f"T{len(rows):04}", "source": source, "target": target,
                     "amount": round(amount, 2),
                     "timestamp": (start + timedelta(minutes=minute)).isoformat()})

    for _ in range(420):
        a, b = rng.sample(normal, 2)
        add(a, b, rng.uniform(20, 1400), rng.randrange(7 * 1440))
    for i in range(5):
        add(f"R{i}", f"R{(i+1)%5}", 4800 - i*25, 400+i*2)
    for i in range(9):
        add(normal[i], "COLLECTOR", 800+i*45, 900+i)
    add(normal[20], "MULE", 6500, 1400)
    add("MULE", normal[21], 6400, 1407)
    # Legitimate busy merchant: deliberate counterexample for the fan-in heuristic.
    for i in range(8):
        add(normal[30+i], "SHOP", 650+i*20, 1900+i)
    labels = {a: ("ring" if a.startswith("R") else
                   "fan_in" if a == "COLLECTOR" else
                   "pass_through" if a == "MULE" else "benign") for a in accounts}
    return {"accounts": accounts, "transactions": sorted(rows, key=lambda x: x["timestamp"])}, labels
