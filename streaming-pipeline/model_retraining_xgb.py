#!/usr/bin/env python3
"""
XGBoost Model Retraining Script with 21 Features
- Uses 100% fraudTrain.csv data (no sampling)
- Trains XGBoost Classifier - best for imbalanced fraud detection
- Saves model to /opt/data/models/fraud_xgb_21features
"""

import logging
import sys
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml import Pipeline
from pyspark.mllib.evaluation import BinaryClassificationMetrics
import feature_engineering

# XGBoost imports
from xgboost.spark import SparkXGBClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def train_xgb_model():
    """Train XGBoost model on 100% data - excellent for fraud detection"""
    
    spark = SparkSession.builder \
        .appName("FraudDetection_XGB_Training_21Features") \
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
        
        # Feature columns after engineering (renamed amt -> amount)
        feature_cols = [
            'amount', 'age', 'city_pop', 'hour_of_day', 'is_weekend',
            'amount_log', 'is_high_value', 'is_extreme_value',
            'distance_customer_merchant', 'is_out_of_state',
            'amt_to_pop_ratio', 'gender_encoded',
            'cat_grocery_pos', 'cat_shopping_net', 'cat_misc_net', 
            'cat_gas_transport', 'cat_shopping_pos', 'cat_food_dining',
            'cat_personal_care', 'cat_health_fitness', 'cat_entertainment'
        ]
        
        logger.info(f"Feature columns (21): {feature_cols}")
        
        # 3. Prepare label column
        indexer = StringIndexer(inputCol='is_fraud', outputCol='label')
        
        # 4. Assemble features
        assembler = VectorAssembler(inputCols=feature_cols, outputCol='features')
        
        # 5. XGBoost Classifier - optimized for fraud detection
        xgb = SparkXGBClassifier(
            features_col='features',
            label_col='label',
            prediction_col='prediction',
            probability_col='probability',
            # XGBoost hyperparameters
            max_depth=6,                    # Depth of trees (default 6, good balance)
            learning_rate=0.3,              # Eta (step size shrinkage)
            n_estimators=100,               # Number of boosting rounds
            # objective auto-set by SparkXGBClassifier for binary classification
            subsample=0.8,                  # Subsample ratio of training instances
            colsample_bytree=0.8,           # Subsample ratio of columns
            min_child_weight=1,             # Minimum sum of instance weight
            gamma=0,                        # Minimum loss reduction
            reg_alpha=0,                    # L1 regularization
            reg_lambda=1,                   # L2 regularization
            scale_pos_weight=1,             # Balance of positive/negative weights
            eval_metric='auc',              # Evaluation metric
            seed=42,                        # Random seed
            num_workers=4                   # Parallel workers
        )
        
        # 6. Create pipeline
        pipeline = Pipeline(stages=[indexer, assembler, xgb])
        
        # 7. Train/test split
        logger.info("Splitting data: 80% train, 20% test...")
        train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
        
        logger.info(f"Training set: {train_df.count()} rows")
        logger.info(f"Test set: {test_df.count()} rows")
        
        # 8. Train model
        logger.info("Training XGBoost model (100 estimators)...")
        logger.info("⏳ This may take 5-10 minutes for 1.3M rows...")
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
        model_path = '/opt/data/models/fraud_xgb_21features'
        logger.info(f"Saving XGBoost model to {model_path}...")
        model.write().overwrite().save(model_path)
        
        logger.info(f"✅ XGBoost model saved to {model_path}")
        logger.info(f"📊 Final AUC-ROC: {auc_roc:.4f}")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    train_xgb_model()
