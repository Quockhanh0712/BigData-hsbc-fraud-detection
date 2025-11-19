#!/usr/bin/env python3
"""
Uploads fraudTrain.csv and fraudTest.csv to MinIO.
It also converts them to Parquet format for optimized Spark processing.
"""
import os
import sys
import logging
from pathlib import Path
import pandas
import boto3
from botocore.client import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataUploader:
    """Uploads the 23-column fraud detection dataset to MinIO."""
    
    def __init__(self):
        self.endpoint = 'http://localhost:9000'
        self.access_key = 'admin'
        self.secret_key = 'password123'
        self.bucket = 'hsbc-data'
        self.s3_client = boto3.client('s3',
                                      endpoint_url=self.endpoint,
                                      aws_access_key_id=self.access_key,
                                      aws_secret_access_key=self.secret_key,
                                      config=Config(signature_version='s3v4'))

    def process_and_upload(self, file_path: Path):
        """Converts a CSV to Parquet and uploads both formats to MinIO."""
        if not file_path.exists():
            logger.error(f"Dataset file not found: {file_path}. Please download it and place it in data/raw/.")
            return False

        logger.info(f"--- Processing {file_path.name} ---")
        
        # Convert to Parquet
        parquet_path = file_path.with_suffix('.parquet')
        try:
            logger.info(f"Reading {file_path.name}...")
            df = pandas.read_csv(file_path)
            logger.info(f"Converting to {parquet_path.name}...")
            df.to_parquet(parquet_path, index=False)
            logger.info("Conversion successful.")
        except Exception as e:
            logger.error(f"Failed to convert {file_path.name} to Parquet: {e}")
            return False

        # Upload both original CSV and new Parquet file
        self.upload_file(file_path, f"raw/{file_path.name}")
        self.upload_file(parquet_path, f"raw/{parquet_path.name}")
        return True

    def upload_file(self, local_path: Path, s3_key: str):
        """Uploads a single file to MinIO."""
        try:
            logger.info(f"Uploading {local_path.name} to s3://{self.bucket}/{s3_key}")
            self.s3_client.upload_file(str(local_path), self.bucket, s3_key)
            logger.info(f"✅ Upload successful for {local_path.name}.")
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_path.name}: {e}")

    def run(self):
        """Main execution logic."""
        data_dir = Path('A:/hsbc-fraud-detection-new/data/raw')


        
        # Process training data
        train_success = self.process_and_upload(data_dir / 'fraudTrain.csv')
        
        # Process testing data
        test_success = self.process_and_upload(data_dir / 'fraudTest.csv')
        
        if train_success and test_success:
            logger.info("\n✅ All dataset files processed and uploaded successfully!")
        else:
            logger.error("\n❌ One or more dataset files failed to process. Please check logs.")
            sys.exit(1)

def main():
    logger.info("="*60)
    logger.info("PHASE 1: DATA UPLOAD SCRIPT (23-COLUMN DATASET)")
    logger.info("="*60)
    uploader = DataUploader()
    uploader.run()

if __name__ == "__main__":
    main()