import os
import boto3
import json

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME')
OPENAI_API_KEY = os.environ.get('OPENAI_API')


def handler(event, context):
    for record in event['Records']:
        story_id = record['Sns']['Message']

        # Insert content string "Test Content" into DynamoDB
        content = "Test Content"

        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'id': story_id},
            UpdateExpression="set isTextGenerated=:t, content=:c",
            ExpressionAttributeValues={':t': True, ':c': content},
            ReturnValues="UPDATED_NEW"
        )

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
