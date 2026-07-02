import boto3
import os
import pickle
import io
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

s3 = boto3.client('s3')

def drop_identifier_columns(df, uniqueness_threshold=0.95):
    id_like_cols = []
    for col in df.select_dtypes(include=['object', 'string']).columns:
        uniqueness_ratio = df[col].nunique() / len(df)
        if uniqueness_ratio > uniqueness_threshold:
            id_like_cols.append(col)
    
    print(f"Dropping likely ID columns: {id_like_cols}")
    return df.drop(columns=id_like_cols)

def encode_features(df):
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    if categorical_cols:
        df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    return df

SILVER_BUCKET = os.environ['SILVER_BUCKET']
MODEL_BUCKET = os.environ['MODEL_BUCKET']

def lambda_handler(event, context):

    obj = s3.get_object(Bucket=SILVER_BUCKET, Key='clean_data.parquet')
    df = pd.read_parquet(io.BytesIO(obj['Body'].read()))

    df = drop_identifier_columns(df)
    df = encode_features(df)

    x = df.drop(columns=["product_wg_ton"])
    y = df['product_wg_ton']

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)

    print(f"RMSE: {rmse}")
    print(f"R²: {r2}")

    coef_df = pd.DataFrame({
        'feature': x.columns,
        'coefficient': model.coef_
    }).sort_values('coefficient', key=abs, ascending=False)
    print(coef_df.head(10))

    feature_columns = x.columns.tolist()

    bundle = {
        'model': model,
        'feature_columns': feature_columns
    }

    pickle.dump(bundle, open('/tmp/bundle.pkl', 'wb'))

    s3.upload_file('/tmp/bundle.pkl', MODEL_BUCKET, 'model/bundle.pkl')
    print("Model uploaded to S3")

    return {
        'statusCode': 200,
        'body': 'Training complete'
    }

