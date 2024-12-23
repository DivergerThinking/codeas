TOOL_RETRIEVE_RELEVANT_CONTEXT = {
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
                },
                "n_results": {
                    "type": "number",
                    "description": "The number of results to retrieve",
                    "default": 10,
                },
                "rerank": {
                    "type": "boolean",
                    "description": "Whether to rerank the results",
                    "default": True,
                },
                "context_type": {
                    "type": "string",
                    "description": "The type of context to retrieve",
                    "enum": ["content", "description"],
                    "default": "content",
                },
            },
            "required": ["query"],
        },
    },
}
