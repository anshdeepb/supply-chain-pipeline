from aws_cdk import Stack, RemovalPolicy
from aws_cdk import aws_s3 as s3

from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam

from constructs import Construct

class SupplyChainPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        bronze = s3.Bucket(self, "Bronze",
                            encryption=s3.BucketEncryption.S3_MANAGED,
                            removal_policy=RemovalPolicy.RETAIN,
                            versioned=True,
                            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
                            )
        
        silver = s3.Bucket(self, "Silver",
                           encryption=s3.BucketEncryption.S3_MANAGED,
                           removal_policy=RemovalPolicy.RETAIN,
                           versioned=True,
                           block_public_access=s3.BlockPublicAccess.BLOCK_ALL
                           )
        
        model = s3.Bucket(self, "Model",
                          encryption=s3.BucketEncryption.S3_MANAGED,
                          removal_policy=RemovalPolicy.RETAIN,
                          versioned=True,
                          block_public_access=s3.BlockPublicAccess.BLOCK_ALL
                          )
        
        scripts = s3.Bucket(self, "Scripts",
                          encryption=s3.BucketEncryption.S3_MANAGED,
                          removal_policy=RemovalPolicy.RETAIN,
                          versioned=True,
                          block_public_access=s3.BlockPublicAccess.BLOCK_ALL
                          )
            