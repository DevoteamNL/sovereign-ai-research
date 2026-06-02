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

**✨ New in this quickstart:** UI branding can be customized via environment variables without rebuilding containers. This includes:

- Application title, description, and favicon
- Custom fonts (Google Fonts)
- Logo, brand colors, and name
- Documentation links
- Sign-in button styling

All environment variables are optional and default to NVIDIA AI-Q branding.

#### Available Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEXT_PUBLIC_APP_TITLE` | Browser tab title | `"AI-Q"` | `"Red Hat Research"` |
| `NEXT_PUBLIC_APP_DESCRIPTION` | Meta description | `"AI-powered research assistant"` | `"Red Hat AI-powered research assistant"` |
| `NEXT_PUBLIC_FAVICON_PATH` | Favicon path (relative to `public/`) | `"/favicon.ico"` | `"/favicon.svg"` |
| `NEXT_PUBLIC_FONTS_URL` | Google Fonts URL for custom fonts | None | `"https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700&display=swap"` |
| `NEXT_PUBLIC_BRAND_NAME` | Brand name in UI and aria-labels | `"NVIDIA"` or `"AI-Q"` | `"Red Hat"` |
| `NEXT_PUBLIC_BRAND_COLOR` | Primary brand color (hex) | `"#76b900"` | `"#EE0000"` |
| `NEXT_PUBLIC_LOGO_SVG_PATH` | SVG path data for logo | NVIDIA eye mark | Red Hat fedora paths |
| `NEXT_PUBLIC_LOGO_VIEWBOX` | SVG viewBox | `"0 0 71 47"` | `"0 0 512 512"` |
| `NEXT_PUBLIC_DOCS_URL` | Documentation link | `"https://github.com/NVIDIA-AI-Blueprints/aiq"` | `"https://www.redhat.com/en/blog/introducing-ai-quickstarts"` |
| `NEXT_PUBLIC_SIGNIN_BUTTON_CLASS` | Tailwind classes for sign-in button | `"bg-[#76b900] hover:bg-[#5a8f00]"` | `"bg-[#EE0000] hover:bg-[#CC0000]"` |

#### Example: Red Hat Branding Configuration

**Helm values file (`values-vllm.yaml`):**

```yaml
aiq:
  apps:
    frontend:
      env:
        # Application metadata
        NEXT_PUBLIC_APP_TITLE: "Red Hat Research"
        NEXT_PUBLIC_APP_DESCRIPTION: "Red Hat AI-powered research assistant"
        NEXT_PUBLIC_FAVICON_PATH: "/favicon.svg"
        
        # Custom fonts
        NEXT_PUBLIC_FONTS_URL: "https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700&family=Red+Hat+Text:wght@400;500;600;700&display=swap"
        
        # Brand identity
        NEXT_PUBLIC_BRAND_NAME: "Red Hat"
        NEXT_PUBLIC_BRAND_COLOR: "#EE0000"
        
        # Logo (Red Hat fedora - multi-path SVG)
        NEXT_PUBLIC_LOGO_SVG_PATH: "M341.5 261.1c-1.1-3.6-3.2-7-6.2-9.7l-2.6-2.3c-5.8-5-13.3-7.7-21-7.7h-16.4c-1.4 0-2.7.3-3.9.8l-35.7 15.3c-3.1 1.3-5.1 4.3-5.1 7.7v7.9c0 3.3 2 6.3 5.1 7.6l11.5 4.9c3.1 1.3 5.1 4.3 5.1 7.6v18.6c0 4.6-3.7 8.3-8.3 8.3H196c-4.6 0-8.3 3.7-8.3 8.3v16.6c0 4.6 3.7 8.3 8.3 8.3h67.5c29.8 0 54-24.2 54-54v-9.8c0-2.5-1.1-4.9-3.1-6.5l-9.2-7.6c-1.9-1.6-3.1-3.9-3.1-6.5v-.5c0-2.8 1.4-5.3 3.7-6.8l4.5-2.9c2.3-1.5 3.7-4.1 3.7-6.8v-2.2c0-1.3-.2-2.7-.5-3.8zM459.4 187.5c-25.7-3.3-50.9 2.8-71.4 17.3l-14 9.9c-8.5 6-18.5 9.2-28.8 9.2h-39.9c-6.3 0-12.3 1.5-17.8 4.3l-50.9 25.8c-9.2 4.7-15.1 14.1-15.1 24.5v14.1c0 9.4 4.8 18.2 12.7 23.3l23.7 15.2c2.6 1.7 4.2 4.6 4.2 7.7v30.4c0 15 12.2 27.2 27.2 27.2h30.1c44.7 0 81-36.3 81-81v-13.5c0-3.6-1.7-7-4.5-9.2l-14.6-11.3c-2.8-2.2-4.5-5.6-4.5-9.2v-4.2c0-4.1 2.1-7.9 5.6-10.1l14.7-9.4c5.5-3.5 8.8-9.5 8.8-16v-4.3c0-3.2-.6-6.3-1.8-9.2-2.1-5.2-3.5-10.8-3.8-16.5-.3-4.6 3.7-8.5 8.3-7.9 7.8 1.1 15.4 3.6 22.3 7.6 8.2 4.7 17.7 6.2 27 4.2l.6-.1c8-1.7 14.9-6.7 18.9-13.7 4-7 4.7-15.2 2-22.7-3.2-8.8-10.7-15.1-19.9-16.4z"
        NEXT_PUBLIC_LOGO_VIEWBOX: "0 0 512 512"
        
        # Navigation & actions
        NEXT_PUBLIC_DOCS_URL: "https://www.redhat.com/en/blog/introducing-ai-quickstarts"
        NEXT_PUBLIC_SIGNIN_BUTTON_CLASS: "bg-[#EE0000] hover:bg-[#CC0000]"
```

