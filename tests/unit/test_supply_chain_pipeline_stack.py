import aws_cdk as core
import aws_cdk.assertions as assertions

from supply_chain_pipeline.supply_chain_pipeline_stack import SupplyChainPipelineStack

# example tests. To run these tests, uncomment this file along with the example
# resource in supply_chain_pipeline/supply_chain_pipeline_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SupplyChainPipelineStack(app, "supply-chain-pipeline")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
