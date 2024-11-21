
def handler(event, context):
    event_type = type(event)
    context_type = type(context)
    return {
        "statusCode": 200,
        "event_type": event_type,
        "event": event,
        "context_type": context_type,
        "context": context
    }