#!/bin/bash

echo "=========================================="
echo "PHASE 4: MODEL TRAINING"
echo "Dataset: fraudTrain.csv (23 columns)"
echo "=========================================="

# Check if model already exists
if docker exec spark-master test -d /opt/models/fraud_detection_rf 2>/dev/null; then
    echo "⚠️  Model already exists!"
    echo "To retrain, delete the model first:"
    echo "  docker exec spark-master rm -rf /opt/models/fraud_detection_rf"
    exit 0
fi

# Check if data exists in MinIO
echo "Checking data in MinIO..."
sleep 2

echo ""
echo "Starting training job..."
echo "Expected time: 10-15 minutes"
echo ""

# Submit Spark job
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --executor-cores 2 \
  --num-executors 2 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4 \
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
  --conf spark.hadoop.fs.s3a.access.key=admin \
  --conf spark.hadoop.fs.s3a.secret.key=password123 \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.sql.shuffle.partitions=50 \
  /opt/spark-apps/model_retraining.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ TRAINING COMPLETED!"
    echo "=========================================="
    echo ""
    echo "Verify model:"
    echo "  docker exec spark-master ls -lh /opt/models/"
    echo ""
    echo "Check Spark UI:"
    echo "  http://localhost:8080"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ TRAINING FAILED!"
    echo "=========================================="
    echo ""
    echo "Check logs:"
    echo "  docker logs spark-master"
    exit 1
fi
