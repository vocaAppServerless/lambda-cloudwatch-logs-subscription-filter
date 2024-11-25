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

def determine_status(message: str) -> str:
    """
    로그 메시지에서 상태를 판별하여 반환
    """
    if "CRITICAL" in message:
        return "CRITICAL"
    elif "ERROR" in message:
        return "ERROR"
    elif "WARNING" in message:
        return "WARNING"
    elif "INFO" in message:
        return "INFO"
    elif "DEBUG" in message:
        return "DEBUG"
    else:
        return "NORMAL"

def handler(event, context):
    # print(f"event type => {type(event)}")
    # print(f"event => {event}")
    # print(f"context type => {type(context)}")
    # print(f"context => {context}")
    decoded_data = base64.b64decode(event["awslogs"]["data"])
    # print(event)
    # Gzip 압축 해제
    with gzip.GzipFile(fileobj=io.BytesIO(decoded_data)) as f:
        original_data = f.read()

    log_data = json.loads(original_data.decode("utf-8"))
    print(f"{log_data} \n\n\n\n")
    kst = timezone(timedelta(hours=9))
    
    headers = {"Content-Type": "application/json"}
    logstash_url = get_secret()["LOGSTASH_URL"]
    
    for log_event in log_data["logEvents"]:
        # 개별 로그 이벤트에 공통 필드 추가

        # timestamp 변환
        timestamp = log_event["timestamp"]
        timestamp_in_seconds = timestamp / 1000
        readable_time = datetime.fromtimestamp(timestamp_in_seconds, tz=kst).isoformat()
        log_event["timestamp"] = readable_time
        
        message = log_event["message"]
        status = determine_status(message)
        
        delivery_dict = dict
        delivery_dict = {
            "logGroup": log_data["logGroup"],
            "eventId": log_event["id"],
            "@timestamp": log_event["timestamp"],
            "message": log_event["message"],
            "status": status
        }
        print(delivery_dict)
        # Logstash로 개별 로그 이벤트 전송
        response = requests.post(
            logstash_url, data=json.dumps(delivery_dict), headers=headers
        )
        print(f"Logstash response: {response.status_code}, {response.text}")


    return {"statusCode": 200, "body": "Logs sent to Logstash"}

event = {'awslogs': {'data': 'H4sIAAAAAAAA/62SW08bMRBG/8rWKi9VNmuPL+PxU4MICJUAIulFEFRtYidayO6GXYdLEf+9SppKVC0SSH20P418fL55ZGVo23weRg/LwBzb64163wf94bB30GcdVt9VoWGOSTQCyGrgiliHLer5QVOvlsyxLL9rs0VeTnyexdDGX+kwNiEvmWPAQWVCZCCyi/dHvVF/OLqcSWO98ZMcZ1yhAeIeZpy8V+BNDsA6rF1N2mlTLGNRV/vFIoamZe6CXbV1lc42Z3a5eah/G6q4zh5Z4deg1gBpqbkWCq0xqIQCbVEp1MJIawRHAQQKUXEhOXLLgZRiHRaLMrQxL5fMCZQA3ILhRmHntyLm2HDUOxslZ+FmFdp46F3CFeXG0yTlNg+pwmBTCopSrwSotS2S0+RLaNqirlyyNTCu2FPnL2DFgZMGaYwlAVKjJURpLGgynBtjEUChBo1cGnoJGI14Drz2nwqRghgJ4zQ6xbtoxPk4voZ8HA+P90/Gsayree0nLts27VY4temO4t+WRzsg4YPyX8t3sx7Gm3O6pU9z9YCn+HE71r2+zsuroluF6LQiabPbepr/WwKS0tZKDcJKMKCVAWMlGeJCEAGStYos12tB1rwkgeQfrfWP997a2X+gw1fSnfVPT96+VOO4t2ryuFkrsNRVlJTtOO4Wi0XwybOM+CYYhLJuHpJh8SO4RIBNBrvjOMjvk23wuQ3eJaQ39+vfXz79BJzxvN8cBAAA'}}
context = None
handler(event, context)