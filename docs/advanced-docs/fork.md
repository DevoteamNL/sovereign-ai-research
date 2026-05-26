# Fork Customizations

This document tracks changes made to the [NVIDIA AI-Q Blueprint](https://github.com/NVIDIA-AI-Blueprints/aiq) for Red Hat AI deployment.

## Red Hat AI Enhancements

### Frontend Rebranding

- Red Hat visual identity: logo (fedora SVG), colors (#76b900 to #EE0000 palette), fonts (Red Hat Display/Text via Google Fonts), app name (AI-Q to Red Hat Research), favicon
- Remapped KUI design system green and blue palette tokens to Red Hat red via CSS custom property overrides in globals.css

### vLLM Integration

AI-Q now supports running with locally-hosted vLLM models in addition to NGC cloud models:

- **Four deployment configurations** via Helm values files:
  - `values-vllm.yaml`: vLLM models + embedded LlamaIndex/ChromaDB
  - `values.yaml` (default): NGC cloud models + embedded LlamaIndex/ChromaDB
  - `values-vllm-frag.yaml`: vLLM models + RAG AI quickstart (based on NVIDIA RAG Blueprint)
  - `values-frag.yaml`: NGC cloud models + RAG AI quickstart (based on NVIDIA RAG Blueprint)

- **vLLM configuration files** embedded as ConfigMaps in Helm values:
  - `config_web_vllm.yml` (in `values-vllm.yaml`): Uses `_type: openai` for vLLM endpoints with env var overrides for model names and base URLs
  - `config_web_vllm_frag.yml` (in `values-vllm-frag.yaml`): vLLM + RAG AI quickstart (based on NVIDIA RAG Blueprint) integration
  - `config_web_frag.yml` (in `values-frag.yaml`): NGC + RAG AI quickstart (based on NVIDIA RAG Blueprint) integration
  - All configs support environment variable substitution for flexible endpoint configuration

- **vLLM model deployment chart** (`deploy/helm/vllm-models/`):
  - Deploys models via KServe InferenceServices on Red Hat OpenShift AI
  - Supports both full GPU and MIG (Multi-Instance GPU) configurations
  - Pre-configured for RedHatAI quantized models: gpt-oss-120b (FP8/INT4), nemotron-nano-30b (FP8), nemotron-mini-4b
  - Includes resource profiles and node selectors for GPU placement

### RAG Integration Enhancements

- **Dual RAG backend support** in knowledge_search function:
  - `backend: llamaindex` - Embedded LlamaIndex with ChromaDB
  - `backend: foundational_rag` - RAG AI quickstart based on NVIDIA RAG Blueprint
  
- **RAG AI quickstart deployment option**:
  - Separate configuration for query (`RAG_SERVER_URL`) and ingestion (`RAG_INGEST_URL`) endpoints
  - Configurable collection names and timeout settings
  - PostgreSQL backend for document summaries when using RAG AI quickstart
  - See [RAG AI quickstart documentation](https://docs.redhat.com/en/learn/ai-quickstarts/rh-aml-rag-nvidia) for deployment

### Database Integration

- **PostgreSQL configuration** for persistent storage:
  - Job store and event store for async job infrastructure (`NAT_JOB_STORE_DB_URL`)
  - LangGraph checkpoints for agent state persistence (`AIQ_CHECKPOINT_DB`)
  - Document summaries database (`AIQ_SUMMARY_DB`)
  - Database initialization via init container with PostgreSQL schema setup
  - Environment variable overrides for database credentials

### Deployment Structure

- **Helm-based deployment** for Red Hat OpenShift AI:
  - Modular chart structure with separate backend, frontend, and PostgreSQL components
  - OpenShift Routes for external access with TLS edge termination
  - ConfigMap-based configuration for easy customization without image rebuilds
  - ImagePullSecrets configuration for NGC registry access
  - Resource limits and autoscaling configurations

### Bug Fixes & Improvements

- WebSocket connection timeout fix: 10-second timeout for stuck CONNECTING state prevents indefinite "Please Wait" hang
- SSE request body fix: `input_message` to `query` to match backend schema

### Documentation

- Deployment guide with all four configuration options
- vLLM migration guide and model recipes
- Configuration reference documentation
- Customization guide for model selection and agent tuning
- User verification guide for testing deployments

## Upstream Base

This fork is based on **NVIDIA AI-Q Blueprint v2.1.0**. For the complete upstream changelog, see the [upstream repository](https://github.com/NVIDIA-AI-Blueprints/aiq/blob/v2.1.0/CHANGELOG.md).
