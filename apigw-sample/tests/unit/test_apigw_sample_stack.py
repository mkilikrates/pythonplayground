import aws_cdk as core
import aws_cdk.assertions as assertions

from apigw_sample.apigw_sample_stack import ApigwSampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in apigw_sample/apigw_sample_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ApigwSampleStack(app, "apigw-sample")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
