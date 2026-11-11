# Verification — 11 November 2026

Tested commit scope: transaction exploration, chronological routes, Neo4j export and import.

- Python suite with live Neo4j enabled: **34 passed** (31 standard tests + 3 opt-in integration tests).
- JavaScript investigation core: **17 assertions passed**.
- Dashboard controller with DOM/canvas stubs: **13 smoke assertions passed**.
- Additional independent checks: 500 randomly generated chronological route cases compared with exhaustive search; 500 JavaScript/Python filter comparisons; 100 seeded datasets checked for score bounds and valid evidence references.
- CLI end-to-end: threshold 60, R0-to-R4 route, full CSV exports, embedded dashboard assets.

## Live Neo4j

Neo4j Community **5.26.33**, running in a dedicated local Docker container without published host ports.

Verified repeated import with **80 accounts, 444 transfers, 888 relationships**, exactly one sender and recipient per transfer, score totals, flagged counts, amount totals, timestamp conversion, and all example Cypher queries.

Live testing found a real import issue: empty CSV rule cells became null and removed the `rules` property from benign accounts. The import now uses `coalesce` and an explicit empty-list fallback. Regression tests confirm all 72 zero-score accounts retain `rules = []`.

The integration suite is opt-in; default CI does not start Neo4j. See [Neo4j instructions](neo4j.md).

## Browser limitation

Real browser interactions and visual layout remain **unverified**. The browser tool rejected local preview access because of a saved user permission setting. Controller stubs do not verify browser rendering, hit-testing or actual file downloads. No browser result is claimed.

## Follow-up from a user-provided browser screenshot

The supplied desktop screenshot confirmed that the dashboard rendered the expected 80 accounts, 444 transfers, 8 flagged accounts and 430 connections. It also exposed a graph layout defect: individual coordinate clamping accumulated nodes along the viewport borders.

The simulation now runs in free coordinates and its output is fitted uniformly into the viewport. A regression test runs 230 simulation steps at three viewport sizes and verifies bounds, distinct positions, geometry preservation and absence of border accumulation. Controller tests also verify node selection using the displayed coordinates (14 smoke assertions total).

The corrected layout still needs confirmation in a refreshed browser screenshot. Automated real-browser interaction and actual CSV downloading remain unverified because of the saved permission block.
