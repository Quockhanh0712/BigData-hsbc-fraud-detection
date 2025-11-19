#!/usr/bin/env python3
"""
RandomForest Model Retraining Script with 21 Features
- Uses 100% fraudTrain.csv data (no sampling)
- Trains RandomForest with 200 trees, max_features='sqrt'
- Saves model to /opt/data/models/fraud_rf_21features
"""

import logging
import sys
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline
from pyspark.mllib.evaluation import BinaryClassificationMetrics
import feature_engineering

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def train_rf_model():
    """Train RandomForest model with 200 trees on 100% data"""
    
    spark = SparkSession.builder \
        .appName("FraudDetection_RF_Training_21Features") \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .getOrCreate()
    
    try:
        # 1. Load full training data (100% data)
        logger.info("Loading fraudTrain.csv from local file...")
        df = spark.read.csv(
            '/opt/data/raw/fraudTrain.csv',
            header=True,
            inferSchema=True
        )
        
        logger.info(f"Using 100% data: {df.count()} rows")
        
        # 2. Feature engineering (21 features)
        logger.info("Applying feature engineering (21 features)...")
        fe = feature_engineering.FeatureEngineer()
        df = fe.engineer_features(df)
        
        feature_cols = [
            'amt', 'age', 'city_pop', 'hour', 'day_of_week', 'day_of_month',
            'is_weekend', 'hour_sin', 'hour_cos', 'amt_log', 'lat', 'long',
            'merch_lat', 'merch_long', 'distance_km', 'amt_per_age',
            'amt_per_city_pop', 'lat_long_interaction', 'merch_lat_long_interaction',
            'hour_amt_interaction', 'age_city_pop_interaction'
        ]
        
        logger.info(f"Feature columns (21): {feature_cols}")
        
        # 3. Prepare label column
        indexer = StringIndexer(inputCol='is_fraud', outputCol='label')
        
        # 4. Assemble features
        assembler = VectorAssembler(inputCols=feature_cols, outputCol='features')
        
        # 5. RandomForest Classifier - PySpark equivalent config
        rf = RandomForestClassifier(
            featuresCol='features',
            labelCol='label',
            numTrees=200,              # n_estimators=200
            maxDepth=30,               # Max depth for each tree
            minInstancesPerNode=2,     # Default for RF
            featureSubsetStrategy='sqrt',  # max_features='sqrt'
            impurity='gini',
            seed=41                    # random_state=41
        )
        
        # 6. Create pipeline
        pipeline = Pipeline(stages=[indexer, assembler, rf])
        
        # 7. Train/test split
        logger.info("Splitting data: 80% train, 20% test...")
        train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
        
        logger.info(f"Training set: {train_df.count()} rows")
        logger.info(f"Test set: {test_df.count()} rows")
        
        # 8. Train model
        logger.info("Training RandomForest model with 200 trees...")
        model = pipeline.fit(train_df)
        
        # 9. Evaluate
        logger.info("Evaluating model on test set...")
        predictions = model.transform(test_df)
        
        # Calculate AUC-ROC
        predictions_rdd = predictions.select('label', 'probability').rdd.map(
            lambda row: (float(row['probability'][1]), float(row['label']))
        )
        metrics = BinaryClassificationMetrics(predictions_rdd)
        auc_roc = metrics.areaUnderROC
        
        logger.info(f"✅ AUC-ROC: {auc_roc:.4f}")
        
        # 10. Save model
        model_path = '/opt/data/models/fraud_rf_21features'
        logger.info(f"Saving RandomForest model to {model_path}...")
        model.write().overwrite().save(model_path)
        
        logger.info(f"✅ RandomForest model saved to {model_path}")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    train_rf_model()
