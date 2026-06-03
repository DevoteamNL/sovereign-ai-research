# Customizing AI-Q for Red Hat OpenShift AI

This quickstart deploys AI-Q using pre-built container images on Red Hat OpenShift AI. This guide covers configuration changes, model selection for the 4 deployment options, and when you need to build custom images.

## Table of Contents

- [Quick Configuration Changes](#quick-configuration-changes)
- [The 4 Deployment Options](#the-4-deployment-options)
- [Model Selection](#model-selection)
- [Knowledge Layer Configuration](#knowledge-layer-configuration)
- [Agent Behavior Tuning](#agent-behavior-tuning)
- [Building Custom Images](#building-custom-images)
  - [UI Branding Customization](#ui-branding-customization)
- [Additional Resources](#additional-resources)

---

## Quick Configuration Changes

These changes don't require rebuilding containers—just edit Helm values and redeploy.

### Update API Keys

Configure data source API keys via the `aiq-credentials` secret:

```bash
oc create secret generic aiq-credentials -n ns-aiq \
  --from-literal=NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  --from-literal=TAVILY_API_KEY="$TAVILY_API_KEY" \
  --from-literal=SERPER_API_KEY="$SERPER_API_KEY" \
  --dry-run=client -o yaml | oc apply -f -

# Restart backend to pick up changes
oc rollout restart deployment -n ns-aiq aiq-backend
```

### Edit Agent Parameters

Modify inline ConfigMaps in your values file (e.g., `values-vllm.yaml`):

```yaml
configMaps:
  - name: aiq-vllm-config
    data:
      config_web_vllm.yml: |
        functions:
          shallow_research_agent:
            max_llm_turns: 10        # Increase for deeper shallow research
            max_tool_iterations: 5   # Increase for more tool calls
          
          deep_research_agent:
            max_loops: 2             # Increase for more research iterations
```

Apply changes:

```bash
helm upgrade aiq aiq-rh/ -n ns-aiq -f aiq-rh/values-vllm.yaml
```

---

## The 4 Deployment Options

This quickstart supports four deployment configurations:

| Option | Models | Knowledge | Values File | Use Case |
|--------|--------|-----------|-------------|----------|
| **A** | vLLM (local GPUs) | LlamaIndex | `values-vllm.yaml` | Production, data privacy |
| **B** | NGC (cloud) | LlamaIndex | `values.yaml` (default) | Quick start, no GPU |
| **C** | vLLM (local GPUs) | RAG AI quickstart | `values-vllm-frag.yaml` | Production, advanced RAG |
| **D** | NGC (cloud) | RAG AI quickstart | `values-frag.yaml` | Quick start + advanced RAG |

### Option A & C: vLLM on KServe (Local GPUs)

**Models run on your GPUs using vLLM** via KServe InferenceServices. This gives you:
- Full control over model selection
- Data stays on-premises
- Cost efficiency for high-volume usage

**Model configuration:** `deploy/helm/vllm-models/values.yaml`

### Option B & D: NGC Cloud Inference

**Models run on NVIDIA's hosted API**. This gives you:
- No GPU infrastructure required
- Quick deployment
- Pay-per-use pricing

**Model configuration:** Inline ConfigMaps in values files

### Options C & D: RAG AI quickstart Integration

**RAG AI quickstart (based on NVIDIA RAG Blueprint)** for knowledge retrieval. This provides:
- Advanced multimodal document processing
- GPU-accelerated vector search
- Production-grade scalability

Requires deploying the RAG Blueprint separately (see [AML RAG Quickstart](https://github.com/rh-ai-quickstart/aml-rag-nvidia)).

---

## Model Selection

### vLLM Model Selection (Options A & C)

Edit `deploy/helm/vllm-models/values.yaml` to change models:

```yaml
models:
  # Orchestrator - large reasoning model
  gpt-oss-120b:
    enabled: true
    modelUri: oci://registry.redhat.io/rhelai1/modelcar-gpt-oss-120b:1.5
    servedModelName: RedHatAI/gpt-oss-120b
    resources:
      limits:
        nvidia.com/gpu: "1"     # Adjust for model size
    vllmArgs:
      - --tensor-parallel-size=1
      - --max-model-len=131072
  
  # Researcher - fast, efficient model
  nemotron-nano-30b:
    enabled: true
    modelUri: oci://quay.io/jharmison/models:redhatai--nvidia-nemotron-3-nano-30b-a3b-fp8-modelcar
    servedModelName: RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8
    resources:
      limits:
        nvidia.com/gpu: "1"
    vllmArgs:
      - --max-model-len=131072
      - --enable-auto-tool-choice
      - --tool-call-parser=qwen3_coder
```

**To swap vLLM models:**
1. Change `modelUri` to HuggingFace model ID (e.g., `hf://meta-llama/Llama-3.3-70B-Instruct`) or OCI registry
2. Update `servedModelName` to match
3. Adjust GPU resources for new model's VRAM requirements
4. Redeploy: `helm upgrade vllm-models vllm-models/ -n ns-aiq`

**vLLM Configuration in Backend:**

The backend connects to vLLM models using `_type: openai` (OpenAI-compatible API):

```yaml
llms:
  researcher_llm:
    _type: openai                    # Use 'openai' for vLLM endpoints
    model_name: RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8
    base_url: http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080/v1
    api_key: no-key                  # vLLM doesn't require auth by default
    temperature: 0.1
    max_tokens: 16384
```

**Important - vLLM vs NIM Configuration:**

| Parameter | vLLM (`_type: openai`) | NIM (`_type: nim`) |
|-----------|------------------------|-------------------|
| `_type` | `openai` | `nim` |
| `api_key` | `no-key` or omit | `${NVIDIA_API_KEY}` |
| `chat_template_kwargs` | **DO NOT USE** | `enable_thinking: true` (optional) |

**⚠️ Critical:** `chat_template_kwargs` is NIM-only. If you add it to vLLM configs, the `/think` directives will appear as literal text in responses.

### NGC Model Selection (Options B & D)

Edit inline ConfigMaps in your values file:

```yaml
configMaps:
  - name: aiq-frag-config
    data:
      config_web_frag.yml: |
        llms:
          gpt_oss_llm:
            _type: nim
            model_name: openai/gpt-oss-120b    # Change model here
            base_url: https://integrate.api.nvidia.com/v1
            temperature: 1.0
            max_tokens: 256000
            chat_template_kwargs:
              enable_thinking: true            # NIM only - enables chain-of-thought
```

Browse available NGC models at [build.nvidia.com](https://build.nvidia.com/explore/discover).

### LLM Parameters by Role

Different agents benefit from different temperature/token settings:

| Role | Temperature | Top-p | Max Tokens | Why |
|------|------------|-------|------------|-----|
| Intent classifier | `0.5` | `0.9` | `4096` | Moderate creativity for classification |
| Shallow researcher | `0.1` | `0.3` | `16384` | Low temperature for factual accuracy |
| Deep orchestrator | `1.0` | `1.0` | `128000` | High creativity for complex reasoning |
| Summary model | `0.3` | `0.7` | `100` | Conservative, concise summaries |

---

## Knowledge Layer Configuration

AI-Q supports two knowledge retrieval backends. Your deployment option determines which you use.

### LlamaIndex (Options A & B)

**Embedded in the backend pod** - no external dependencies.

```yaml
functions:
  knowledge_search:
    _type: knowledge_retrieval
    backend: llamaindex
    collection_name: ${COLLECTION_NAME:-default_collection}
    top_k: 5
    chroma_dir: /app/data/chroma              # Persistent storage path
```

**Characteristics:**
- Vector store: ChromaDB (embedded)
- Best for: Quick start, simple deployments
- Limitations: Single-pod scaling, basic document processing

### RAG AI quickstart (Options C & D)

**RAG AI quickstart (based on NVIDIA RAG Blueprint) deployment** - advanced features.

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

**Characteristics:**
- Vector store: Milvus (GPU-accelerated)
- Document processing: NV-Ingest (multimodal extraction)
- Best for: Production, large document sets
- Requires: Separate RAG Blueprint deployment

**Deployment:** See [AML RAG Quickstart](https://github.com/rh-ai-quickstart/aml-rag-nvidia) for RAG Blueprint installation.

**Connecting to RAG Blueprint:**

Set environment variables in your values file:

```yaml
# In values-vllm-frag.yaml or values-frag.yaml
aiq:
  apps:
    backend:
      env:
        RAG_SERVER_URL: http://rag-server.rag.svc.cluster.local:8081/v1
        RAG_INGEST_URL: http://ingestor-server.rag.svc.cluster.local:8082/v1
        COLLECTION_NAME: my_documents
```

---

## Agent Behavior Tuning

### Shallow Research Agent

Controls fast, bounded research with tool calls:

```yaml
functions:
  shallow_research_agent:
    _type: shallow_research_agent
    llm: researcher_llm
    tools:
      - web_search_tool
      - knowledge_search
    max_llm_turns: 10                # Maximum reasoning iterations
    max_tool_iterations: 5           # Maximum tool calls per turn
```

**When to adjust:**
- Increase `max_llm_turns` for more thorough shallow research
- Increase `max_tool_iterations` for more comprehensive tool usage
- Default values balance speed vs depth

### Deep Research Agent

Controls multi-phase comprehensive research:

```yaml
functions:
  deep_research_agent:
    _type: deep_research_agent
    orchestrator_llm: orchestrator_llm    # Large reasoning model
    planner_llm: orchestrator_llm         # Planning model
    researcher_llm: researcher_llm        # Research execution model
    max_loops: 2                          # Research iteration depth
    tools:
      - advanced_web_search_tool
      - knowledge_search
```

**When to adjust:**
- Increase `max_loops` for deeper, more iterative research (slower, more comprehensive)
- Use different LLMs for orchestrator vs researcher to balance cost/performance

### Human-in-the-Loop (HITL)

Control clarification and plan approval:

```yaml
# Disable clarifier entirely (skip plan approval)
workflow:
  _type: chat_deepresearcher_agent
  enable_clarifier: false

# Or keep clarifier but skip approval step
functions:
  clarifier_agent:
    _type: clarifier_agent
    enable_plan_approval: false
```

### Tool Configuration

**Web Search (Tavily):**

```yaml
functions:
  web_search_tool:
    _type: tavily_web_search
    max_results: 5                  # Number of search results
    max_content_length: 1000        # Truncate results for token efficiency
  
  advanced_web_search_tool:
    _type: tavily_web_search
    max_results: 2
    advanced_search: true           # Deeper search, slower
```

**Paper Search (Google Scholar via Serper):**

```yaml
functions:
  paper_search_tool:
    _type: paper_search
    max_results: 5
    serper_api_key: ${SERPER_API_KEY}
```

---

## Building Custom Images

For agent logic changes or adding features, you'll need to build custom container images. However, **UI branding customization can now be done via environment variables** without rebuilding (see [UI Branding Customization](#ui-branding-customization)).

### Container Images & Versioning

This quickstart is based on **NVIDIA AI-Q Blueprint v2.1.0**:

- **Backend:** [NVIDIA AI-Q v2.1.0](https://github.com/NVIDIA-AI-Blueprints/aiq/tree/v2.1.0)
- **Frontend:** [NVIDIA AI-Q v2.1.0](https://github.com/NVIDIA-AI-Blueprints/aiq/tree/v2.1.0)

### Build Process

**1. Clone upstream at v2.1.0:**

```bash
git clone -b v2.1.0 https://github.com/NVIDIA-AI-Blueprints/aiq
cd aiq
```

**2. Make your changes:**

- **UI customization:** Edit `frontends/ui/` (Next.js app)
- **Agent logic:** Edit `src/aiq_agent/` (Python code)
- **Branding:** Colors, logos, fonts

**3. Build images:**

```bash
# Backend
docker build -f deploy/Dockerfile \
  -t your-registry.io/aiq-backend:custom .

# Frontend
docker build -f frontends/ui/Dockerfile \
  -t your-registry.io/aiq-frontend:custom \
  frontends/ui/
```

**4. Push to registry:**

```bash
docker push your-registry.io/aiq-backend:custom
docker push your-registry.io/aiq-frontend:custom
```

**5. Update Helm values:**

```yaml
aiq:
  apps:
    backend:
      image:
        repository: your-registry.io/aiq-backend
        tag: custom
        pullPolicy: Always
    frontend:
      image:
        repository: your-registry.io/aiq-frontend
        tag: custom
        pullPolicy: Always
```

**6. Deploy:**

```bash
helm upgrade --install aiq aiq-rh/ -n ns-aiq -f aiq-rh/values-vllm.yaml
```

### Version Alignment Warning

**⚠️ Critical:** Always build from v2.1.0 to match this quickstart's Helm charts and configurations.

- **Quickstart version:** v2.1.0
- **Upstream tag:** `v2.1.0`
- **Repository:** https://github.com/NVIDIA-AI-Blueprints/aiq/tree/v2.1.0

Using a different version may cause incompatibilities.

### UI Branding Customization

**✨ New in this quickstart:** Customize UI branding at deployment time without rebuilding containers. Changes include logo, colors, fonts, favicon, and documentation links.

#### Quick Start: Use the Branding File

A pre-configured `values-branding.yaml` file is provided. Use it with any deployment option:

```bash
# With any base values file (vllm, frag, vllm-frag, or default)
helm upgrade --install aiq aiq-rh/ -n ns-aiq \
  -f aiq-rh/values-vllm.yaml \
  -f aiq-rh/values-branding.yaml
```

Changes take effect on pod restart (no image rebuild required).

#### How It Works

Branding uses two configuration layers:

**1. Next.js Metadata (3 environment variables)**

Sets browser tab title, description, and favicon path:

```yaml
apps:
  frontend:
    env:
      NEXT_PUBLIC_APP_TITLE: "Red Hat Research"
      NEXT_PUBLIC_APP_DESCRIPTION: "Red Hat AI-powered research assistant"
      NEXT_PUBLIC_FAVICON_PATH: "/branding/favicon.svg"
```

**2. Runtime Branding (ConfigMap with branding.json)**

Loaded at runtime from `/branding/branding.json`. All fields are optional and default to NVIDIA branding:

```yaml
configMaps:
  - name: rh-branding-assets
    data:
      favicon.svg: |
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
          <rect width="64" height="64" rx="12" fill="#EE0000"/>
        </svg>
      
      branding.json: |
        {
          "brandName": "Red Hat Research",
          "brandColor": "#EE0000",
          "logoSvgPath": "M5 5 L35 5 L35 35 L5 35 Z",
          "logoViewBox": "0 0 40 40",
          "docsUrl": "https://www.redhat.com/en/blog/introducing-ai-quickstarts",
          "signinButtonClass": "bg-[#EE0000] hover:bg-[#CC0000]",
          "fontsUrl": "https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;700&display=swap"
        }
```

**branding.json fields:**

| Field | Description | Example |
|-------|-------------|---------|
| `brandName` | Brand name shown in UI | `"Red Hat Research"` |
| `brandColor` | Primary color (hex) | `"#EE0000"` |
| `logoSvgPath` | SVG path `d` attribute | `"M5 5 L35 5..."` |
| `logoViewBox` | SVG viewBox | `"0 0 40 40"` |
| `docsUrl` | Documentation link | `"https://..."` |
| `signinButtonClass` | Tailwind button classes | `"bg-[#EE0000] hover:bg-[#CC0000]"` |
| `fontsUrl` | Google Fonts URL | `"https://fonts.googleapis.com/..."` |

#### Mount the ConfigMap

Mount branding assets into the frontend pod:

```yaml
apps:
  frontend:
    volumeMounts:
      - name: rh-branding
        mountPath: /app/public/branding
        readOnly: true
    
    volumes:
      - name: rh-branding
        configMap:
          name: rh-branding-assets
```

See [values-branding.yaml](deploy/helm/aiq-rh/values-branding.yaml) for a complete working example.

#### Implementation Details

Branding is implemented via patch `0002-Add-runtime-branding-with-CSS-variables-and-metadata.patch`:

- `frontends/ui/src/shared/hooks/useBranding.ts` - Fetches `/branding/branding.json` at runtime
- `frontends/ui/src/app/layout.tsx` - Metadata and fonts
- `frontends/ui/src/adapters/ui/Logo.tsx` - Logo rendering
- `frontends/ui/src/features/layout/components/AppBar.tsx` - Brand name, docs link, button styling

The patch creates a React hook that fetches branding configuration at runtime and falls back to NVIDIA defaults if not found.

See [patches/aiq/README.md](patches/aiq/README.md) for patch workflow details.

---

## Additional Resources

### Deployment Documentation

- **DEPLOYMENT-GUIDE.md** - Detailed deployment instructions for all 4 options
- **Configuration Reference** - Complete YAML parameter reference (see `docs/configuration-reference.md`)

### Upstream Resources

- **NVIDIA NeMo Agent Toolkit:** [Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest/)
- **Upstream AI-Q Blueprint:** [Repository](https://github.com/NVIDIA-AI-Blueprints/aiq)
- **vLLM Documentation:** [vllm.ai](https://vllm.ai/)

### Related Quickstarts

- **RAG AI quickstart:** [Documentation](https://docs.redhat.com/en/learn/ai-quickstarts/rh-aml-rag-nvidia) - RAG AI quickstart based on NVIDIA RAG Blueprint (Options C & D)
- **Red Hat AI Quickstarts:** [Collection](https://www.redhat.com/en/blog/introducing-ai-quickstarts)

### Support

- **This quickstart:** [GitHub Issues](https://github.com/rh-ai-quickstart/rh-research/issues)
- **Upstream AI-Q:** [Issues](https://github.com/NVIDIA-AI-Blueprints/aiq/issues)
- **NeMo Agent Toolkit:** [Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest/)
