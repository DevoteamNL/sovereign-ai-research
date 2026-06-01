# AI-Q Deployment Guide for OpenShift AI

This guide covers the three deployment configurations for AI-Q on OpenShift AI.

## Quick Start Decision Tree

```
Do you have vLLM server(s) running?
├─ YES
│   ├─ Do you have the RAG AI quickstart (based on NVIDIA RAG Blueprint) deployed?
│   │  ├─ YES → Use Option D: vLLM + RAG AI quickstart (fully local, recommended for production)
│   │  └─ NO → Use Option A: vLLM + Embedded RAG (fully local)
└─ NO
    ├─ Do you have the RAG AI quickstart (based on NVIDIA RAG Blueprint) deployed?
    │  ├─ YES → Use Option C: NGC + RAG AI quickstart
    │  └─ NO → Use Option B: NGC + Embedded RAG (quick start)
```

---

## Option A: Local vLLM Models (Recommended)

**Best for:** OpenShift AI deployments with GPU infrastructure

**What you need:**
- vLLM server(s) running and accessible from the cluster
- Models loaded: 
  - `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (intent & research)
  - `RedHatAI/gpt-oss-120b` (orchestration)
  - `nvidia/Nemotron-Mini-4B-Instruct` (summarization)
- API keys: `NVIDIA_API_KEY` (for image pulls only), `TAVILY_API_KEY` (optional)

**What you get:**
- LLM inference via your vLLM server(s)
- Embedded LlamaIndex with ChromaDB for document storage
- Full control over model selection and hosting
- Data stays within your cluster

### Deploy

```bash
cd deploy/helm

# Update chart dependencies

# Install with vLLM configuration (pre-configured for vllm-models chart)
helm upgrade --install aiq aiq-rh/ \
  -n ns-aiq --create-namespace \
  -f aiq-rh/values-vllm.yaml

# Verify
kubectl get pods -n ns-aiq
```

### Configuration

The `values-vllm.yaml` file is pre-configured for use with the `vllm-models` chart:

**vLLM Endpoints** (KServe InferenceServices):
- Intent & Researcher: `http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080`
- Orchestrator: `http://gpt-oss-120b-predictor.ns-aiq.svc.cluster.local:8080`
- Summary: `http://nemotron-mini-4b-predictor.ns-aiq.svc.cluster.local:8080`

**Models served**:
- Intent: `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (30B FP8)
- Researcher: `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (30B FP8)
- Orchestrator: `RedHatAI/gpt-oss-120b` (120B, ~80GB VRAM)
- Summary: `nvidia/Nemotron-Mini-4B-Instruct` (4B)

### Using External vLLM Servers

If using your own vLLM server(s) instead of the vllm-models chart:

```bash
helm install aiq aiq-rh/ \
  -n ns-aiq --create-namespace \
  -f aiq-rh/values-vllm.yaml \
  --set aiq.apps.backend.env.VLLM_BASE_URL=http://your-vllm-server:8000 \
  --set aiq.apps.backend.env.VLLM_ORCHESTRATOR_BASE_URL=http://your-orchestrator-server:8000 \
  --set aiq.apps.backend.env.VLLM_SUMMARY_BASE_URL=http://your-summary-server:8000
```

---

## Option B: NGC Cloud Models

**Best for:** Quick start without GPU infrastructure

**What you need:**
- API keys: `NVIDIA_API_KEY`, `TAVILY_API_KEY` (optional)
- Internet connectivity to NGC API

**What you get:**
- LLM inference via NGC API (pay-per-use)
- Embedded LlamaIndex with ChromaDB for document storage
- No additional infrastructure needed

### Deploy

```bash
cd deploy/helm

# Install with default NGC configuration
helm upgrade --install aiq aiq-rh/ \
  -n ns-aiq --create-namespace

# Verify
kubectl get pods -n ns-aiq
```

### Configuration

The default `aiq-rh/values.yaml` configures:
- Config file: `configs/config_web_default_llamaindex.yml` (default)
- Models used:
  - Intent: `nvidia/nemotron-3-nano-30b-a3b`
  - Researcher: `nvidia/nemotron-3-nano-30b-a3b`
  - Orchestrator: `openai/gpt-oss-120b`
- NGC API endpoint: `https://integrate.api.nvidia.com/v1`

---

## Option C: NGC Models with RAG AI quickstart

**Best for:** Cloud LLMs with enterprise RAG infrastructure

