import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['STORY_TABLE_NAME'])


def handler(event, context):
    try:
        story_id = event['pathParameters']['id']
        response = table.get_item(
            Key={
                'id': story_id
            }
        )
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': 'http://localhost:4200',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET',
                },
                'body': json.dumps(response['Item'])
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': 'http://localhost:4200',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET',
                },
                'body': json.dumps({'message': 'Story not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                # Adjust to match your frontend URL
                'Access-Control-Allow-Origin': 'http://localhost:4200',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,GET',
            },
            'body': json.dumps({'message': str(e)})
        }
