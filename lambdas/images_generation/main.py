import os
import boto3
import json
import requests

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['STORY_TABLE_NAME'])
BUCKET_NAME = os.environ.get('BUCKET_NAME')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
API_ENDPOINT = 'https://api.openai.com/v1/images/generations'

s3 = boto3.client('s3')
number_of_chapters = 5

URLS = {}

max_tokens = 2000

headers = {
    'Authorization': f'Bearer {OPENAI_API_KEY}',
    'Content-Type': 'application/json',
}

def replace_urls(story, urls):
    for key in urls:
        story = story.replace(key, urls[key])
    return story

def split_story_into_chapters(story):
    chapters = story.split('Chapter')
    chapters = [chapter.strip() for chapter in chapters if chapter.strip()]
    return chapters


def handler(event, context):
    for record in event['Records']:
        story_id = record['Sns']['Message']

    response = table.get_item(
        Key={
            'id': story_id
        }
    )

    content = response["Item"]["content"]
    chapters = split_story_into_chapters(content)

    # Send image to s3

    for i, chapter in enumerate(chapters):

        chapter = chapter[slice(997)]

        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }

        data = {
            'prompt': chapter,
            'n': 1,
            'size': '512x512'
        }

        response = requests.post(API_ENDPOINT, headers=headers, json=data)

        if response.status_code == 200:
            image_url = response.json()['data'][0]['url']
            image_response = requests.get(image_url)
            image_content = image_response.content
            s3_key = f"{story_id}/images/IMAGE_{i + 1}.jpg"
            s3.put_object(Bucket=BUCKET_NAME, Key=s3_key,
                          Body=image_content, ContentType='image/jpeg')

            s3_image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

            KEY = f"IMAGE_{i + 1}.jpg"
            URLS[KEY] = s3_image_url

    content = replace_urls(content, URLS)

    ## Update dynamodb

    table.update_item(
        Key={'id': story_id},
        UpdateExpression="set isImagesGenerated=:t, content=:c",
        ExpressionAttributeValues={':t': True, ':c': content},
        ReturnValues="UPDATED_NEW"
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
