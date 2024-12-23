EXTRACT_FILE_INFO_PROMPT = """
Analyze the given file content and provide a minimal yet comprehensive summary in this exact structure:
TYPE: [file type: code/test/config/script/ci/doc/other]

CORE: [1-sentence description of primary purpose]

MAIN: [Based on TYPE, one of:]
- For code: list key classes/functions (name:purpose)
- For test: list key tests (name:purpose)
- For config: list key configurations/settings
- For CI/CD: list key stages/jobs
- For scripts: list key operations/tasks
- For docs: list key sections/topics

DEPS: [Skip if not applicable]
- Int: [Internal references/imports]
- Ext: [External dependencies/services]
- Env: [Environment requirements]

FLOW: [2-3 key processes/sequences with →]

NOTE: [Critical details/warnings/prerequisites]

Here are some examples:
<example for a code file>
CORE: REST API client for managing cloud storage buckets

MAIN:
- BucketClient: handles bucket CRUD operations
- StorageManager: manages file transfers + caching

DEPS:
- Int: utils/auth, common/config
- Ext: requests, boto3, redis

FLOW: auth→validate→operation→cache→response

NOTE: Requires valid AWS credentials, 5GB cache limit
</example>

<example for a Dockerfile>
TYPE: config

CORE: Multi-stage build for Python ML service

MAIN:
- base: Python3.9 + core deps
- build: compile extensions
- final: minimal runtime image

DEPS:
- Ext: nginx, pytorch, cuda
- Env: GPU support, 4GB min RAM

FLOW: base→build→optimize→deploy

NOTE: Must build on same arch as deploy target
</example>

<example for a GitHub Action>
TYPE: ci

CORE: Automated testing + deployment pipeline

MAIN:
- test: unit + integration tests
- build: create Docker image
- deploy: push to k8s

DEPS:
- Ext: AWS-actions, Docker-build
- Env: AWS credentials, registry access

FLOW: test→build→scan→deploy

NOTE: Requires protected branch rules
</example>

<example for a config file>
TYPE: config

CORE: Production environment variables and feature flags

MAIN:
- API_ENDPOINTS: service discovery
- RATE_LIMITS: throttling configs
- FEATURES: toggle settings

DEPS:
- Int: dev.env, staging.env
- Env: vault access

NOTE: Requires vault KV path setup
</example>


Rules:
1. Use extreme brevity - every word must add value
2. Skip standard/obvious elements
3. Omit details unless crucial
4. Use symbols/arrows over words
5. No complete sentences except in CORE
6. Omit sections if irrelevant to file type

Here is the file content:
<file_content>
{file_content}
</file_content>
""".strip()

RETRIEVE_RELEVANT_CONTEXT_PROMPT = """
You are a context retrieval assistant. Your task is to analyze the user's query and fetch relevant context using the available retrieval tool.

Given the query, determine:
1. How many results might be needed (default: 10)
2. Whether reranking would improve results (default: true)
3. Whether full content or just descriptions are needed (default: content)

Consider these factors:
- Broad queries may need more results
- Specific queries benefit from reranking
- High-level questions often only need descriptions
- Implementation details require full content

Example responses:
User query: "How does the authentication system work?":
    query = "authentication system implementation"
    n_results = 15
    rerank = true
    context_type = "content"

User query: "List all utility modules":
    query = "utility modules"
    n_results = 20
    rerank = false
    context_type = "description"

If the query is not clear, ask the user to clarify instead of running the tool.
""".strip()


RERANK_RESULTS_PROMPT = """
Given the user query and file information summaries below, return ONLY the genuinely relevant file paths in ranked order. Exclude any files that aren't directly useful for the query.

Ranking criteria:
- Direct relevance to query terms/concepts
- Clear connection to query intent
- File importance (core > auxiliary)
- File type appropriateness

IMPORTANT: Omit files if their relevance is questionable. Quality > Quantity.

Query: {query}

File Summaries:
{file_infos}

Return only a JSON array of relevant file paths, like:
["path/most/relevant.py", "path/second.py"]

Note: It's perfectly acceptable to return a small number of files or even an empty array [] if no files are truly relevant.
""".strip()
