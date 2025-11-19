#!/bin/bash

echo "======================================"
echo "PHASE 4 TEST - Model Training"
echo "======================================"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_passed=0
test_failed=0

# Test 1: Data exists in MinIO
echo -e "\n${YELLOW}Test 1: Training data in MinIO${NC}"
if docker exec minio ls /data/hsbc-data/raw/fraudTrain.csv > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC} - fraudTrain.csv found"
    ((test_passed++))
else
    echo -e "${RED}❌ FAIL${NC} - fraudTrain.csv not found"
    ((test_failed++))
fi

# Test 2: Spark Master is running
echo -e "\n${YELLOW}Test 2: Spark Master running${NC}"
if docker ps | grep -q spark-master; then
    echo -e "${GREEN}✅ PASS${NC} - Spark Master running"
    ((test_passed++))
else
    echo -e "${RED}❌ FAIL${NC} - Spark Master not running"
    ((test_failed++))
fi

# Test 3: Training script exists
echo -e "\n${YELLOW}Test 3: Training script exists${NC}"
if docker exec spark-master test -f /opt/spark-apps/model_retraining.py; then
    echo -e "${GREEN}✅ PASS${NC} - model_retraining.py found"
    ((test_passed++))
else
    echo -e "${RED}❌ FAIL${NC} - model_retraining.py not found"
    ((test_failed++))
fi

# Test 4: Feature engineering exists
echo -e "\n${YELLOW}Test 4: Feature engineering exists${NC}"
if docker exec spark-master test -f /opt/spark-apps/feature_engineering.py; then
    echo -e "${GREEN}✅ PASS${NC} - feature_engineering.py found"
    ((test_passed++))
else
    echo -e "${RED}❌ FAIL${NC} - feature_engineering.py not found"
    ((test_failed++))
fi

# Summary
echo ""
echo "======================================"
echo "PRE-TRAINING CHECK"
echo "======================================"
echo -e "${GREEN}Passed: $test_passed${NC}"
echo -e "${RED}Failed: $test_failed${NC}"
echo "======================================"

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}✅ Ready for training!${NC}"
    echo ""
    echo "Run: make train-model"
    exit 0
else
    echo -e "${RED}❌ Please fix failed tests first${NC}"
    exit 1
fi
