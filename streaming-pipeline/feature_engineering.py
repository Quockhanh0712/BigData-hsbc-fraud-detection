#!/usr/bin/env python3
"""
Feature Engineering - FULL 21-feature implementation
Includes numeric, demographic, temporal, geographic and one-hot category encodings
"""

from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Full feature engineering for 21 features requested by user."""

    def __init__(self):
        # Pre-computed category list for one-hot (top categories)
        self.top_categories = [
            'grocery_pos', 'shopping_net', 'misc_net', 'gas_transport',
            'shopping_pos', 'food_dining', 'personal_care', 'health_fitness',
            'entertainment', 'utilities', 'travel', 'electronics', 'others'
        ]

    def engineer_features(self, df):
        """
        Apply 21 features to the incoming DataFrame.
        - Numerical: amount, amount_log
        - Demographic: age, gender_encoded
        - Temporal: hour_of_day, is_weekend
        - Geographic: distance_customer_merchant, is_out_of_state
        - Category one-hots: 13 binary flags
        - Additional crafted features: is_high_value, is_extreme_value, amt_to_pop_ratio
        """
        logger.info("🔧 Applying 21-feature engineering...")

        # Normalize column names if needed
        if 'trans_date_trans_time' in df.columns and 'transaction_time' not in df.columns:
            df = df.withColumn('transaction_time', to_timestamp(col('trans_date_trans_time')))

        if 'amt' in df.columns and 'amount' not in df.columns:
            df = df.withColumnRenamed('amt', 'amount')

        # 1-2: Amount features
        df = df.withColumn('amount_log', log1p(col('amount')))
        df = df.withColumn('is_high_value', when(col('amount') > 100, 1).otherwise(0))
        df = df.withColumn('is_extreme_value', when(col('amount') > 500, 1).otherwise(0))

        # 3-4: Demographic features
        # Age from dob if present (dob as YYYY-MM-DD or timestamp)
        df = df.withColumn('age', when(col('dob').isNotNull(),
                                       floor(months_between(current_date(), to_date(col('dob'))) / 12))
                                       .otherwise(lit(None)))

        # Gender encoding: male=1, female=0, else= -1
        df = df.withColumn('gender_encoded',
                           when(lower(col('gender')) == 'm', 1)
                           .when(lower(col('gender')) == 'male', 1)
                           .when(lower(col('gender')) == 'f', 0)
                           .when(lower(col('gender')) == 'female', 0)
                           .otherwise(-1)
                           )

        # 5-6: Temporal features
        df = df.withColumn('hour_of_day', hour(col('transaction_time')))
        df = df.withColumn('is_weekend', when(dayofweek(col('transaction_time')).isin([1, 7]), 1).otherwise(0))

        # 7-8: Geographic features
        # Distance approximation using simple haversine formula if lat/long present
        def haversine_expr(lat1, lon1, lat2, lon2):
            return (
                2 * 6371 * asin(
                    sqrt(
                        pow(sin(radians(lat2 - lat1) / 2), 2) +
                        cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(radians(lon2 - lon1) / 2), 2)
                    )
                )
            )

        if 'lat' in df.columns and 'long' in df.columns and 'merch_lat' in df.columns and 'merch_long' in df.columns:
            df = df.withColumn('distance_customer_merchant', haversine_expr(col('lat'), col('long'), col('merch_lat'), col('merch_long')))
        else:
            df = df.withColumn('distance_customer_merchant', lit(None))

        # is_out_of_state: Since merchant_state column doesn't exist, set to 0 (feature not available)
        df = df.withColumn('is_out_of_state', lit(0))

        # 9-21: Category one-hot encodings (13 categories)
        for cat in self.top_categories:
            col_name = f"cat_{cat}"
            df = df.withColumn(col_name, when(lower(col('category')) == cat, 1).otherwise(0))

        # Extra crafted features
        # Amount relative to city population (if available)
        df = df.withColumn('amt_to_pop_ratio', when(col('city_pop').isNotNull() & (col('city_pop') > 0), col('amount') / col('city_pop')).otherwise(lit(0.0)))

        # Add date partition column
        df = df.withColumn('date', to_date(col('transaction_time')))

        logger.info("✅ 21 features applied")

        return df

    def get_feature_columns(self):
        numeric = [
            'amount', 'amount_log', 'is_high_value', 'is_extreme_value',
            'age', 'gender_encoded', 'hour_of_day', 'is_weekend',
            'distance_customer_merchant', 'amt_to_pop_ratio'
        ]

        # category one-hot columns
        cat_ones = [f"cat_{c}" for c in self.top_categories]

        categorical = cat_ones + ['category']

        return {
            'numeric': numeric,
            'categorical': categorical,
            'all': numeric + categorical
        }
