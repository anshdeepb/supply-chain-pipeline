# Supply Chain Warehouse Throughput Prediction Pipeline

A cloud-native, event-driven data pipeline built on AWS that ingests raw FMCG warehouse data, cleans it through a medallion architecture (Bronze → Silver), trains a regression model to predict warehouse product throughput, and exposes predictions via a REST API — all provisioned through Infrastructure as Code (AWS CDK).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup & Deployment](#setup--deployment)
- [Usage](#usage)
- [Design Decisions](#design-decisions)
- [AWS Well-Architected Framework Alignment](#aws-well-architected-framework-alignment)

## Overview

This project predicts the total product weight (in tons) a warehouse is expected to handle, based on its operational and infrastructure attributes — capacity, zone, worker count, distance from hub, government certification, flood risk, and more.

**Use case:** Supply chain planners can use this to estimate throughput for new or existing warehouses, identify under/over-utilized facilities, and inform infrastructure investment decisions.

**Dataset:** [Supply Chain Optimization for a FMCG Company](https://www.kaggle.com/code/mernaassaad/sco-for-a-fmcg-company/input) (Kaggle)

## Architecture

```
Upload CSV
    │
    ▼
S3 Bronze (raw data)
    │  S3 event
    ▼
Trigger Lambda ──────► Glue ETL Job (Python Shell)
                              │  cleans, deduplicates, imputes
                              ▼
                        S3 Silver (clean_data.parquet)
                              │  S3 event
                              ▼
                        Training Lambda (Docker container)
                              │  encodes features, trains Linear Regression
                              ▼
                        S3 Model (bundle.pkl)
                              │
                              ▼
API Gateway ──────► Inference Lambda ──────► Prediction (product_wg_ton)
    ▲
    │
Local client (predict.py)
```

**Two-phase pipeline:**

1. **Data pipeline** — Bronze (raw CSV) → Glue ETL cleans and validates → Silver (Parquet)
2. **ML pipeline** — Silver triggers automatic model training → Model bucket → API Gateway serves live predictions

The two Lambda functions (training and inference) never call each other directly — they communicate only through the Model S3 bucket, keeping the system loosely coupled.

## Tech Stack

| Component | Service | Why |
|---|---|---|
| Raw/clean storage | Amazon S3 (4 buckets: Bronze, Silver, Model, Scripts) | Cheap, durable, inherently multi-AZ; separate buckets enforce single-responsibility storage |
| ETL | AWS Glue (Python Shell job) | Dataset is a single flat CSV — Spark's distributed compute is unnecessary overhead; Python Shell is cheaper and faster to iterate |
| Pipeline trigger | AWS Lambda | S3 can't invoke Glue directly; Lambda bridges the S3 event to the Glue API |
| Model training/inference | AWS Lambda (Docker container image) | Pay-per-invocation avoids idle server costs (vs. EC2/SageMaker); container deployment was required once combined ML dependencies (pandas + scikit-learn) exceeded the 250MB zip/layer limit |
| API exposure | Amazon API Gateway | Standard serverless pattern for exposing Lambda over HTTP |
| IaC | AWS CDK (Python) | Full infrastructure defined in code; more readable and maintainable than raw CloudFormation YAML |
| Monitoring | Amazon CloudWatch | Automatic logging for all Lambda/Glue executions; used for alarms and debugging |

**SageMaker** was originally considered for model hosting but was unavailable due to AWS Academy Learner Lab IAM restrictions (unable to create a SageMaker execution role). Lambda was selected as the production-viable alternative.

## Prerequisites

- Python 3.9+
- Node.js 18+ (required for the CDK CLI)
- [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html): `npm install -g aws-cdk`
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running, for building the training/inference Lambda container images)
- AWS CLI configured with credentials for a non-root IAM user: `aws configure`
- An AWS account (Academy Learner Lab sandbox or personal account) with permissions for S3, Lambda, Glue, IAM, API Gateway, and CloudWatch

## Project Structure

```
supply_chain_pipeline/
├── app.py                          # CDK app entry point
├── supply_chain_pipeline_stack.py  # All infrastructure defined here
├── glue/
│   └── etl_job.py                  # Bronze → Silver cleaning script
├── src/
│   ├── lambda_trigger/
│   │   └── handler.py              # S3 event → starts Glue job
│   ├── lambda_training_container/  # Docker-based training Lambda
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── handler.py
│   └── lambda_inference_container/ # Docker-based inference Lambda
│       ├── Dockerfile
│       ├── requirements.txt
│       └── handler.py
├── scripts/
│   └── predict.py                  # Local client for demo predictions
├── requirements.txt
├── cdk.json
├── runbook.md
└── README.md
```

## Setup & Deployment

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd supply_chain_pipeline
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS credentials

```bash
aws configure
```

Enter your Access Key ID, Secret Access Key, region (`us-east-1` recommended), and output format (`json`). Use a dedicated IAM user — avoid root credentials.

### 3. Bootstrap CDK (one-time per AWS account)

```bash
cdk bootstrap
```

### 4. Ensure Docker Desktop is running

The training and inference Lambdas are deployed as container images (required to fit their ML dependencies within Lambda's limits), so Docker must be active before deploying.

### 5. Deploy the stack

```bash
cdk synth      # sanity check — compiles to CloudFormation, no AWS changes
cdk deploy     # provisions everything: S3, Glue, Lambda, API Gateway, CloudWatch
```

First deploy takes longer than usual due to Docker image builds and pushes to ECR.

### 6. Download the dataset

Download the CSV from the [Kaggle link above](#overview) and note its local path — you'll upload it in the next step.

### 7. Trigger the pipeline

```bash
aws s3 cp /path/to/your/dataset.csv s3://<bronze-bucket-name>/warehouse_data.csv
```

This alone kicks off the entire pipeline automatically: Glue cleans the data, the training Lambda fires on the new Silver object, and a model is trained and saved — no further manual steps required.

### 8. Verify

```bash
aws glue get-job-runs --job-name bronze-to-silver-etl
aws s3 ls s3://<silver-bucket-name>/
aws s3 ls s3://<model-bucket-name>/model/
```

## Usage

Once deployed and the model has trained, get predictions using the included client script:

```bash
python scripts/predict.py
```

You'll be prompted for warehouse attributes (capacity, worker count, distance from hub, etc.) and the script returns a predicted `product_wg_ton` value via the deployed API Gateway endpoint.

Or call the API directly:

```bash
curl -X POST https://<api-gateway-url>/predict \
  -H "Content-Type: application/json" \
  -d '{"WH_capacity_size": 3, "workers_num": 45, "dist_from_hub": 12, ...}'
```

## Design Decisions

- **S3 for Bronze/Silver instead of RDS** — prioritizes read speed and cost for bulk ML workloads; a future Gold-layer RDS table is the natural extension point for concurrent analyst SQL access.
- **CSV → Parquet conversion at Silver** — columnar storage, better compression, and native type preservation compared to CSV; standard practice for medallion Silver/Gold layers.
- **Dynamic, schema-agnostic cleaning** — the Glue ETL script detects binary Yes/No columns and imputes nulls without hardcoding column names, making it resilient to schema changes.
- **Identifier columns dropped via cardinality threshold** (>95% unique values) rather than hardcoded by name — mirrors real-world practice of combining automated heuristics with explicit review.
- **One-hot encoding over label encoding for nominal categories** (e.g. `zone`) — avoids implying a false ordinal relationship between categories with no inherent order.
- **80/20 train-test split** — ensures RMSE/R² reflect performance on unseen data rather than an optimistic training-data score.
- **Linear Regression as the initial model** — chosen for interpretability and fast training time within Lambda's execution constraints.
- **Docker container Lambdas instead of zip + layers** — pandas + scikit-learn + scipy exceeded Lambda's 250MB unzipped layer limit; container images support up to 10GB and eliminated platform-compatibility issues between local development machines and Lambda's Amazon Linux runtime.
- **Loosely coupled training/inference** — the two Lambdas share no direct dependency; they communicate exclusively through the Model S3 bucket.

## AWS Well-Architected Framework Alignment

| Pillar | Implementation |
|---|---|
| **Operational Excellence** | Full IaC via CDK; structured CloudWatch logging in all Lambda/Glue executions; runbook included (see `runbook.md`) |
| **Security** | All S3 buckets encrypted at rest (SSE-S3) with public access blocked; least-privilege IAM roles scoped per-service (e.g. Glue role can read Bronze/write Silver only); no hardcoded credentials |
| **Reliability** | S3 is inherently multi-AZ; Glue job configured with retry and timeout limits; Bronze data retained indefinitely (`RemovalPolicy.RETAIN`) for reprocessing |
| **Performance Efficiency** | Glue job sized to minimal DPU capacity for dataset scale; model bundle loaded outside the Lambda handler to persist across warm invocations |

---
