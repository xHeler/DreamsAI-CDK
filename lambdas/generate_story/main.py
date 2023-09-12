import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('TABLE_NAME')
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

    return {
        'statusCode': 200,
        'body': json.dumps({'id': story_id})
    }
