import json
import boto3
import requests
import logging

logger = logging.getLogger()



def lambda_handler(event, context):
    # print("event",event)

    query = event["queryStringParameters"]['q']
    print("query", query)

    # Define the client to interact with Lex
    client = boto3.client('lex-runtime')
    response = client.post_text(botName='SearchBot',
                                botAlias='searchAlias',
                                userId='testuser',
                                inputText=query)
    print("response", response)
    
    # Extract labels from users' input
    labels = []
    if 'slots' in response:
        for slot in response['slots']:
            labels.append(response['slots'][slot])

    labels = [x for x in labels if x is not None]
    
    # Constrcut query using 'or' pattern
    query = {
        "query": {
            "bool": {
                "should": []
            }
        }
    }
    for label in labels:
        new_query = {
            "term": {
                "labels": label
            }
        }
        query['query']['bool']['should'].append(new_query)
    
    # Do the search with Opensearch, get the photo links
    host = 'https://search-photos-kqcgjzgvw4w4n4r7kn6cvlhthu.us-east-1.es.amazonaws.com'
    index = 'photos'
    type = '_search'
    url = host + '/' + index + '/' + type
    auth = ('admin', 'Admin..123')
    headers = {"Content-Type": "application/json"}

    es_res_raw = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
    es_res = json.loads(es_res_raw.text)
    
    res_list = es_res['hits']['hits']

    print('\nSearch results:')
    print(es_res)
    res_str = ''
    
    
    # Construct the photo links into a string and return it
    if len(res_list) != 0:
        for item in res_list:
            if item['_source']['objectKey'] not in res_str:
                res_str += item['_source']['objectKey'] + ","
    
        res_str = res_str.rstrip(res_str[-1])
    print(res_str)

    
    return {
        'statusCode': 200,
        'body': json.dumps(res_str),
        'headers':{
            'Access-Control-Allow-Origin': '*'
        }
    }

    # postText input text is q,
    # return dispatch(event)
