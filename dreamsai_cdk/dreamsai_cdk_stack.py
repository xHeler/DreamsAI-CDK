import os
from aws_cdk import (
    RemovalPolicy,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_apigateway as apigw,
    aws_lambda_event_sources as lambda_event_sources

)
from constructs import Construct
from dotenv import load_dotenv


class DreamsaiCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_dotenv()

        # Environments
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

        # Create an SNS topic
        text_generation_topic = sns.Topic(
            self, "TextGenerationTopic"
        )

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
                "TOPIC_ARN": text_generation_topic.topic_arn
            }
        )

        # Grant the necessary permissions
        story_table.grant_write_data(generate_story_lambda)
        text_generation_topic.grant_publish(generate_story_lambda)

        # CORS
        cors_options = apigw.CorsOptions(
            allow_methods=["POST", "GET"],
            allow_origins=["*"],
            allow_headers=["*"],
        )

        # Define API Gateway with a Lambda proxy integration for GenerateStory Lambda
        api = apigw.RestApi(self, "storiesApi",
                            description="API for generating stories.",
                            default_cors_preflight_options=cors_options)
        generate_story = api.root.add_resource(
            'api').add_resource('stories')
        generate_story.add_method(
            'POST', apigw.LambdaIntegration(generate_story_lambda))

        ################################

        status_lambda = _lambda.Function(
            self, 'StatusLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='main.handler',
            code=_lambda.Code.from_asset('lambdas/status'),
            environment={
                'STORY_TABLE_NAME': story_table.table_name
            }
        )

        # Define API Gateway for Status Stories lambda
        status_resource = api.root.add_resource(
            "stories").add_resource("{id}")
        status_integration = apigw.LambdaIntegration(status_lambda)
        status_resource.add_method("GET", status_integration)

        # Grant the necessary permissions
        story_table.grant_read_data(status_lambda)

        # Generate texr | GPT

        text_generation_lambda = _lambda.Function(
            self, 'TextGenerationFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='main.handler',
            code=_lambda.Code.from_asset('lambdas/text_generation/function.zip'),
            environment={
                "TABLE_NAME": story_table.table_name,
                "OPENAI_API_KEY": OPENAI_API_KEY
            },
            timeout=Duration.seconds(60)
        )

        # Add SNS topic as an event source for the text_generation_lambda
        text_generation_lambda.add_event_source(
            lambda_event_sources.SnsEventSource(text_generation_topic)
        )

        # Grant permission to dynamodb
        story_table.grant_write_data(text_generation_lambda)
