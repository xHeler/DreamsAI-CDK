import aws_cdk as core
import aws_cdk.assertions as assertions

from dreamsai_cdk.dreamsai_cdk_stack import DreamsaiCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in dreamsai_cdk/dreamsai_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DreamsaiCdkStack(app, "dreamsai-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
