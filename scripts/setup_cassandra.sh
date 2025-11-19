#!/bin/bash
echo "======================================================"
echo "PHASE 1: SETTING UP CASSANDRA SCHEMA (23-COLUMN DATASET)"
echo "======================================================"

echo "Waiting for Cassandra to be ready..."
# Give Cassandra some time to initialize, especially on first run
sleep 25 

# Loop until cqlsh is available
until docker exec cassandra_new cqlsh -e "SELECT now() FROM system.local;" > /dev/null 2>&1; do
    echo "Cassandra is not ready yet. Waiting 5 more seconds..."
    sleep 5
done
echo "✅ Cassandra is ready!"

echo "Executing CQL script to create keyspace and tables..."
docker exec -i cassandra_new cqlsh << 'EOF'

CREATE KEYSPACE IF NOT EXISTS hsbc 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE hsbc;

DROP TABLE IF EXISTS fraud_alerts;

CREATE TABLE fraud_alerts (
    transaction_time TIMESTAMP,
    transaction_id TEXT,
    amount DOUBLE,
    merchant TEXT,
    category TEXT,
    cc_num TEXT,
    first TEXT,
    last TEXT,
    gender TEXT,
    job TEXT,
    state TEXT,
    city TEXT,
    zip TEXT,
    is_fraud INT,
    fraud_probability DOUBLE,
    detected_at TIMESTAMP,
    PRIMARY KEY (transaction_time, transaction_id)
) WITH CLUSTERING ORDER BY (transaction_id ASC)
  AND default_time_to_live = 2592000;

CREATE INDEX IF NOT EXISTS ON fraud_alerts (detected_at);
CREATE INDEX IF NOT EXISTS ON fraud_alerts (category);
CREATE INDEX IF NOT EXISTS ON fraud_alerts (state);
CREATE INDEX IF NOT EXISTS ON fraud_alerts (merchant);

DESCRIBE TABLE fraud_alerts;

EOF

echo "======================================================"
echo "✅ Cassandra schema setup completed!"
echo "======================================================"