**What you need:**
- [RAG AI quickstart (based on NVIDIA RAG Blueprint)](https://docs.redhat.com/en/learn/ai-quickstarts/rh-aml-rag-nvidia) deployed and accessible
- RAG server URLs (query and ingestion endpoints)
- API keys: `NVIDIA_API_KEY`, `TAVILY_API_KEY` (optional)

**What you get:**
- LLM inference via NGC API
- Enterprise RAG with vector database, reranking, multi-collection support
- Shared RAG infrastructure across multiple applications

### Deploy

```bash
cd deploy/helm

# Update chart dependencies

# Install with RAG AI quickstart (based on NVIDIA RAG Blueprint) configuration
helm upgrade --install aiq aiq-rh/ \
  -n ns-aiq --create-namespace \
  -f aiq-rh/values-frag.yaml \
  --set aiq.apps.backend.env.RAG_SERVER_URL=http://rag-server.<rag-namespace>.svc.cluster.local:8081/v1 \
  --set aiq.apps.backend.env.RAG_INGEST_URL=http://ingestor-server.<rag-namespace>.svc.cluster.local:8082/v1

# Verify
kubectl get pods -n ns-aiq
```

### Configuration

The `values-frag.yaml` file configures:
- Config file: `configs/config_web_frag.yml`
- RAG endpoints: Set via `RAG_SERVER_URL` and `RAG_INGEST_URL`
- Models: Same NGC models as Option B

---

## Option D: vLLM Models with RAG AI quickstart

**Best for:** Fully local deployment with enterprise RAG infrastructure

**What you need:**
- vLLM server(s) running and accessible from the cluster
- Models loaded:
  - `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (intent & research)
  - `RedHatAI/gpt-oss-120b` (orchestration)
  - `nvidia/Nemotron-Mini-4B-Instruct` (summarization)
- [RAG AI quickstart (based on NVIDIA RAG Blueprint)](https://docs.redhat.com/en/learn/ai-quickstarts/rh-aml-rag-nvidia) deployed and accessible
- RAG server URLs (query and ingestion endpoints)
- API keys: `TAVILY_API_KEY` (optional), `SERPER_API_KEY` (optional)

**What you get:**
- LLM inference via your vLLM server(s) - full control, data locality
- Enterprise RAG with vector database, reranking, multi-collection support
- Shared RAG infrastructure across multiple applications
- All data and models stay within your cluster

### Deploy

```bash
cd deploy/helm

# Update chart dependencies

# Install with vLLM + RAG AI quickstart configuration (pre-configured for vllm-models chart)
helm upgrade --install aiq aiq-rh/ \
  -n ns-aiq --create-namespace \
  -f aiq-rh/values-vllm-frag.yaml \
  --set aiq.apps.backend.env.RAG_SERVER_URL=http://rag-server.<rag-namespace>.svc.cluster.local:8081/v1 \
  --set aiq.apps.backend.env.RAG_INGEST_URL=http://ingestor-server.<rag-namespace>.svc.cluster.local:8082/v1

# Verify
kubectl get pods -n ns-aiq
```

### Configuration

The `values-vllm-frag.yaml` file is pre-configured for use with the `vllm-models` chart:

**vLLM Endpoints** (KServe InferenceServices):
- Intent & Researcher: `http://nemotron-nano-30b-predictor.ns-aiq.svc.cluster.local:8080`
- Orchestrator: `http://gpt-oss-120b-predictor.ns-aiq.svc.cluster.local:8080`
- Summary: `http://nemotron-mini-4b-predictor.ns-aiq.svc.cluster.local:8080`

**RAG endpoints**: Set via command-line (update `<rag-namespace>` to your RAG AI quickstart namespace)

**Models served**:
- Intent: `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (30B FP8)
- Researcher: `RedHatAI/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8` (30B FP8)
- Orchestrator: `RedHatAI/gpt-oss-120b` (120B, ~80GB VRAM)
- Summary: `nvidia/Nemotron-Mini-4B-Instruct` (4B)

This gives you the best of both worlds: local model control + enterprise RAG capabilities.

---

## Common Post-Deployment Steps

### Access the Application

```bash
# Get the frontend route URL
oc get route aiq-frontend -n ns-aiq -o jsonpath='{.spec.host}'

# Get the backend API route URL
oc get route aiq-backend -n ns-aiq -o jsonpath='{.spec.host}'
```

Open the frontend URL in your browser to access the Red Hat Research UI.

Backend API documentation: `https://<backend-route>/docs`

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n ns-aiq

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# aiq-backend-xxx                 1/1     Running   0          2m
# aiq-frontend-xxx                1/1     Running   0          2m
# aiq-postgres-xxx                1/1     Running   0          2m

# Check backend health
kubectl port-forward -n ns-aiq svc/aiq-backend 8000:8000 &
curl http://localhost:8000/health
```

### Troubleshooting

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n ns-aiq
kubectl logs <pod-name> -n ns-aiq
```

**Backend can't connect to vLLM:**
```bash
# Check if vLLM server is accessible
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://vllm-server:8000/v1/models

# Check backend logs for connection errors
kubectl logs -n ns-aiq -l component=backend --tail=100
```

**Image pull errors:**
```bash
# Verify secrets exist
kubectl get secrets -n ns-aiq

# Check image pull secret configuration
kubectl describe pod <pod-name> -n ns-aiq | grep -A 5 "Events"
```

**Force pull new image version:**
```bash
kubectl delete pod -l component=frontend -n ns-aiq
kubectl delete pod -l component=backend -n ns-aiq
```

---

## Upgrading

To upgrade an existing deployment:

```bash
cd deploy/helm

# Pull latest changes
git pull origin quickstart

# Upgrade (use same values file as original install)
helm upgrade aiq aiq-rh/ -n ns-aiq -f <your-values-file.yaml>

# Force pod restart to pull new images
kubectl rollout restart deployment -n ns-aiq aiq-backend aiq-frontend
```

---

## Uninstalling

```bash
# Uninstall the Helm release
helm uninstall aiq -n ns-aiq

# Remove namespace and all resources
kubectl delete namespace ns-aiq
```

---

## Additional Resources

- [Configuration Files Documentation](../README.md#configuration-files)
- [vLLM Migration Guide](source/customization/vllm-migration.md)
- [vLLM Model Recipes](source/customization/vllm-recipes.md)
- [Helm Deployment Documentation](../deploy/helm/README.md)
- [Upstream NVIDIA AI-Q Blueprint](https://github.com/NVIDIA-AI-Blueprints/aiq)
