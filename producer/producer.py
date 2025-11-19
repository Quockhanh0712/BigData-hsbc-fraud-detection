#!/usr/bin/env python3
"""
Production Producer - 23-column fraudTrain.csv dataset
Dataset: 1,296,675 transactions, fraud rate: 0.58%
"""

import json
import time
import logging
import signal
import sys
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime

from config import ProducerConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealDataProducer:
    """Producer đọc và replay dataset 23 cột thực tế"""
    
    def __init__(self, data_path='/data/raw/df_test_hdfs.csv'):
        self.config = ProducerConfig()
        self.data_path = data_path
        self.producer = None
        self.running = True
        self.df = None
        self.current_index = 0
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False
    
    def load_data(self):
        """Load fraudTrain.csv với schema chính xác"""
        logger.info(f"Loading dataset: {self.data_path}")
        
        try:
            # Đọc CSV với dtype specifications
            dtype_spec = {
                'cc_num': str,        # Tránh int64 overflow
                'zip': str,           # Giữ leading zeros
                'is_fraud': int,
                'city_pop': int
            }
            
            self.df = pd.read_csv(
                self.data_path,
                dtype=dtype_spec,
                parse_dates=['trans_date_trans_time']
            )
            
            logger.info(f"✅ Loaded: {len(self.df):,} transactions")
            logger.info(f"Columns: {len(self.df.columns)} - {list(self.df.columns)}")
            
            # Drop Unnamed: 0 nếu có
            if 'Unnamed: 0' in self.df.columns:
                self.df = self.df.drop('Unnamed: 0', axis=1)
                logger.info("Dropped 'Unnamed: 0' index column")
            
            # Thống kê
            fraud_count = self.df['is_fraud'].sum()
            fraud_rate = self.df['is_fraud'].mean()
            
            logger.info(f"Fraud: {fraud_count:,} ({fraud_rate:.4%})")
            logger.info(f"Normal: {len(self.df) - fraud_count:,} ({1-fraud_rate:.4%})")
            
            # Thêm hour_of_day
            self.df['hour_of_day'] = self.df['trans_date_trans_time'].dt.hour
            
            # Shuffle để replay ngẫu nhiên
            self.df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
            logger.info("Data shuffled and ready")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Load failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def row_to_json(self, row):
        """
        Chuyển pandas row thành JSON transaction
        
        Xử lý đúng type:
        - int64 → int (cc_num, zip, unix_time, city_pop)
        - float64 → float (amt, lat, long, merch_lat, merch_long)
        - object → str (text fields)
        - Timestamp → ISO string
        """
        try:
            transaction = {
                # Identifiers
                "transaction_id": str(row['trans_num']),
                
                # Transaction details
                "transaction_time": row['trans_date_trans_time'].isoformat(),
                "amount": float(row['amt']),
                "unix_time": int(row['unix_time']),
                "hour_of_day": int(row['hour_of_day']),
                
                # Card & Customer
                "cc_num": str(row['cc_num']),
                "first": str(row['first']),
                "last": str(row['last']),
                "gender": str(row['gender']),
                "dob": str(row['dob']),
                "job": str(row['job']),
                
                # Customer Location
                "street": str(row['street']),
                "city": str(row['city']),
                "state": str(row['state']),
                "zip": str(row['zip']).zfill(5),  # Giữ leading zeros
                "lat": float(row['lat']),
                "long": float(row['long']),
                "city_pop": int(row['city_pop']),
                
                # Merchant
                "merchant": str(row['merchant']),
                "category": str(row['category']),
                "merch_lat": float(row['merch_lat']),
                "merch_long": float(row['merch_long']),
                
                # Target (for validation)
                "is_fraud": int(row['is_fraud'])
            }
            
            return transaction
            
        except Exception as e:
            logger.error(f"Row conversion error: {str(e)}")
            logger.error(f"Row: {row.name}")
            return None
    
    def get_next_transaction(self):
        """Lấy transaction tiếp theo từ dataset"""
        if self.current_index >= len(self.df):
            logger.info("Dataset exhausted, looping back...")
            self.current_index = 0
        
        row = self.df.iloc[self.current_index]
        self.current_index += 1
        
        return self.row_to_json(row)
    
    def connect_kafka(self):
        """Kết nối Kafka"""
        logger.info(f"Connecting to Kafka: {self.config.KAFKA_BOOTSTRAP_SERVERS}")
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                acks=self.config.KAFKA_ACKS,
                retries=self.config.KAFKA_RETRIES,
                compression_type=self.config.KAFKA_COMPRESSION_TYPE,
                max_in_flight_requests_per_connection=5,
                linger_ms=10
            )
            logger.info("✅ Kafka connected")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {str(e)}")
            return False
    
    def send_transaction(self, transaction):
        """Gửi transaction lên Kafka"""
        if transaction is None:
            return False
        
        try:
            future = self.producer.send(
                self.config.KAFKA_TOPIC,
                value=transaction,
                key=transaction['transaction_id'].encode('utf-8')
            )
            
            future.get(timeout=10)
            return True
            
        except Exception as e:
            logger.error(f"Send failed: {str(e)}")
            return False
    
    def run(self):
        """Main producer loop"""
        # Load data
        if not self.load_data():
            logger.error("Cannot start - data loading failed")
            sys.exit(1)
        
        # Connect Kafka
        if not self.connect_kafka():
            logger.error("Cannot start - Kafka connection failed")
            sys.exit(1)
        
        logger.info("\n" + "="*60)
        logger.info("PRODUCER STARTED - 23 COLUMN DATASET")
        logger.info("="*60)
        logger.info(f"Dataset: {len(self.df):,} transactions")
        logger.info(f"Topic: {self.config.KAFKA_TOPIC}")
        logger.info(f"Rate: {self.config.TRANSACTION_RATE} tx/sec")
        logger.info("="*60 + "\n")
        
        count = 0
        fraud_count = 0
        error_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                # Get next transaction
                transaction = self.get_next_transaction()
                
                # Send to Kafka
                if self.send_transaction(transaction):
                    count += 1
                    if transaction['is_fraud'] == 1:
                        fraud_count += 1
                else:
                    error_count += 1
                
                # Log progress every 100 transactions
                if count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    fraud_pct = (fraud_count / count * 100) if count > 0 else 0
                    
                    logger.info(
                        f"📊 Sent: {count:,} | "
                        f"Fraud: {fraud_count} ({fraud_pct:.2f}%) | "
                        f"Errors: {error_count} | "
                        f"Rate: {rate:.1f} tx/sec"
                    )
                
                # Rate limiting
                time.sleep(1 / self.config.TRANSACTION_RATE)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupted by user")
        except Exception as e:
            logger.error(f"\n❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.cleanup(count, fraud_count, error_count)
    
    def cleanup(self, total, fraud, errors):
        """Cleanup resources"""
        logger.info("\n" + "="*60)
        logger.info("PRODUCER SUMMARY")
        logger.info("="*60)
        logger.info(f"Total sent: {total:,}")
        logger.info(f"Fraud: {fraud} ({fraud/total*100:.2f}%)")
        logger.info(f"Normal: {total - fraud:,} ({(total-fraud)/total*100:.2f}%)")
        logger.info(f"Errors: {errors}")
        
        if self.producer:
            logger.info("Flushing pending messages...")
            self.producer.flush(timeout=10)
            self.producer.close()
        
        logger.info("✅ Producer stopped cleanly")
        logger.info("="*60 + "\n")

def main():
    producer = RealDataProducer(data_path='/data/raw/df_sampled.csv')
    producer.run()

if __name__ == "__main__":
    main()
