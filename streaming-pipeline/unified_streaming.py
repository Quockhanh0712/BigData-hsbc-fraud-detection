#!/usr/bin/env python3
"""
Unified Streaming Pipeline - Phase 5
HOÀN CHỈNH cho dataset 23 cột
"""

import sys
sys.path.append('/opt/spark-apps')

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml import PipelineModel
import logging

from config import Config
from feature_engineering import FeatureEngineer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedStreamingPipeline:
    """
    Kappa Architecture - Single streaming pipeline
    - Real-time feature engineering (23 columns)
    - Model inference
    - Data archiving
    """
    
    def __init__(self):
        self.config = Config()
        self.spark = self.create_spark_session()
        self.feature_engineer = FeatureEngineer()
        self.model = self.load_model()
    
    def create_spark_session(self):
        """Create Spark session với config đầy đủ"""
        logger.info("Creating Spark session...")
        
        spark = SparkSession.builder \
            .appName("HSBC-Unified-Streaming-Kappa-23Cols") \
            .config("spark.jars.packages",
                   "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                   "org.apache.hadoop:hadoop-aws:3.3.4,"
                   "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0") \
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
            .config("spark.hadoop.fs.s3a.access.key", "admin") \
            .config("spark.hadoop.fs.s3a.secret.key", "password123") \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
            .config("spark.cassandra.connection.host", "cassandra") \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.sql.shuffle.partitions", "20") \
            .config("spark.streaming.kafka.consumer.poll.ms", "256") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        logger.info(f"✅ Spark session created: {spark.version}")
        
        return spark
    
    def load_model(self):
        """Load trained XGBoost model từ local storage"""
        model_path = "/opt/data/models/fraud_xgb_21features"
        
        try:
            logger.info(f"Loading XGBoost model from {model_path}")
            model = PipelineModel.load(model_path)
            logger.info("✅ XGBoost model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            logger.warning("⚠️  Starting without model - archive only mode")
            return None
    
    def get_transaction_schema(self):
        """
        Schema cho dataset 23 cột từ fraudTrain.csv
        """
        return StructType([
            # Identifiers
            StructField("transaction_id", StringType(), False),
            
            # Transaction details
            StructField("transaction_time", TimestampType(), False),
            StructField("amount", DoubleType(), False),
            StructField("unix_time", LongType(), False),
            StructField("hour_of_day", IntegerType(), False),
            
            # Card & Customer
            StructField("cc_num", StringType(), False),
            StructField("first", StringType(), True),
            StructField("last", StringType(), True),
            StructField("gender", StringType(), True),
            StructField("dob", StringType(), True),
            StructField("job", StringType(), True),
            
            # Customer Location
            StructField("street", StringType(), True),
            StructField("city", StringType(), True),
            StructField("state", StringType(), True),
            StructField("zip", StringType(), True),
            StructField("lat", DoubleType(), True),
            StructField("long", DoubleType(), True),
            StructField("city_pop", IntegerType(), True),
            
            # Merchant
            StructField("merchant", StringType(), False),
            StructField("category", StringType(), False),
            StructField("merch_lat", DoubleType(), True),
            StructField("merch_long", DoubleType(), True),
            
            # Target
            StructField("is_fraud", IntegerType(), True)
        ])
    
    def read_from_kafka(self):
        """Đọc streaming data từ Kafka"""
        logger.info(f"Connecting to Kafka: {self.config.KAFKA_BOOTSTRAP_SERVERS}")
        
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.config.KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", self.config.KAFKA_TOPIC) \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .option("maxOffsetsPerTrigger", "1000") \
            .load()
        
        logger.info(f"✅ Subscribed to topic: {self.config.KAFKA_TOPIC}")
        
        return df
    
    def parse_messages(self, df):
        """Parse JSON messages từ Kafka"""
        schema = self.get_transaction_schema()
        
        transactions = df.select(
            from_json(col("value").cast("string"), schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("data.*", "kafka_timestamp")
        
        return transactions
    
    def start_archive_stream(self, df):
        """
        Archive stream - Lưu vào Data Lake (MinIO)
        Dữ liệu này dùng để retrain model
        """
        logger.info("Starting archive stream...")
        
        query = df.writeStream \
            .format("parquet") \
            .option("path", "s3a://hsbc-data/stream-archive/transactions") \
            .option("checkpointLocation", "s3a://hsbc-data/checkpoints/archive") \
            .partitionBy("date") \
            .outputMode("append") \
            .trigger(processingTime="10 seconds") \
            .start()
        
        logger.info("✅ Archive stream started → s3a://hsbc-data/stream-archive/")
        
        return query
    
    def start_inference_stream(self, df):
        """
        Inference stream - Real-time fraud detection
        """
        logger.info("Starting inference stream...")
        
        query = df.writeStream \
            .foreachBatch(self.process_inference_batch) \
            .outputMode("append") \
            .option("checkpointLocation", "s3a://hsbc-data/checkpoints/inference") \
            .trigger(processingTime="2 seconds") \
            .start()
        
        logger.info("✅ Inference stream started")
        
        return query
    
    def process_inference_batch(self, batch_df, batch_id):
        """
        Xử lý từng micro-batch
        - Apply model
        - Filter fraud
        - Write to Cassandra
        """
        if batch_df.isEmpty():
            return
        
        logger.info(f"📦 Batch {batch_id}: {batch_df.count()} transactions")
        
        try:
            # Apply model inference
            predictions = self.model.transform(batch_df)
            
            # Filter fraud alerts (prediction = 1)
            fraud_alerts = predictions.filter(col("prediction") == 1).select(
                col("transaction_id"),
                col("transaction_time"),
                col("amount"),
                col("merchant"),
                col("category"),
                col("cc_num"),
                col("first"),
                col("last"),
                col("gender"),
                col("job"),
                col("state"),
                col("city"),
                col("zip"),
                col("prediction").alias("is_fraud"),
                current_timestamp().alias("detected_at")
            )
            
            fraud_count = fraud_alerts.count()
            
            if fraud_count > 0:
                # Log each fraud transaction details
                fraud_list = fraud_alerts.collect()
                logger.info(f"\n{'='*80}")
                logger.info(f"🚨 BATCH {batch_id}: DETECTED {fraud_count} FRAUD TRANSACTIONS")
                logger.info(f"{'='*80}")
                
                for idx, row in enumerate(fraud_list, 1):
                    logger.info(f"\n🔴 FRAUD #{idx}:")
                    logger.info(f"   Transaction ID: {row['transaction_id']}")
                    logger.info(f"   Time:           {row['transaction_time']}")
                    logger.info(f"   Amount:         ${row['amount']:,.2f}")
                    logger.info(f"   Merchant:       {row['merchant']}")
                    logger.info(f"   Category:       {row['category']}")
                    logger.info(f"   Customer:       {row['first']} {row['last']}")
                    logger.info(f"   Location:       {row['city']}, {row['state']} {row['zip']}")
                    logger.info(f"   Card:           {row['cc_num'][-4:] if row['cc_num'] else 'N/A'}****")
                
                logger.info(f"\n{'='*80}")
                logger.info(f"💾 Writing {fraud_count} fraud alerts to Cassandra...")
                
                # Write to Cassandra
                fraud_alerts.write \
                    .format("org.apache.spark.sql.cassandra") \
                    .mode("append") \
                    .options(table="fraud_alerts", keyspace="hsbc") \
                    .save()
                
                logger.info(f"✅ Successfully saved {fraud_count} fraud alerts to Cassandra")
                logger.info(f"{'='*80}\n")
            else:
                logger.info(f"✓ Batch {batch_id}: No fraud detected in {batch_df.count()} transactions")
        
        except Exception as e:
            logger.error(f"❌ Error processing batch {batch_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run(self):
        """
        Main execution - Chạy streaming pipeline
        """
        logger.info("\n" + "="*60)
        logger.info("UNIFIED STREAMING PIPELINE - PHASE 5")
        logger.info("Dataset: fraudTrain.csv (23 columns)")
        logger.info("="*60 + "\n")
        
        try:
            # 1. Read from Kafka
            df = self.read_from_kafka()
            
            # 2. Parse JSON messages
            transactions = self.parse_messages(df)
            
            # 3. Feature engineering (SHARED logic)
            transactions_with_features = self.feature_engineer.engineer_features(transactions)
            
            # 4. Branch 1: Archive to Data Lake
            archive_query = self.start_archive_stream(transactions_with_features)
            
            # 5. Branch 2: Real-time inference (if model available)
            inference_query = None
            if self.model:
                inference_query = self.start_inference_stream(transactions_with_features)
            else:
                logger.warning("⚠️  Inference disabled - no model")
            
            logger.info("\n" + "="*60)
            logger.info("✅ ALL STREAMS STARTED SUCCESSFULLY")
            logger.info("="*60 + "\n")
            
            # Wait for termination
            logger.info("Press Ctrl+C to stop...")
            
            try:
                archive_query.awaitTermination()
                if inference_query:
                    inference_query.awaitTermination()
            except KeyboardInterrupt:
                logger.info("\n⚠️  Shutting down streams...")
                archive_query.stop()
                if inference_query:
                    inference_query.stop()
        
        except Exception as e:
            logger.error(f"\n❌ Pipeline error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        finally:
            logger.info("Stopping Spark session...")
            self.spark.stop()
            logger.info("✅ Pipeline stopped cleanly\n")

def main():
    pipeline = UnifiedStreamingPipeline()
    pipeline.run()

if __name__ == "__main__":
    main()