**Deploy with branding:**

```bash
helm upgrade --install aiq aiq-rh/ -n ns-aiq -f aiq-rh/values-vllm.yaml
```

Changes take effect immediately on pod restart (no image rebuild required).

#### Adding Custom Static Assets

For custom favicons or other static assets, build a custom frontend image:

**1. Add files to `upstream/aiq/frontends/ui/public/`:**

```bash
cd upstream/aiq
cp ~/my-favicon.svg frontends/ui/public/favicon.svg
```

**2. Build and push:**

```bash
docker build -f frontends/ui/Dockerfile \
  -t your-registry.io/aiq-frontend:custom \
  frontends/ui/

docker push your-registry.io/aiq-frontend:custom
```

**3. Update Helm values:**

```yaml
aiq:
  apps:
    frontend:
      image:
        repository: your-registry.io/aiq-frontend
        tag: custom
      env:
        NEXT_PUBLIC_FAVICON_PATH: "/favicon.svg"
```

#### Custom Fonts with Tailwind

When using `NEXT_PUBLIC_FONTS_URL`, you may also want to configure Tailwind to use the custom fonts. This **requires a custom frontend build**.

**Edit `frontends/ui/tailwind.config.ts`:**

```typescript
export default {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Red Hat Text', 'sans-serif'],
        display: ['Red Hat Display', 'sans-serif'],
      },
    },
  },
}
```

Then rebuild the frontend image as shown above.

#### Logo Customization Notes

**Multi-path SVGs** (like Red Hat's fedora): Concatenate all `<path>` elements' `d` attribute values. The component automatically splits on 'M' commands.

**Single-path SVGs**: Simply paste the `d` attribute value.

**viewBox**: Match your logo's coordinate system. Use browser dev tools to inspect the original SVG.

#### Implementation Details

UI customization is implemented via patches applied to the upstream AI-Q v2.1.0 source:

- **Patch file:** `patches/aiq/0002-add-env-var-support-for-custom-ui.patch`
- **Modified files:**
  - `frontends/ui/src/app/layout.tsx` - Metadata, fonts, favicon
  - `frontends/ui/src/adapters/ui/Logo.tsx` - Logo rendering
  - `frontends/ui/src/features/layout/components/AppBar.tsx` - Brand name, docs link, sign-in button

Patches are applied during the container build process. See `patches/aiq/README.md` for patch workflow details.

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
