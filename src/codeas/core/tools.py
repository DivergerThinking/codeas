import json


def handle_tool_calls(tool_calls: list):
    tool_calls_messages = []
    for tool_call in tool_calls:
        function_name = tool_call["function"]["name"]
        tool_call_arguments = json.loads(tool_call["function"]["arguments"])
        tool_calls_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": call_function(function_name, tool_call_arguments),
            }
        )
    return tool_calls_messages


def call_function(function_name: str, arguments: dict):
    return eval(f"{function_name}(**arguments)")


def get_weather(location: str):
    ...


TOOL_GET_WEATHER = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
        },
    },
}


def retrieve_relevant_context(query: str):
    return "this is a dummy tool call output for testing purposes. just pretend you received the correct output and respond to the user with any random code answer"


TOOL_RETRIEVE_CONTEXT = {
    "type": "function",
    "function": {
        "name": "retrieve_relevant_context",
        "description": "Retrieve relevant context for the query",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to retrieve context for",
                }
            },
            "required": ["query"],
        },
    },
}
