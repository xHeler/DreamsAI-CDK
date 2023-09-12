import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

TABLE_NAME = os.environ.get('TABLE_NAME')
TOPIC_ARN = os.environ['TOPIC_ARN']
table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    story_id = str(uuid.uuid4())

    table.put_item(
        Item={
            'id': story_id,
            'isVoiceGenerated': False,
            'isTextGenerated': False,
            'isImagesGenerated': False,
            'content': ""
        }
    )

    try:
        sns_response = sns_client.publish(
            TopicArn=TOPIC_ARN,
            Message=story_id
        )

        if "MessageId" not in sns_response:
            raise Exception("Failed to publish message to SNS topic.")

        response = {
            'statusCode': 200,
            'headers': {
                # Adjust to match your frontend URL
                'Access-Control-Allow-Origin': 'http://localhost:4200',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',  # Adjust as needed
            },
            'body': json.dumps({'id': story_id})
        }
    except Exception as e:
        table.update_item(
            Key={'id': story_id},
            UpdateExpression="set content=:c",
            ExpressionAttributeValues={
                ':c': "ERROR"
            },
            ReturnValues="UPDATED_NEW"
        )

        response = {
            'statusCode': 500,
            'headers': {
                # Adjust to match your frontend URL
                'Access-Control-Allow-Origin': 'http://localhost:4200',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST',  # Adjust as needed
            },
            'body': json.dumps({'error': str(e)})
        }

    return response
