// Account scores exported from Python; this does not reimplement the detector.
MATCH (a:GFLAccount) WHERE a.score >= 50
RETURN a.id AS account, a.score AS score, a.rules AS rules
ORDER BY score DESC, account;

// Inspect individual transfers around the synthetic collection hub.
MATCH (sender:GFLAccount)-[:SENT]->(t:GFLTransfer)-[:TO]->(receiver:GFLAccount)
WHERE sender.id = 'COLLECTOR' OR receiver.id = 'COLLECTOR'
RETURN sender.id, t.id, t.amount, t.timestamp, receiver.id
ORDER BY t.timestamp;

// Distinct senders over the entire dataset (not the Python time-window rule).
MATCH (sender:GFLAccount)-[:SENT]->(t:GFLTransfer)-[:TO]->(receiver:GFLAccount)
WITH receiver, count(DISTINCT sender) AS senders, sum(t.amount) AS received
RETURN receiver.id, senders, received
ORDER BY senders DESC LIMIT 20;

// Verify import counts; the committed seed-42 demo expects 80 and 444.
MATCH (a:GFLAccount) RETURN count(a) AS accounts;
MATCH (t:GFLTransfer) RETURN count(t) AS transfers;
