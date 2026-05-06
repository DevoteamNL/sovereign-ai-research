# AI-Q Configuration Reference for OpenShift AI

Quick reference for YAML configuration parameters used in the 4 deployment options. For quick configuration changes, see [CUSTOMIZATION.md](CUSTOMIZATION.md).

## Table of Contents

- [Configuration Structure](#configuration-structure)
- [Environment Variables](#environment-variables)
- [LLM Configuration](#llm-configuration)
- [Tool Configuration](#tool-configuration)
- [Agent Configuration](#agent-configuration)
- [Workflow Configuration](#workflow-configuration)

---

## Configuration Structure

AI-Q uses a single YAML file with four top-level sections:

```yaml
general:     # Logging, API server (usually don't need to change)
llms:        # Model definitions (NGC or vLLM endpoints)
functions:   # Tools and agents
workflow:    # Top-level orchestrator
```

Configuration is provided via inline ConfigMaps in Helm values files.

---

## Environment Variables

Use shell-style variable substitution in YAML:

```yaml
# Required variable (deployment fails if not set)
api_key: ${NVIDIA_API_KEY}

# Variable with default fallback
checkpoint_db: ${AIQ_CHECKPOINT_DB:-./checkpoints.db}

# In URLs
base_url: ${VLLM_BASE_URL:-http://localhost:8000}/v1
collection_name: ${COLLECTION_NAME:-default_collection}
```

Variables are set in the `aiq-credentials` Kubernetes secret or as environment variables in the deployment.

---

## LLM Configuration

### Basic Structure

Each LLM definition gets a unique key:

```yaml
llms:
  researcher_llm:             # Your chosen name
    _type: openai             # 'openai' for vLLM, 'nim' for NGC
    model_name: RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8
    base_url: http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080/v1
    api_key: no-key
    temperature: 0.1
    max_tokens: 16384
```

### vLLM Configuration (Options A & C)

For vLLM models running on KServe:

```yaml
llms:
  # Intent classifier
  intent_llm:
    _type: openai                    # OpenAI-compatible API
    model_name: ${VLLM_INTENT_MODEL:-RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8}
    base_url: ${VLLM_BASE_URL:-http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080}/v1
    api_key: ${VLLM_API_KEY:-no-key}
    temperature: 0.5
    top_p: 0.9
    max_tokens: 4096
  
  # Researcher
  researcher_llm:
    _type: openai
    model_name: ${VLLM_RESEARCHER_MODEL:-RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8}
    base_url: ${VLLM_BASE_URL:-http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080}/v1
    api_key: ${VLLM_API_KEY:-no-key}
    temperature: 0.1
    top_p: 0.3
    max_tokens: 16384
  
  # Orchestrator
  orchestrator_llm:
    _type: openai
    model_name: ${VLLM_ORCHESTRATOR_MODEL:-RedHatAI/gpt-oss-120b}
    base_url: ${VLLM_ORCHESTRATOR_BASE_URL:-http://gpt-oss-120b-predictor.ns-aiq.svc.cluster.local:8080}/v1
    api_key: ${VLLM_API_KEY:-no-key}
    temperature: 1.0
    top_p: 1.0
    max_tokens: 128000
```

### NGC Configuration (Options B & D)

For NVIDIA cloud-hosted models:

```yaml
llms:
  # Intent classifier
  nemotron_llm_intent:
    _type: nim
    model_name: nvidia/nemotron-3-nano-30b-a3b
    base_url: "https://integrate.api.nvidia.com/v1"
    api_key: ${NVIDIA_API_KEY}
    temperature: 0.5
    top_p: 0.9
    max_tokens: 4096
    num_retries: 5
    chat_template_kwargs:
      enable_thinking: true          # NIM only - chain-of-thought reasoning
  
  # Researcher
  nemotron_nano_llm:
    _type: nim
    model_name: nvidia/nemotron-3-nano-30b-a3b
    base_url: "https://integrate.api.nvidia.com/v1"
    api_key: ${NVIDIA_API_KEY}
    temperature: 0.1
    top_p: 0.3
    max_tokens: 16384
    num_retries: 5
    chat_template_kwargs:
      enable_thinking: true
  
  # Orchestrator
  gpt_oss_llm:
    _type: nim
    model_name: openai/gpt-oss-120b
    base_url: https://integrate.api.nvidia.com/v1
    api_key: ${NVIDIA_API_KEY}
    temperature: 1.0
    top_p: 1.0
    max_tokens: 256000
    max_retries: 10
```

### LLM Parameters

| Parameter | Type | Description | Notes |
|-----------|------|-------------|-------|
| `_type` | `str` | **Required.** Provider type | `nim` for NGC, `openai` for vLLM |
| `model_name` | `str` | **Required.** Model identifier | Matches `servedModelName` in vLLM chart |
| `base_url` | `str` | **Required.** API endpoint URL | Include `/v1` suffix |
| `api_key` | `str` | API key | `no-key` for vLLM, `${NVIDIA_API_KEY}` for NGC |
| `temperature` | `float` | Sampling temperature (0.0-2.0) | Lower = more deterministic |
| `top_p` | `float` | Nucleus sampling (0.0-1.0) | Controls diversity |
| `max_tokens` | `int` | Maximum response length | Default: `300` |
| `num_retries` | `int` | Retry attempts on failure | Default: `5` |
| `chat_template_kwargs` | `object` | **NIM only.** Template parameters | Use `enable_thinking: true` for reasoning |

### Parameter Recommendations by Role

| Role | Temperature | Top-p | Max Tokens | Reasoning |
|------|------------|-------|------------|-----------|
| Intent classifier | `0.5` | `0.9` | `4096` | Moderate creativity for classification |
| Shallow researcher | `0.1` | `0.3` | `16384` | Low temperature for factual accuracy |
| Deep orchestrator | `1.0` | `1.0` | `128000` | High temperature for complex reasoning |
| Summary model | `0.3` | `0.7` | `100` | Conservative, concise output |

### Critical: vLLM vs NIM Differences

| Feature | vLLM (`_type: openai`) | NIM (`_type: nim`) |
|---------|------------------------|-------------------|
| `_type` value | `openai` | `nim` |
| API key | `no-key` or omit | `${NVIDIA_API_KEY}` |
| `chat_template_kwargs` | **DO NOT USE** ⚠️ | `enable_thinking: true` (optional) |

**⚠️ Warning:** `chat_template_kwargs` is NIM-specific. Adding it to vLLM configs will cause `/think` directives to appear as literal text in responses.

---

## Tool Configuration

### Web Search (Tavily)

```yaml
functions:
  web_search_tool:
    _type: tavily_web_search
    max_results: 5                  # Number of search results
    max_content_length: 1000        # Truncate content for token efficiency
    api_key: ${TAVILY_API_KEY}      # Optional, defaults to env var
  
  advanced_web_search_tool:
    _type: tavily_web_search
    max_results: 2
    advanced_search: true           # Deeper search, slower
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | `int` | `3` | Maximum search results |
| `advanced_search` | `bool` | `false` | Enable Tavily advanced mode (deeper, slower) |
| `max_content_length` | `int` | `None` | Truncate result content (reduces tokens) |
| `api_key` | `str` | `${TAVILY_API_KEY}` | Tavily API key |

### Paper Search (Google Scholar)

```yaml
functions:
  paper_search_tool:
    _type: paper_search
    max_results: 5
    serper_api_key: ${SERPER_API_KEY}
    timeout: 30
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | `int` | `10` | Maximum paper results |
| `serper_api_key` | `str` | `${SERPER_API_KEY}` | Serper API key for Google Scholar |
| `timeout` | `int` | `30` | Request timeout (seconds) |

### Knowledge Retrieval

Two backends supported: LlamaIndex (embedded) or RAG Blueprint (external).

**LlamaIndex Backend (Options A & B):**

```yaml
functions:
  knowledge_search:
    _type: knowledge_retrieval
    backend: llamaindex
    collection_name: ${COLLECTION_NAME:-default_collection}
    top_k: 5
    chroma_dir: /app/data/chroma
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | **Required** | Use `llamaindex` for embedded ChromaDB |
| `collection_name` | `str` | **Required** | Collection to search |
| `top_k` | `int` | `5` | Number of results to return |
| `chroma_dir` | `str` | `/tmp/chroma_data` | ChromaDB persistence directory |

**RAG Blueprint Backend (Options C & D):**

```yaml
functions:
  knowledge_search:
    _type: knowledge_retrieval
    backend: foundational_rag
    collection_name: ${COLLECTION_NAME:-default_collection}
    top_k: 5
    rag_url: ${RAG_SERVER_URL:-http://rag-server.rag.svc.cluster.local:8081/v1}
    ingest_url: ${RAG_INGEST_URL:-http://ingestor-server.rag.svc.cluster.local:8082/v1}
    summary_db: ${AIQ_SUMMARY_DB:-postgresql+asyncpg://postgres:postgres@aiq-postgres:5432/aiq_jobs}
    timeout: 300
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | `str` | **Required** | Use `foundational_rag` for RAG Blueprint |
| `collection_name` | `str` | **Required** | Collection to search |
| `top_k` | `int` | `5` | Number of results |
| `rag_url` | `str` | **Required** | RAG server query endpoint (include `/v1`) |
| `ingest_url` | `str` | **Required** | RAG ingestion endpoint (include `/v1`) |
| `summary_db` | `str` | **Required** | PostgreSQL connection for summaries |
| `timeout` | `int` | `120` | HTTP timeout (seconds) |

---

## Agent Configuration

### Intent Classifier

Routes queries to meta response, shallow research, or deep research:

```yaml
functions:
  intent_classifier:
    _type: intent_classifier
    llm: intent_llm              # Reference to LLM defined in llms section
    tools:
      - web_search_tool
      - knowledge_search
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm` | `str` | LLM reference for classification |
| `tools` | `list` | Available tools (affects routing decisions) |

### Shallow Research Agent

Fast, bounded research with tool calls:

```yaml
functions:
  shallow_research_agent:
    _type: shallow_research_agent
    llm: researcher_llm
    tools:
      - web_search_tool
      - paper_search_tool
      - knowledge_search
    max_llm_turns: 10                # Maximum reasoning iterations
    max_tool_iterations: 5           # Maximum tool calls per turn
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm` | `str` | **Required** | LLM reference for research |
| `tools` | `list` | **Required** | Available tools |
| `max_llm_turns` | `int` | `10` | Maximum reasoning loops |
| `max_tool_iterations` | `int` | `5` | Maximum tool calls per turn |

**When to adjust:**
- Increase `max_llm_turns` for deeper shallow research
- Increase `max_tool_iterations` for more comprehensive tool usage

### Deep Research Agent

Multi-phase comprehensive research with planning and iteration:

```yaml
functions:
  deep_research_agent:
    _type: deep_research_agent
    orchestrator_llm: orchestrator_llm    # Large reasoning model
    researcher_llm: researcher_llm        # Research execution model
    planner_llm: orchestrator_llm         # Planning model
    max_loops: 2                          # Research iteration depth
    tools:
      - advanced_web_search_tool
      - paper_search_tool
      - knowledge_search
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `orchestrator_llm` | `str` | **Required** | LLM for orchestration and final report |
| `researcher_llm` | `str` | **Required** | LLM for research execution |
| `planner_llm` | `str` | **Required** | LLM for planning (often same as orchestrator) |
| `max_loops` | `int` | `2` | Research iteration depth |
| `tools` | `list` | **Required** | Available tools |

**When to adjust:**
- Increase `max_loops` for deeper, more iterative research (slower, more comprehensive)
- Use different LLMs for cost/performance optimization

### Clarifier Agent (Optional)

Human-in-the-loop plan generation and approval:

```yaml
functions:
  clarifier_agent:
    _type: clarifier_agent
    llm: researcher_llm
    planner_llm: researcher_llm
    tools:
      - web_search_tool
      - paper_search_tool
      - knowledge_search
    max_turns: 3
    enable_plan_approval: true
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm` | `str` | **Required** | LLM for clarification |
| `planner_llm` | `str` | **Required** | LLM for plan generation |
| `tools` | `list` | **Required** | Available tools |
| `max_turns` | `int` | `3` | Maximum clarification rounds |
| `enable_plan_approval` | `bool` | `true` | Require user approval before deep research |

---

## Workflow Configuration

Top-level orchestrator configuration:

```yaml
workflow:
  _type: chat_deepresearcher_agent
  enable_escalation: true           # Allow shallow -> deep escalation
  enable_clarifier: true            # Enable HITL plan approval
  use_async_deep_research: true    # Run deep research asynchronously
  checkpoint_db: ${AIQ_CHECKPOINT_DB:-./checkpoints.db}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `_type` | `str` | **Required** | Use `chat_deepresearcher_agent` |
| `enable_escalation` | `bool` | `true` | Allow shallow research to escalate to deep |
| `enable_clarifier` | `bool` | `true` | Enable human-in-the-loop clarification |
| `use_async_deep_research` | `bool` | `true` | Run deep research async (required for web UI) |
| `checkpoint_db` | `str` | `./checkpoints.db` | LangGraph checkpoint database URL |

---

## Complete Example Configurations

### Option A: vLLM + LlamaIndex

Minimal complete configuration:

```yaml
llms:
  researcher_llm:
    _type: openai
    model_name: RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8
    base_url: http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080/v1
    api_key: no-key
    temperature: 0.1
    max_tokens: 16384
  
  orchestrator_llm:
    _type: openai
    model_name: RedHatAI/gpt-oss-120b
    base_url: http://gpt-oss-120b-predictor.ns-aiq.svc.cluster.local:8080/v1
    api_key: no-key
    temperature: 1.0
    max_tokens: 128000

functions:
  web_search_tool:
    _type: tavily_web_search
    max_results: 5
  
  knowledge_search:
    _type: knowledge_retrieval
    backend: llamaindex
    collection_name: ${COLLECTION_NAME:-default_collection}
    top_k: 5
  
  shallow_research_agent:
    _type: shallow_research_agent
    llm: researcher_llm
    tools: [web_search_tool, knowledge_search]
  
  deep_research_agent:
    _type: deep_research_agent
    orchestrator_llm: orchestrator_llm
    researcher_llm: researcher_llm
    planner_llm: orchestrator_llm
    tools: [web_search_tool, knowledge_search]

workflow:
  _type: chat_deepresearcher_agent
  enable_escalation: true
```

### Option D: NGC + RAG Blueprint

Minimal complete configuration:

```yaml
llms:
  nemotron_nano_llm:
    _type: nim
    model_name: nvidia/nemotron-3-nano-30b-a3b
    base_url: "https://integrate.api.nvidia.com/v1"
    temperature: 0.1
    max_tokens: 16384
    chat_template_kwargs:
      enable_thinking: true
  
  gpt_oss_llm:
    _type: nim
    model_name: openai/gpt-oss-120b
    base_url: https://integrate.api.nvidia.com/v1
    temperature: 1.0
    max_tokens: 256000

functions:
  web_search_tool:
    _type: tavily_web_search
    max_results: 5
  
  knowledge_search:
    _type: knowledge_retrieval
    backend: foundational_rag
    collection_name: ${COLLECTION_NAME:-default_collection}
    rag_url: ${RAG_SERVER_URL}
    ingest_url: ${RAG_INGEST_URL}
    summary_db: ${AIQ_SUMMARY_DB}
  
  shallow_research_agent:
    _type: shallow_research_agent
    llm: nemotron_nano_llm
    tools: [web_search_tool, knowledge_search]
  
  deep_research_agent:
    _type: deep_research_agent
    orchestrator_llm: gpt_oss_llm
    researcher_llm: nemotron_nano_llm
    planner_llm: gpt_oss_llm
    tools: [web_search_tool, knowledge_search]

workflow:
  _type: chat_deepresearcher_agent
  enable_escalation: true
```

---

## Additional Resources

- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Quick configuration changes and model selection
- **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Detailed deployment instructions
- **[NVIDIA NeMo Agent Toolkit](https://docs.nvidia.com/nemo/agent-toolkit/latest/)** - Upstream documentation
