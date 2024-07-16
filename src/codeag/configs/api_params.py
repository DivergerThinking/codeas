GPT35_BASE_PARAMS = {
    "temperature": 0.3,
    "top_p": 0.7,
    "response_format": {"type": "json_object"},
    "stream": True,
    "timeout": 10,
    "model": "gpt-3.5-turbo-0125",
}

GPT4_BASE_PARAMS = {
    "temperature": 0.3,
    "top_p": 0.7,
    "response_format": {"type": "json_object"},
    "stream": True,
    "timeout": 10,
    "model": "gpt-4o",
}

GPT4_NO_JSON = {
    "temperature": 0.3,
    "top_p": 0.7,
    # "response_format": {"type": "json_object"},
    "stream": True,
    "timeout": 10,
    "model": "gpt-4o",
}
