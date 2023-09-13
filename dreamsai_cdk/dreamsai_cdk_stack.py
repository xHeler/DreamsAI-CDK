import os
from aws_cdk import (
    RemovalPolicy,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_apigateway as apigw,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam
)
from constructs import Construct
from dotenv import load_dotenv
from aws_cdk.aws_s3 import Bucket, BlockPublicAccess

from aws_cdk.aws_iam import (
    PolicyStatement,
    Effect,
    ArnPrincipal
)


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

        images_generation_topic = sns.Topic(
            self, "ImagesGenerationTopic"
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
            code=_lambda.Code.from_asset(
                'lambdas/text_generation/function.zip'),
            environment={
                "TABLE_NAME": story_table.table_name,
                "OPENAI_API_KEY": OPENAI_API_KEY,
                "TOPIC_ARN": images_generation_topic.topic_arn
            },
            timeout=Duration.seconds(90)
        )

        images_generation_topic.grant_publish(text_generation_lambda)

        # Add SNS topic as an event source for the text_generation_lambda
        text_generation_lambda.add_event_source(
            lambda_event_sources.SnsEventSource(text_generation_topic)
        )

        # Grant permission to dynamodb
        story_table.grant_write_data(text_generation_lambda)

        # S3 + lambda image lambda generation
        public_bucket = Bucket(
            self,
            "dreamsai-story-files",
            bucket_name="dreamsai-story-files",
        )

        # Create the Lambda function
        images_generation_lambda = _lambda.Function(
            self, 'ImageGenerationLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='main.handler',
            code=_lambda.Code.from_asset(
                'lambdas/images_generation/function.zip'),
            environment={
                "BUCKET_NAME": public_bucket.bucket_name,
                "TABLE_NAME": story_table.table_name,
                "OPENAI_API_KEY": OPENAI_API_KEY,
                'STORY_TABLE_NAME': story_table.table_name,
                "TOPIC_ARN": images_generation_topic.topic_arn
            },
            timeout=Duration.seconds(100)
        )

        public_bucket.grant_put(images_generation_lambda)

        # Grand permission to dynamodb
        story_table.grant_read_data(images_generation_lambda)
        story_table.grant_write_data(images_generation_lambda)

        images_generation_lambda.add_event_source(
            lambda_event_sources.SnsEventSource(images_generation_topic)
        )
