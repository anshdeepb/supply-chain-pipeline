import boto3
import os
import pickle
import io
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

s3 = boto3.client('s3')

def encode_features(df):
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    if categorical_cols:
        df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    return df

#SILVER_BUCKET = os.environ['SILVER_BUCKET']
SILVER_BUCKET = "supplychainpipelinestack-silver060ffe09-lxkumwjjqipn"
#MODEL_BUCKET = os.environ['MODEL_BUCKET']

#def lambda_handler(event, context):

obj = s3.get_object(Bucket=SILVER_BUCKET, Key='clean_data.parquet')
df = pd.read_parquet(io.BytesIO(obj['Body'].read()))

print(df.head())

    