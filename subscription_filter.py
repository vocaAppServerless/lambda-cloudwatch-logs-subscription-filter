import json
import gzip
import base64
import io
import requests
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta

def get_secret():

    secret_name = "logstash/url"
    region_name = "ap-northeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="ap-northeast-2"
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = json.loads(get_secret_value_response['SecretString'])
    return secret

def handler(event, context):
    
    print(f"event type => {type(event)}")
    print(f"event => {event}")
    print(f"context type => {type(context)}")
    print(f"context => {context}")
    
    decoded_data = base64.b64decode(event['awslogs']['data'])
    
    # Gzip 압축 해제
    with gzip.GzipFile(fileobj=io.BytesIO(decoded_data)) as f:
        original_data = f.read()
        
    log_data = json.loads(original_data.decode('utf-8'))
    
    kst = timezone(timedelta(hours=9))
    
    for log_event in log_data['logEvents']:
        timestamp = log_event['timestamp']
        timestamp_in_seconds = timestamp / 1000
        readable_time = datetime.fromtimestamp(timestamp_in_seconds, tz=kst).isoformat()
        log_data['logEvents'][0]['timestamp'] = readable_time
    print(log_data)
    
    # Logstash로 전송할 URL
    # logstash_url = "http://<LOGSTASH_SERVER_IP>:5044" # Logstash의 HTTP 입력 플러그인 주소
    logstash_url = get_secret()["LOGSTASH_URL"]
    print(logstash_url)
    headers = {'Content-Type': 'application/json'}
    response = requests.post(logstash_url, data=json.dumps(log_data), headers=headers)
    
    print(f"Logstash response: {response.status_code}, {response.text}")
    
    return {
        "statusCode": 200,
        "body": "Logs sent to Logstash"
    }
