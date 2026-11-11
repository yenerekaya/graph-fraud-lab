# Importing into Neo4j

The export uses standard Cypher constraints and `LOAD CSV`, following the official [Neo4j CSV import guide](https://neo4j.com/docs/getting-started/data-import/csv-import/).

## Local Neo4j 5+ database

1. Generate the files: `graph-fraud-lab --output artifacts`.
2. Use a dedicated database for this dataset. Copy `artifacts/neo4j/gfl_accounts.csv` and `gfl_transfers.csv` into that database's configured import directory.
3. Open Neo4j Browser, select that database, and run the statements in `artifacts/neo4j/import.cypher` in order. Alternatively, pass the script to `cypher-shell` using its `-f` option and your own connection settings.
4. Run `queries.cypher` to inspect scores, transaction neighborhoods and import counts.

Local `file:///` imports must be enabled in the Neo4j deployment. Aura does not have access to your local import directory; use the deployment's supported data import flow instead. No credentials are bundled or required for export.

## Model

```text
(sender:GFLAccount)-[:SENT]->(transfer:GFLTransfer)-[:TO]->(receiver:GFLAccount)
```

Both node types have unique IDs. Transfer nodes keep all timestamps and amounts, including repeated payments between the same accounts. Rule names and scores come from the Python detector; the Cypher examples do not claim to reproduce the temporal rules.

Re-running the same unchanged export is idempotent because the script uses `MERGE`. Use a fresh, dedicated database for a changed dataset: IDs are reused across generator seeds and the script neither removes obsolete records nor rewires old endpoints. The importer performs no deletion.

The seed-42 demo expects 80 account nodes and 444 transfer nodes. CSV escaping and record preservation are tested automatically. Live import was verified against Neo4j Community 5.26.33. The opt-in integration suite checks repeated import (80 accounts, 444 transfers, 888 relationships), transfer endpoints, account scores, empty rule lists, amounts, timestamps, and the example queries.

Enable it only against a dedicated seed-42 test container with the exports mounted at `/var/lib/neo4j/import`:

```bash
export GFL_NEO4J_CONTAINER=your-test-container
export GFL_NEO4J_PASSWORD=your-test-password
python -m pytest tests/test_neo4j_live.py -q
```

The tests do not delete records. They import the fixture twice using `MERGE`. Empty CSV rule cells are converted to `[]` explicitly because `LOAD CSV` represents them as null.
