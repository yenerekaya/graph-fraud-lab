"""Opt-in integration test; point only at a dedicated seed-42 test database.

Mount artifacts/neo4j at /var/lib/neo4j/import in the container.
GFL_NEO4J_CONTAINER and GFL_NEO4J_PASSWORD enable these tests.
No databases or records are deleted; the import merges the example fixture.
"""
import os
import subprocess
import pytest
from graph_fraud_lab.data import generate
from graph_fraud_lab.detect import analyze


@pytest.fixture(scope="module")
def live():
    container = os.getenv("GFL_NEO4J_CONTAINER")
    password = os.getenv("GFL_NEO4J_PASSWORD")
    if not container or not password:
        pytest.skip("Dedicated Neo4j test container not configured")
    command = ["docker", "exec", container, "cypher-shell", "-u", "neo4j", "-p", password]

    def run(*args):
        return subprocess.run(command + list(args), check=True, capture_output=True,
                              text=True, timeout=60).stdout.strip()

    # Import twice: repeated imports must preserve counts and field values.
    run("-f", "/var/lib/neo4j/import/import.cypher")
    run("-f", "/var/lib/neo4j/import/import.cypher")
    return run


def scalar(live, query):
    return float(live(query).splitlines()[-1])


def test_live_import_is_idempotent(live):
    assert scalar(live, "MATCH (a:GFLAccount) RETURN count(a);") == 80
    assert scalar(live, "MATCH (t:GFLTransfer) RETURN count(t);") == 444
    assert scalar(live, "MATCH ()-[r:SENT|TO]->() RETURN count(r);") == 888
    assert scalar(live, "MATCH (t:GFLTransfer) OPTIONAL MATCH (a:GFLAccount)-[:SENT]->(t) WITH t, count(a) AS senders OPTIONAL MATCH (t)-[:TO]->(b:GFLAccount) WITH t, senders, count(b) AS recipients WHERE senders <> 1 OR recipients <> 1 RETURN count(*);") == 0


def test_live_scores_and_empty_rule_lists(live):
    result = analyze(generate(42)[0])
    assert scalar(live, "MATCH (a:GFLAccount) RETURN sum(a.score);") == sum(n["score"] for n in result["nodes"])
    assert scalar(live, "MATCH (a:GFLAccount) WHERE a.score >= 50 RETURN count(a);") == 8
    # Regression: LOAD CSV reads empty cells as null; preserve [] explicitly.
    assert scalar(live, "MATCH (a:GFLAccount) WHERE a.rules IS NULL RETURN count(a);") == 0
    assert scalar(live, "MATCH (a:GFLAccount) WHERE a.score = 0 AND a.rules = [] RETURN count(a);") == 72


def test_live_amounts_timestamps_and_example_queries(live):
    rows = generate(42)[0]["transactions"]
    assert scalar(live, "MATCH (t:GFLTransfer) RETURN sum(t.amount);") == pytest.approx(sum(t["amount"] for t in rows))
    assert scalar(live, "MATCH (t:GFLTransfer) WHERE t.timestamp >= datetime('2026-01-01T00:00:00Z') AND t.timestamp < datetime('2026-01-08T00:00:00Z') RETURN count(t);") == 444
    assert scalar(live, "MATCH (a:GFLAccount {id:'R0'})-[:SENT]->(:GFLTransfer)-[:TO]->(:GFLAccount {id:'R1'}) RETURN count(*);") == 1
    assert '"COLLECTOR"' in live("-f", "/var/lib/neo4j/import/queries.cypher")
