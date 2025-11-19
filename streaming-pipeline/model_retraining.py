#!/usr/bin/env python3
"""
Decision Tree training on 100% data with 21 features
Saves model to /opt/data/models/fraud_dt_21features
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp, col
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Create Spark session
    spark = SparkSession.builder \
        .appName("HSBC-Training-DecisionTree-21feat") \
        .getOrCreate()


    def main():
        # Create Spark session
        spark = SparkSession.builder \
            .appName("HSBC-Training-DecisionTree-21feat") \
            .getOrCreate()

        # Load data
        logger.info("Loading fraudTrain.csv...")
        df = spark.read.csv("/opt/data/raw/fraudTrain.csv", header=True, inferSchema=True)

        # Sample 50%
        df = df.sample(fraction=0.5, seed=42)
        logger.info(f"Using {df.count()} rows")

        # Preprocessing
        if 'trans_date_trans_time' in df.columns:
            df = df.withColumn('transaction_time', to_timestamp(col('trans_date_trans_time')))
        if 'amt' in df.columns:
            df = df.withColumnRenamed('amt', 'amount')
        df = df.withColumn('label', col('is_fraud').cast('int'))

        # Import feature engineer from shared apps
        import sys
        sys.path.append('/opt/spark-apps')

    # Load data
    logger.info("Loading fraudTrain.csv...")
    df = spark.read.csv("/opt/data/raw/fraudTrain.csv", header=True, inferSchema=True)

    # Use 100% data (no sampling)
    logger.info(f"Using 100% data: {df.count()} rows")

    # Preprocessing
    if 'trans_date_trans_time' in df.columns:
        df = df.withColumn('transaction_time', to_timestamp(col('trans_date_trans_time')))
    if 'amt' in df.columns:
        df = df.withColumnRenamed('amt', 'amount')
    df = df.withColumn('label', col('is_fraud').cast('int'))

    # Import feature engineer from shared apps
    import sys
    sys.path.append('/opt/spark-apps')
    from feature_engineering import FeatureEngineer

    fe = FeatureEngineer()
    df = fe.engineer_features(df)

    features = fe.get_feature_columns()

    # Pipeline stages
    cat_idx = StringIndexer(inputCol='category', outputCol='category_idx', handleInvalid='keep')

    assembler = VectorAssembler(inputCols=features['numeric'] + ['category_idx'], outputCol='features', handleInvalid='skip')

    dt = DecisionTreeClassifier(
        featuresCol='features', 
        labelCol='label', 
        maxDepth=30, 
        minInstancesPerNode=10,
        minInfoGain=0.0,
        maxBins=64,
        impurity='gini',
        seed=42
    )

    pipeline = Pipeline(stages=[cat_idx, assembler, dt])

    # Train/test split
    train, test = df.randomSplit([0.8, 0.2], seed=42)
    logger.info(f"Training: {train.count()}, Testing: {test.count()}")

    logger.info("Training DecisionTree model...")
    model = pipeline.fit(train)

    # Evaluate
    predictions = model.transform(test)
    evaluator = BinaryClassificationEvaluator(labelCol='label')
    auc = evaluator.evaluate(predictions)
    logger.info(f"✅ AUC-ROC: {auc:.4f}")

    # Save model
    out_path = "/opt/data/models/fraud_dt_21features"
    model.write().overwrite().save(out_path)
    logger.info(f"✅ DecisionTree model saved to {out_path}")

    spark.stop()


if __name__ == "__main__":
    main()

