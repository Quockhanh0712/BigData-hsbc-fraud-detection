#!/usr/bin/env python3
"""
Enhanced Model Training v2.0
Sử dụng enhanced features
"""

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from feature_engineering import FeatureEngineer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Create Spark session
    spark = SparkSession.builder \
        .appName("HSBC-Training-Enhanced-v2") \
        .getOrCreate()
    
    # Load CSV
    logger.info("Loading fraudTrain.csv...")
    df = spark.read.csv("/opt/data/raw/fraudTrain.csv", header=True, inferSchema=True)
    
    # Sample 30% for faster training (increase from 20%)
    df = df.sample(fraction=0.3, seed=42)
    logger.info(f"Sampled: {df.count()} rows")
    
    # Rename columns
    df = df.withColumn('transaction_time', to_timestamp(col('trans_date_trans_time')))
    df = df.withColumnRenamed('amt', 'amount')
    df = df.withColumn('label', col('is_fraud').cast('int'))
    
    # Apply enhanced feature engineering
    fe = FeatureEngineer()
    df = fe.engineer_features(df)
    
    # Get feature columns
    features = fe.get_feature_columns()
    
    # Build pipeline with enhanced features
    stages = []
    
    # StringIndexer for category
    cat_idx = StringIndexer(
        inputCol='category',
        outputCol='category_idx',
        handleInvalid='keep'
    )
    stages.append(cat_idx)
    
    # StringIndexer for amount_category
    amt_cat_idx = StringIndexer(
        inputCol='amount_category',
        outputCol='amount_category_idx',
        handleInvalid='keep'
    )
    stages.append(amt_cat_idx)
    
    # VectorAssembler với enhanced features
    feature_cols = features['numeric'] + ['category_idx', 'amount_category_idx']
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol='features',
        handleInvalid='skip'
    )
    stages.append(assembler)
    
    # RandomForest với tuned hyperparameters
    rf = RandomForestClassifier(
        featuresCol='features',
        labelCol='label',
        numTrees=30,          # Tăng từ 20
        maxDepth=8,           # Tăng từ 5
        maxBins=100,          # Đủ cho category features
        minInstancesPerNode=5,
        subsamplingRate=0.8,
        featureSubsetStrategy='sqrt',
        seed=42
    )
    stages.append(rf)
    
    pipeline = Pipeline(stages=stages)
    
    # Train/test split
    train, test = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training on {train.count()} samples...")
    logger.info(f"Testing on {test.count()} samples...")
    
    # Train
    model = pipeline.fit(train)
    
    # Evaluate
    predictions = model.transform(test)
    evaluator = BinaryClassificationEvaluator(
        labelCol='label',
        metricName='areaUnderROC'
    )
    auc = evaluator.evaluate(predictions)
    
    logger.info(f"✅ AUC-ROC: {auc:.4f}")
    
    # Save model
    model.write().overwrite().save("/opt/data/models/fraud_rf_enhanced_v2")
    logger.info("✅ Enhanced model saved!")
    
    # Feature importance
    rf_model = model.stages[-1]
    feature_importance = rf_model.featureImportances
    
    logger.info("\n🎯 Top Feature Importances:")
    for i, importance in enumerate(feature_importance.toArray()[:10]):
        logger.info(f"  Feature {i}: {importance:.4f}")
    
    spark.stop()

if __name__ == "__main__":
    main()
