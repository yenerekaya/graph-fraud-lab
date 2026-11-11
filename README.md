# Graph Fraud Lab

[![Tests](https://github.com/yenerekaya/graph-fraud-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/yenerekaya/graph-fraud-lab/actions/workflows/tests.yml)

**Follow the connections. Inspect the evidence.**

An explainable transaction-graph investigation project built with Python and NetworkX. Generates synthetic transfers, detects temporal graph patterns, and exports a standalone interactive investigation dashboard. No API keys, cloud account, or frontend build step required.

Version 0.2 adds transaction search and filters, CSV export, chronological route investigation, and Neo4j import files.

[Prebuilt investigation dashboard](artifacts/index.html) — download the HTML file and open it in your browser.

## Quick start

Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
graph-fraud-lab --seed 42 --output artifacts
python -m http.server 8000 --directory artifacts
```

Open http://localhost:8000. You can also open `artifacts/index.html` directly: the dashboard embeds all its data and has no external dependencies.

The committed `artifacts/` directory contains a reproducible seed-42 example ready to inspect without installing Python packages.

## What it detects

| Signal | Rule | Points |
| --- | --- | --- |
| Rapid cycle | 3–5 distinct accounts transfer in chronological order, closing the ring within 30 minutes; every amount stays within 10% of the first | 65 |
| Fan-in / fan-out | At least 6 distinct counterparties within 10 minutes; transfers of at least 500 synthetic units | 55 each |
| Pass-through | An incoming transfer of at least 2,000 units is followed within 30 minutes by forwarding 90–100% to a different counterparty | 60 |

Each rule contributes at most once per account. Scores sum to a maximum of 100. The default review threshold is 50. Scores represent heuristic signal strength, **not fraud probabilities**. Every signal includes its supporting transaction IDs.

NetworkX's [bounded directed cycle enumeration](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cycles.simple_cycles.html) provides candidate rings. Temporal and amount constraints filter these candidates. Repeated transfers are aggregated for graph topology but retained individually for temporal checks and evidence.

## Investigation dashboard

- Directed transaction network with highlighted account connections.
- Account selection through graph nodes or keyboard-accessible table buttons.
- Account scores, rule explanations, amounts, and timestamped transaction evidence.
- Search, minimum-score filtering, a flagged-account view, and reset controls.
- Paginated transaction explorer with ID/account search, UTC date bounds, and minimum amounts.
- Filtered CSV download (spreadsheet formula prefixes are neutralized).
- Earliest-arrival chronological routes, highlighted in blue on the network.
- Account-level precision, recall, and confusion-matrix counts for generated data.

The table's minimum-score slider filters the investigation queue; it does not change the detector's review threshold. Re-run the CLI with `--threshold 60` to change that threshold and regenerate metrics.

## Data and evaluation

The seed-42 fixture has 80 accounts and 444 transfers across seven days. Seven accounts belong to injected suspicious scenarios: a five-account ring, a collection hub, and a forwarding intermediary. Their counterparties remain labeled benign.

A legitimate merchant also receives a burst of payments. It deliberately triggers fan-in: a graph signal alone cannot establish intent. Evaluation counts this as a false positive.

Ground truth is generated separately and passed **only** to the evaluator. The detector accepts accounts and transactions; it does not read labels. `artifacts/evaluation.json` records account-level metrics at the configured threshold. `docs/seed-sweep.json` reports the same fixed rules over 10 seeds as a reproducibility check. All seeds share the same planted motifs; this is not an independent test set or a real-world performance benchmark.

## Investigate a transfer route

```bash
graph-fraud-lab --trace R0 R4 --max-hops 6 --output artifacts
```

Exports `route.json` with the earliest-arriving route through strictly increasing transaction timestamps, bounded by the hop limit (1–12). A later direct transfer can lose to an earlier multi-hop route. This is a temporal walk: accounts may recur. Amounts are not required to match, so the route is evidence of connectivity, not a claim that the same money moved along it.

The dashboard route finder uses the transaction explorer's current filters. Date fields cover whole UTC days, inclusive at both displayed endpoints; internally the upper bound is next-day midnight, exclusive. Transaction filters affect the table, download, and route finder. They do not recalculate account scores, metrics, or the full network.

## Neo4j export

Every run creates `neo4j/gfl_accounts.csv`, `neo4j/gfl_transfers.csv`, `neo4j/import.cypher`, and `neo4j/queries.cypher`.

The graph model is `(GFLAccount)-[:SENT]->(GFLTransfer)-[:TO]->(GFLAccount)`. Individual transfers are nodes with unique IDs, preserving parallel payments. Account scores and rule names are imported from Python.

See [Neo4j import instructions](docs/neo4j.md). CSV round trips and live imports were verified against Neo4j Community 5.26.33, including repeated import, record counts, amounts, timestamps, scores, and empty rule lists.

## Bring your own synthetic data

```bash
graph-fraud-lab --input sample.json --output custom-artifacts
```

```json
{
  "accounts": ["A", "B"],
  "transactions": [
    {"id": "T001", "source": "A", "target": "B", "amount": 850,
     "timestamp": "2026-01-01T12:00:00+00:00"}
  ]
}
```

Account IDs and transaction IDs must be unique. Transfers require declared, distinct endpoints, finite positive amounts, and timezone-aware ISO timestamps. Use a single currency or normalize amounts before analysis. Custom input produces no evaluation metrics because labels are unavailable.

## Outputs

| File | Contents |
| --- | --- |
| `index.html` | Self-contained interactive dashboard |
| `transactions.json` / `.csv` | Input accounts and individual transfers / transfer rows |
| `analysis.json` | Scores, graph edges, rule configuration and evidence |
| `ground_truth.json` | Scenario labels, generated datasets only |
| `evaluation.json` | Account-level evaluation and limitations |
| `route.json` | Chronological route, when `--trace` is provided |
| `neo4j/` | Accounts/transfers CSVs, import script and example queries |

## Development

```bash
python -m pytest
node tests/dashboard-core.test.cjs
node tests/dashboard-controller.test.cjs
```

Tests cover chronological vs. topological rings, amount constraints, counterparties, legitimate refunds, repeated edges, invalid inputs, evaluation, safe dashboard embedding, chronological routes, date boundaries, CSV export, and Neo4j record preservation. Node tests check the investigation algorithms and dashboard controller with DOM/canvas stubs; these do not replace visual browser verification. GitHub Actions runs the suite on Python 3.11–3.13 and checks that the CLI exports successfully.

```text
src/graph_fraud_lab/
  data.py          # deterministic fixture generator
  detect.py        # graph construction, temporal rules and evaluator
  cli.py           # input, exports and dashboard assembly
  investigate.py   # transaction filters and chronological routes
  neo4j.py         # CSV and Cypher export
  dashboard-core.js # testable browser investigation algorithms
  dashboard.html   # dependency-free investigation interface
```

## Scope and next steps

This is a small offline investigation lab. It uses whole-dataset batch analysis and hand-set rule weights, with no training or calibrated probability model. Bounded cycle enumeration can still become expensive on dense graphs; temporal scans are designed for small fixtures. It is not a streaming engine.

Possible extensions: live Neo4j integration tests; a time-based evaluation dataset; comparison against a feature-based anomaly detector; amount-normalized multi-currency input.

## Author

Yener Emirhan Kaya

## License

MIT. See [LICENSE](LICENSE).
