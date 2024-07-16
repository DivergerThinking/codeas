import tiktoken

MODEL_INFO = {
    "gpt-4o-2024-05-13": {"context": 128192, "inprice": 0.005, "outprice": 0.015},
    "gpt-4o": {"context": 128192, "inprice": 0.005, "outprice": 0.015},
    "gpt-4-0125-preview": {"context": 128192, "inprice": 0.01, "outprice": 0.03},
    "gpt-4-1106-preview": {"context": 128192, "inprice": 0.01, "outprice": 0.03},
    "gpt-4": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-0613": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-32k": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-4-32k-0613": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-3.5-turbo-0125": {"context": 16385, "inprice": 0.0005, "outprice": 0.0015},
    "gpt-3.5-turbo-1106": {"context": 16385, "inprice": 0.0010, "outprice": 0.0020},
    "gpt-3.5-turbo-instruct": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-0613": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-16k": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
    "gpt-3.5-turbo-16k-0613": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
}


def calculate_cost(intokens, outtokens, model):
    return round(
        (
            intokens * MODEL_INFO[model]["inprice"]
            + outtokens * MODEL_INFO[model]["outprice"]
        )
        / 1000,
        8,
    )


def count_tokens(text: str, model: str):
    # try:
    encoding = tiktoken.encoding_for_model(model)
    # except KeyError:
    #     # no tokenizer for gpt-4o yet
    #     encoding = tiktoken.get_encoding("gpt-4-turbo")
    return len(encoding.encode(text))


def count_tokens_from_messages(messages: list, model: str):
    """Return the number of tokens used by a list of messages.
    See: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        if len(message) == 2:
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
            if len(message) == 3:
                for key, _, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
