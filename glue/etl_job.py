import sys
import boto3
import pandas as pd
import io
import awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['BRONZE_BUCKET', 'SILVER_BUCKET'])
bronze_bucket = args['BRONZE_BUCKET']
silver_bucket = args['SILVER_BUCKET']

s3 = boto3.client('s3')

obj = s3.get_object(Bucket=bronze_bucket, Key='warehouse_data.csv')
df = pd.read_csv(io.BytesIO(obj['Body'].read()))

# Cleaning
df['flood_proof'] = df['flood_proof'].map({'Yes': 1, 'No': 0})
df['electric_supply'] = df['electric_supply'].map({'Yes': 1, 'No': 0})
df = df.dropna()

buffer = io.BytesIO()
df.to_parquet(buffer, index=False)
s3.put_object(Bucket=silver_bucket, Key='clean_data.parquet', Body=buffer.getvalue())

print("ETL job completed successfully")