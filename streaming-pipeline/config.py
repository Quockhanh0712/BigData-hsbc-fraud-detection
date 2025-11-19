"""
Configuration cho Spark streaming và training
"""
import os

class Config:
    """Centralized configuration"""
    
    # ========== KAFKA ==========
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    KAFKA_TOPIC = os.getenv('KAFKA_TRANSACTION_TOPIC', 'transactions_hsbc')
    
    # ========== CASSANDRA ==========
    CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
    CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))
    CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'hsbc')
    
    # ========== MINIO (S3) ==========
    MINIO_ENDPOINT = 'http://minio:9000'
    MINIO_ACCESS_KEY = 'admin'
    MINIO_SECRET_KEY = 'password123'
    MINIO_BUCKET = 'hsbc-data'
    
    # ========== PATHS ==========
    TRAINING_DATA_PATH = f's3a://{MINIO_BUCKET}/raw/fraudTrain.csv'
    MODEL_PATH = f's3a://{MINIO_BUCKET}/models/fraud_detection_rf'
    ARCHIVE_PATH = f's3a://{MINIO_BUCKET}/stream-archive/transactions'
    
    # ========== SPARK ==========
    def get_spark_configs(self):
        """Return Spark configuration dict"""
        return {
            # S3/MinIO config
            'spark.hadoop.fs.s3a.endpoint': self.MINIO_ENDPOINT,
            'spark.hadoop.fs.s3a.access.key': self.MINIO_ACCESS_KEY,
            'spark.hadoop.fs.s3a.secret.key': self.MINIO_SECRET_KEY,
            'spark.hadoop.fs.s3a.path.style.access': 'true',
            'spark.hadoop.fs.s3a.impl': 'org.apache.hadoop.fs.s3a.S3AFileSystem',
            
            # Cassandra config
            'spark.cassandra.connection.host': self.CASSANDRA_HOST,
            'spark.cassandra.connection.port': str(self.CASSANDRA_PORT),
            
            # Performance
            'spark.sql.shuffle.partitions': '50',
            'spark.default.parallelism': '50',
            'spark.sql.adaptive.enabled': 'true',
        }
