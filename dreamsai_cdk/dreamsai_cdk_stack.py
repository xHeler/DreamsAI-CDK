from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_apigateway as apigw,

)
from constructs import Construct


class DreamsaiCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB
        story_table = dynamodb.Table(
            self, 'StoryTable',
            partition_key=dynamodb.Attribute(
                name='id', type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )

        generate_story_lambda = _lambda.Function(
            self, 'GenerateStoryFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='main.handler',
            code=_lambda.Code.from_asset('lambdas/generate_story'),
            environment={
                "TABLE_NAME": story_table.table_name,
            }
        )

        # Grant the necessary permissions
        story_table.grant_write_data(generate_story_lambda)

        # Define API Gateway with a Lambda proxy integration for GenerateStory Lambda
        api = apigw.RestApi(self, "storiesApi",
                            description="API for generating stories.")
        generate_story = api.root.add_resource(
            'api').add_resource('stories').add_resource('generate')
        generate_story.add_method(
            'GET', apigw.LambdaIntegration(generate_story_lambda))
