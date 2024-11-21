def handler(event, context):
    return {
        "statusCode": 200,
        "event_type": str(type(event)),
        "event": event,
        "context_type": str(type(context)),
        "context": {
            "function_name": context.function_name,
            "memory_limit_in_mb": context.memory_limit_in_mb,
            "aws_request_id": context.aws_request_id
        }
    }
