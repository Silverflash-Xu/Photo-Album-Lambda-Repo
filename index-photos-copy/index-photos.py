import json
import urllib.parse
import boto3
import datetime
import re
import requests
from requests_aws4auth import AWS4Auth

# OpenSearch configuration
region = 'us-east-1'
service = 'es'
auth = ('admin', 'Admin..123')
host = 'https://search-photos-kqcgjzgvw4w4n4r7kn6cvlhthu.us-east-1.es.amazonaws.com' # the OpenSearch Service domain endpoint, including https://
index = 'photos'
type = '_doc'
url = host + '/' + index + '/' + type

headers = { "Content-Type": "application/json" }


s3 = boto3.client('s3')

def detect_labels(photo, bucket):

    client=boto3.client('rekognition')

    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)

    img_label = []
    for label in response['Labels']:
        # print ("Label: " + label['Name'])
        img_label.append(label['Name'].lower())

    return img_label



def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    photo = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print("bucket: " + bucket)
    print("photo: " + photo)

    # label_count=detect_labels(photo, bucket)
    response = s3.head_object(Bucket=bucket,Key=photo)
    print(response)
    if 'x-amz-meta-customlabels' in response['ResponseMetadata']['HTTPHeaders']:
        user_label = response['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'].split(',')
    else:
        user_label = []
    # print("user label: " + ' '.join(user_label))
    img_label = detect_labels(photo, bucket)
    # print("img label: " + ' '.join(img_label))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    key_list = photo.split('/')
    key = key_list[len(key_list) - 1]
    for str in user_label:
        if str.lower() not in img_label:
            img_label.append(str.lower())
    obj = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": timestamp,
        "labels": img_label
        }
    res_obj = json.dumps(obj)
    print("json: " + res_obj)
    # print("Labels detected: " + str(label_count))


    res = requests.post(url, auth=auth, json=obj, headers=headers)
    print(res)

    # try:
    #     response = s3.get_object(Bucket=bucket, Key=photo)
    #     print("CONTENT TYPE: " + response['ContentType'])
    #     return response['ContentType']
    # except Exception as e:
    #     print(e)
    #     print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
    #     raise e
