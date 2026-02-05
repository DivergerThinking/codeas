# CLAUDE.md - Instructions for Claude

## Project Description

**Codeas** (CODEbase ASsistant) is an AI-assisted development tool that uses LLMs to improve development processes through full code context analysis. Developed by **Diverger Thinking**.

- **Version**: 0.4.1
- **Language**: Python 3.9-3.11
- **UI Framework**: Streamlit
- **License**: MIT

## Project Structure

```
src/codeas/
├── main.py                 # Entry point (starts Streamlit UI)
├── configs/                # Configuration and prompts
│   ├── agents_configs.py   # Agent configurations
│   ├── llm_params.py       # LLM model parameters
│   └── prompts.py          # Prompt templates
├── core/                   # Main business logic
│   ├── agent.py            # Agent orchestration
│   ├── clients.py          # Multi-model LLM clients
│   ├── llm.py              # LLM client wrapper
│   ├── metadata.py         # Metadata generation
│   ├── repo.py             # Repository indexing
│   ├── retriever.py        # Context retrieval
│   ├── state.py            # Session state management
│   └── usage_tracker.py    # Cost tracking
├── use_cases/              # Use case implementations
│   ├── documentation.py    # Documentation generation
│   ├── deployment.py       # Deployment planning
│   ├── testing.py          # Testing strategies
│   └── refactoring.py      # Refactoring recommendations
└── ui/                     # Streamlit interface
    ├── 🏠_Home.py          # Main page
    ├── pages/              # Feature pages
    └── components/         # Reusable components
```

## Useful Commands

```bash
# Install dependencies
pip install -e .

# Run the application
codeas

# Code formatting
make style

# Run with Streamlit directly
streamlit run src/codeas/ui/🏠_Home.py
```

## Tech Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.9-3.11 |
| UI | Streamlit 1.28+ |
| Validation | Pydantic 2.5+ |
| LLM Providers | OpenAI, Anthropic, Google Gemini |
| Token Counting | tokencost |
| Code Quality | black, isort, ruff |

## Code Conventions

- **Formatting**: Use `make style` (black + isort + ruff)
- **Data validation**: Pydantic BaseModel for all data structures
- **Typing**: Type hints required for public functions
- **Documentation**: Docstrings in Spanish for main functions
- **Imports**: Ordered with isort (black profile)

## Key Architecture

### Core Modules

1. **State** (`core/state.py`): Centralized session state management
2. **Repo** (`core/repo.py`): Repository file indexing and filtering
3. **Metadata** (`core/metadata.py`): File classification and metadata extraction
4. **Retriever** (`core/retriever.py`): Relevant context selection for LLM
5. **Agent** (`core/agent.py`): LLM interaction normalization

### Design Patterns

- **Metadata-Driven**: Pre-computed metadata reduces token costs
- **Supervised Automation**: Preview → Review → Apply flow
- **Multi-Model Support**: Abstraction layer for multiple LLM providers
- **Cost Transparency**: Complete token/cost tracking

### Workflow

1. User selects repository on Home
2. Metadata generation (or cache loading)
3. Apply filters per page
4. Preview phase with cost estimation
5. Generation executes LLM with selected context
6. Review and output selection
7. Application writes artifacts to filesystem
8. Tracking records usage and costs

## Runtime Data

All execution data is stored in `.codeas/`:
- `metadata.json`: Cached metadata
- `filters.json`: Filtering patterns per page
- `outputs/`: Generated artifacts
- `usage.json`: Cost tracking

## Main Use Cases

1. **Documentation**: Generates 8 automatic documentation sections
2. **Deployment**: Infrastructure analysis and Terraform generation
3. **Testing**: Test strategies and test cases
4. **Refactoring**: Improvement identification and diff generation

## Environment Variables

```bash
OPENAI_API_KEY=sk-...        # OpenAI API key
ANTHROPIC_API_KEY=sk-ant-... # Anthropic API key
GOOGLE_API_KEY=...           # Google Gemini API key
```

## Development Considerations

- The project uses emojis in UI file names (e.g.: `🏠_Home.py`)
- Prompts are centralized in `configs/prompts.py` (~28KB)
- Main documentation is in Spanish
- State persistence through JSON files in `.codeas/`
- Do not modify `metadata.json` directly - it regenerates automatically
