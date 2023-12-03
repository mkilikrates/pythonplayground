import aws_cdk as core
import aws_cdk.assertions as assertions

from function_sample.function_sample_stack import FunctionSampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in function_sample/function_sample_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = FunctionSampleStack(app, "function-sample")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
