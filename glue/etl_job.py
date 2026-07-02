import sys
import boto3
import pandas as pd
import io
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['BRONZE_BUCKET', 'SILVER_BUCKET'])
bronze_bucket = args['BRONZE_BUCKET']
silver_bucket = args['SILVER_BUCKET']

def clean_dataframe(df):
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        unique_vals = set(map(str, df[col].dropna().unique()))
        if unique_vals.issubset({'Yes', 'No', 'yes', 'no'}):
            df[col] = df[col].map({'Yes': 1, 'No': 0, 'yes': 1, 'no': 0})
    
    df = df.drop_duplicates()
    if 'product_wg_ton' in df.columns:
        df = df.dropna(subset=['product_wg_ton'])
    
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    
    return df

s3 = boto3.client('s3')

obj = s3.get_object(Bucket=bronze_bucket, Key='FMCG_data.csv')
df = pd.read_csv(io.BytesIO(obj['Body'].read()))

df = clean_dataframe(df)

buffer = io.BytesIO()
df.to_parquet(buffer, index=False)
s3.put_object(Bucket=silver_bucket, Key='clean_data.parquet', Body=buffer.getvalue())

print("ETL job completed successfully")