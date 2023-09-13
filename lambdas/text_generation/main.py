import os
import boto3
import json
import requests

dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
TABLE_NAME = os.environ.get('TABLE_NAME')
TOPIC_ARN = os.environ['TOPIC_ARN']
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
API_ENDPOINT = 'https://api.openai.com/v1/chat/completions'


number_of_chapters = 5


max_tokens = 2000

headers = {
    'Authorization': f'Bearer {OPENAI_API_KEY}',
    'Content-Type': 'application/json',
}


def handler(event, context):
    content = "ERROR"
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        story_id = message["story_id"]
        json_body = message["body"]

        fable_style = json_body.get('storyStyle')
        number_of_chapters = json_body.get('duration')

        prompt = f'Write a fairy tale in the style of "{fable_style}". The fairy tale should consist of {number_of_chapters} chapters. Each chapter should have a description of 200-250 words. The description should be written in markdown format and include an image at the beginning of each chapter. Use the following format for the image: "![prompt](IMAGE_1.jpg)". The word "prompt" should be replaced with a prompt to autogenerate the image. Keep the filename "IMAGE_1.jpg" unchanged but instead 1 type chapter number. Exclude the authors name from the story. Start the story with the first chapter and continue until the end.'

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{
                'role': 'system',
                'content': 'You are a professional fairy tale writer, your fairy tales are always written in full.'
            }, {
                'role': 'user',
                'content': prompt
            }],
            'max_tokens': max_tokens,
        }

        response = requests.post(API_ENDPOINT, headers=headers, json=data)

        # Insert content string "Test Content" into DynamoDB
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
        else:
            content = "ERROR"

        # Publish to sns
    sns_response = sns_client.publish(
        TopicArn=TOPIC_ARN,
        Message=json.dumps({"story_id": story_id, "body": "test"}),

    )

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
