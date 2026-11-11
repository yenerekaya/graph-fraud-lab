// Use a separate database per dataset. Copy the two CSV files to Neo4j's import directory.
// Transfer nodes retain individual transaction identity even for repeated account pairs.
CREATE CONSTRAINT gfl_account_id IF NOT EXISTS FOR (a:GFLAccount) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT gfl_transfer_id IF NOT EXISTS FOR (t:GFLTransfer) REQUIRE t.id IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///gfl_accounts.csv' AS row
MERGE (a:GFLAccount {id: row.id})
SET a.score = toInteger(row.score),
    a.rules = CASE WHEN coalesce(row.rules, '') = '' THEN [] ELSE split(row.rules, '|') END;

LOAD CSV WITH HEADERS FROM 'file:///gfl_transfers.csv' AS row
MATCH (a:GFLAccount {id: row.source}), (b:GFLAccount {id: row.target})
MERGE (t:GFLTransfer {id: row.id})
SET t.amount = toFloat(row.amount), t.timestamp = datetime(row.timestamp)
MERGE (a)-[:SENT]->(t)
MERGE (t)-[:TO]->(b);
