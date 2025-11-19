import os

class ProducerConfig:
    """Producer configuration"""
    
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    KAFKA_TOPIC = os.getenv('KAFKA_TRANSACTION_TOPIC', 'transactions_hsbc')
    
    # Rate control
    TRANSACTION_RATE = int(os.getenv('TRANSACTION_RATE', 15))  # transactions/second (default increased)
    FRAUD_RATE = float(os.getenv('FRAUD_RATE', 0.05))  # 5% fraud
    
    # Kafka producer settings
    KAFKA_ACKS = 'all'
    KAFKA_RETRIES = 3
    KAFKA_COMPRESSION_TYPE = 'snappy'
