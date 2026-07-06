# Pipeline Failure Runbook

## 1. Detect
- CloudWatch alarm on inference Lambda error metric fires within 5 min
- Check Glue job run history: AWS Console → Glue → Jobs → Run History

## 2. Diagnose
Check CloudWatch Log Groups:
- `/aws/lambda/inference-function` — inference errors
- `/aws-glue/jobs/` — ETL failures

Common causes:
- Malformed CSV in bronze bucket
- Model bucket empty (training Lambda not yet run)
- Schema mismatch between bronze and silver layers
- Lambda timeout on oversized input

## 3. Fix & Re-trigger

| Failure | Action |
|---|---|
| Malformed CSV | Remove/fix file in bronze S3 bucket |
| Glue job failed | Silver layer unchanged — safe to re-trigger |
| Model bucket empty | Manually invoke training Lambda |
| Infrastructure missing | Run `cdk deploy --all` |

```bash
# Re-trigger Glue ETL job
aws glue start-job-run --job-name <glue-job-name>

# Manually invoke training Lambda
aws lambda invoke --function-name <training-lambda-name> \
  --payload '{}' response.json

# Verify silver bucket updated
aws s3 ls s3://<silver-bucket>/
```

## 4. Verify Recovery
- Glue job shows "Succeeded" in console
- Model file timestamp updated in S3 model bucket
- Test POST to API Gateway returns valid prediction
- CloudWatch alarm returns to OK state

## 5. Full Redeploy
```bash
cdk deploy --all
```
- RTO: ~15 minutes
- RPO: 0 (data persists in S3 independently of infrastructure)