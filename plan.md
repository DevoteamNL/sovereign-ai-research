# Plan: Migrate LLM Endpoints to vLLM

## Background

The current architecture uses NVIDIA NIM endpoints (`_type: nim`, `base_url: https://integrate.api.nvidia.com/v1`) with NVIDIA-specific models. We want to support externally hosted models via vLLM with flexible model selection.

## Current Architecture

**What's good:**
- `LLMProvider` (`src/aiq_agent/common/llm_provider.py`) provides role-based LLM abstraction — different models per role (orchestrator, researcher, planner, etc.)
- NAT's `Builder.get_llm()` + YAML config is declarative and flexible
- The `_type` discriminator already supports multiple backends: `nim`, `openai`, `dynamo`, `litellm`, `azure_openai`, `aws_bedrock`
- `_type: openai` creates a LangChain `ChatOpenAI` client that works with any OpenAI-compatible endpoint including vLLM

**What's tightly coupled:**
- All 4 config files hardcode `_type: nim` + `base_url: https://integrate.api.nvidia.com/v1`
- Model names are NVIDIA-specific (`nvidia/nemotron-3-nano-30b-a3b`, `openai/gpt-oss-120b`)
- API key validation in `config_validation.py` maps types to specific env vars (`nim` → `NVIDIA_API_KEY`)
- `chat_template_kwargs: enable_thinking: true` is NIM-specific — not all vLLM models support this

## Migration Phases

### Phase 1 — New config file (zero code changes) [DONE]

Create `configs/config_web_vllm.yml` using `_type: openai` pointing to external vLLM:

```yaml
llms:
  intent_llm:
    _type: openai
    model_name: meta-llama/Llama-3.1-8B-Instruct
    base_url: "${VLLM_BASE_URL:-http://localhost:8000}/v1"
    api_key: "${VLLM_API_KEY:-no-key}"
    temperature: 0.5
    max_tokens: 4096

  researcher_llm:
    _type: openai
    model_name: meta-llama/Llama-3.1-70B-Instruct
    base_url: "${VLLM_BASE_URL:-http://localhost:8000}/v1"
    api_key: "${VLLM_API_KEY:-no-key}"
    temperature: 0.1
    max_tokens: 16384

  orchestrator_llm:
    _type: openai
    model_name: Qwen/Qwen2.5-72B-Instruct
    base_url: "${VLLM_BASE_URL:-http://localhost:8000}/v1"
    api_key: "${VLLM_API_KEY:-no-key}"
    temperature: 1.0
    max_tokens: 128000
```

Switch at deploy time: `CONFIG_FILE=configs/config_web_vllm.yml`

### Phase 2 — Update config validation (small code change) [DONE]

File: `src/aiq_agent/common/config_validation.py`

- Add `openai` type with `VLLM_API_KEY` env var mapping
- Make API key validation optional when `base_url` points to a local/private endpoint
- The current `LLM_API_KEY_MAP` maps `_type` → required env vars; extend it for vLLM

### Phase 3 — Remove `enable_thinking` dependency [DONE]

The `chat_template_kwargs: enable_thinking: true` is NIM-specific. vLLM models that support extended thinking use different mechanisms (e.g., `<think>` tokens in prompt, or model-native reasoning).

**Action items:**
- Audit which agents depend on `enable_thinking` and what behavior it triggers
- Investigate how NAT's `ThinkingMixin` works and whether it gracefully degrades
- Make thinking support conditional — detect model capability or config flag
- For vLLM-served reasoning models (e.g., Qwen2.5 with QwQ), use prompt-based thinking instead

### Phase 4 — UI model selector (optional, larger effort)

Add a frontend dropdown to choose model configurations at runtime rather than being locked to a single config at startup. This would require:

- Backend API endpoint to list available models/configs
- Frontend UI component in Settings panel
- Runtime config switching without server restart

### Phase 5 — Clean up Nemotron-specific thinking tokens [DONE]

There are three distinct "thinking" concepts in the codebase:

1. **`chat_template_kwargs: enable_thinking: true`** — NIM API parameter that activates extended chain-of-thought. The model produces `<think>...</think>` blocks. Only consumed by `VerboseTraceCallback` for debug logging — no agent logic depends on it. **Safe to drop for vLLM** (not supported, zero functional impact).

2. **NAT `ThinkingMixin`** — Auto-injects `/think` or `/no_think` system prompt prefix for Nemotron models. Gated by regex `^nvidia/(llama|nvidia).*nemotron` — won't fire for non-Nemotron model names. **Auto-degrades safely for vLLM.**

3. **`think` tool** — LangChain `@tool` scratchpad used by deep research agent. Model-agnostic, works with any LLM. **No changes needed.**

**Problem:** Several prompt templates have `/no_think` **hardcoded** as literal text. Non-Nemotron models will see this as noise, potentially echoing it in output or getting confused.

**Files requiring cleanup:**
- `src/aiq_agent/agents/clarifier/agent.py` (lines 76, 84) — fallback prompts start with `/no_think\n\n`
- `src/aiq_agent/agents/clarifier/prompts/plan_generation.j2` (line 1) — starts with `/no_think`
- `src/aiq_agent/agents/chat_researcher/nodes/intent_classifier.py` (line 89) — fallback prompt starts with `/no_think\n\n`

**Action items:**
- Remove hardcoded `/no_think` tokens from prompt templates; replace with natural language ("Respond concisely without showing your reasoning") or remove entirely (most models default to concise output when prompted for JSON)
- Make thinking opt-in via config flag rather than model name regex, so future reasoning models (DeepSeek-R1, Qwen QwQ) can be supported without matching a Nemotron regex
- Do NOT reimplement `chat_template_kwargs` — vLLM reasoning models handle extended thinking natively

## Key Files

| File | Role |
|------|------|
| `configs/config_web_default_llamaindex.yml` | Current default config (NIM endpoints) |
| `src/aiq_agent/common/llm_provider.py` | Role-based LLM abstraction (LLMProvider, LLMRole) |
| `src/aiq_agent/common/config_validation.py` | API key validation (LLM_API_KEY_MAP) |
| `src/aiq_agent/agents/*/register.py` | Agent registration — uses `builder.get_llm()` |
| `.venv/.../nat/llm/nim_llm.py` | NAT NIM config (NIMModelConfig) |
| `.venv/.../nat/plugins/langchain/llm.py` | NAT client creation — `ChatOpenAI`, `ChatNVIDIA` |

## NAT Supported LLM Types

| `_type` | Client Class | Use Case |
|---------|-------------|----------|
| `nim` | `ChatNVIDIA` | NVIDIA NIM API |
| `openai` | `ChatOpenAI` | OpenAI-compatible (vLLM, TGI, etc.) |
| `dynamo` | `ChatOpenAI` | OpenAI-compatible + Dynamo KV cache headers |
| `litellm` | `ChatLiteLLM` | LiteLLM proxy for multi-provider routing |
| `azure_openai` | `AzureChatOpenAI` | Azure OpenAI |
| `aws_bedrock` | `ChatBedrockConverse` | AWS Bedrock |
| `huggingface` | `ChatHuggingFace` | Local HuggingFace models |
