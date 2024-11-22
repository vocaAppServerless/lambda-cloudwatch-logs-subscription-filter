import boto3
import requests
import random
import time

def get_parameter(parameter_name):
    ssm = boto3.client("ssm", region_name="ap-northeast-2")

    try:
        response = ssm.get_parameter(Name=parameter_name)
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        print(f"Parameter '{parameter_name}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def send_requests(api_endpoint, num_requests):
    paths = {
        "/incorrectList": ["POST"],
        "/incorrectLists": ["GET"],
        "/incorrectWord": ["POST"],
        "/incorrectWords": ["POST"],
        "/list": ["POST"],
        "/lists": ["GET"],
        "/test": ["GET"],
        "/user": ["GET"],
        "/word": ["POST"],
        "/words": ["POST"]
    }
    
    for _ in range(num_requests):
        path = random.choice(list(paths.keys()))
        method = random.choice(paths[path])

        if method == "GET":
            response = requests.get(api_endpoint + path)
        elif method == "POST":
            response = requests.post(api_endpoint + path)

        print(f"Request to {path} ({method}): Status Code {response.status_code}")

        time.sleep(random.uniform(0.5, 2))
    
    
if __name__ == "__main__":
    parameter_name = "/remember-me/api_gateway_endpoint_invoke_url"
    api_gateway_endpoint_invoke_url = get_parameter(parameter_name)
    
    if api_gateway_endpoint_invoke_url:
        send_requests(api_gateway_endpoint_invoke_url, num_requests=50)
    else:
        print("Failed to retrieve the API Gateway endpoint URL.")