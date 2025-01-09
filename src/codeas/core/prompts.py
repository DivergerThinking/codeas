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

Once the relevant context has been retrieved, respond to the user based on the retrieved information.
""".strip()


RERANK_RESULTS_PROMPT = """
Given the user query and file information summaries below, return ONLY the genuinely relevant file paths in ranked order. Exclude any files that aren't directly useful for the query.

Ranking criteria:
- Direct relevance to query terms/concepts
- Clear connection to query intent
- File importance (core > auxiliary)
- File type appropriateness

IMPORTANT: Omit files if their relevance is questionable. Quality > Quantity.

Query: 
<query>
{query}
</query>

File Summaries:
<file_infos>
{file_infos}
</file_infos>

Return only a JSON array of relevant file paths, like:
["path/most/relevant.py", "path/second.py"]

Note: It's perfectly acceptable to return a small number of files or even an empty array [] if no files are truly relevant.
""".strip()


DOCUMENTATION_AGENT_PROMPT = """

""".strip()

SUMMARIZE_FILE_INFOS_PROMPT = """
Given these file information:
<file_infos>
{file_infos}
</file_infos>

Create a condensed summary that preserves information relevant to this task:
<task>
{task}
</task>

Guidelines:
1. Focus on details that could help accomplish the task
2. DO NOT attempt to fulfill the task itself
3. Skip information irrelevant to the task
4. Maintain original technical details/relationships
5. Preserve critical dependencies/requirements

Format the response as a detailed summary following a similar style as the file information.
""".strip()

DEFINE_DOCUMENTATION_STRUCTURE_PROMPT = """
Given this project information:
<project_info>
{project_info}
</project_info>

Define a clear structure for technical documentation that would help developers understand and use this project.

Guidelines:
1. Create logical sections that progress from high-level to detailed understanding
2. Each section should have 2-5 focused sub-sections
3. Sub-sections must include a specific query to retrieve relevant context
4. Queries should be precise and targeted to the sub-section's topic
5. The sections should be comprehensive and cover all relevant aspects of the project
6. The sub-sections should be detailed and cover all relevant aspects of their corresponding section

Return the structure as JSON matching this format:
{{
  "sections": [
    {{
      "title": "section name",
      "sub_sections": [
        {{
          "title": "sub-section name",
          "query": "specific search query to find relevant content",
          "n_results": "number of results to retrieve",
          "context_type": "whether to retrieve full content or just descriptions"
        }}
      ]
    }}
  ]
}}

Example section structure:
{{
  "sections": [
    {{
      "title": "Getting Started",
      "sub_sections": [
        {{
          "title": "Installation Requirements",
          "query": "project dependencies installation requirements setup",
          "n_results": 10,
          "context_type": "description"
        }},
        {{
          "title": "Basic Configuration",
          "query": "initial configuration settings environment variables",
          "n_results": 10,
          "context_type": "description"
        }}
      ]
    }}
  ]
}}

Focus on creating queries that will effectively retrieve the most relevant content for each sub-section.
""".strip()

GENERATE_SUBSECTION_CONTENT_PROMPT = """
You are a senior software engineer with a knack for writing technical documentation.

Given the following retrieved context:
<context>
{context}
</context>

Generate a detailed and comprehensive markdown content for the following section:
<title>
{subsection_title}
</title>
""".strip()
