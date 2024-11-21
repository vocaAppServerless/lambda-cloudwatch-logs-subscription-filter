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
    client = session.client(service_name="secretsmanager", region_name="ap-northeast-2")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response["SecretString"])
    return secret


def handler(event, context):
    print(f"event type => {type(event)}")
    print(f"event => {event}")
    print(f"context type => {type(context)}")
    print(f"context => {context}")

    decoded_data = base64.b64decode(event["awslogs"]["data"])

    # Gzip 압축 해제
    with gzip.GzipFile(fileobj=io.BytesIO(decoded_data)) as f:
        original_data = f.read()

    log_data = json.loads(original_data.decode("utf-8"))

    kst = timezone(timedelta(hours=9))

    # Logstash로 전송할 URL
    logstash_url = get_secret()["LOGSTASH_URL"]
    headers = {"Content-Type": "application/json"}
    print(logstash_url)

    common_fields = {
        "messageType": log_data.get("messageType"),
        "owner": log_data.get("owner"),
        "logGroup": log_data.get("logGroup"),
        "logStream": log_data.get("logStream"),
        "subscriptionFilters": log_data.get("subscriptionFilters"),
    }

    for log_event in log_data["logEvents"]:
        # 개별 로그 이벤트에 공통 필드 추가
        event_data = {**common_fields, **log_event}

        # timestamp 변환
        timestamp = log_event["timestamp"]
        timestamp_in_seconds = timestamp / 1000
        readable_time = datetime.fromtimestamp(timestamp_in_seconds, tz=kst).isoformat()
        event_data["timestamp"] = readable_time
        event_data["@timestamp"] = readable_time  # @timestamp 필드 추가
        # Logstash로 개별 로그 이벤트 전송
        response = requests.post(
            logstash_url, data=json.dumps(event_data), headers=headers
        )
        print(f"Logstash response: {response.status_code}, {response.text}")

    return {"statusCode": 200, "body": "Logs sent to Logstash"}
