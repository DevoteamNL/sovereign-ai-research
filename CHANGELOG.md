# Change Log

Migration (2026-04-20)

- Project home moved to [`rh-ai-quickstart/rh-research`](https://github.com/rh-ai-quickstart/rh-research); see `MIGRATION.md` for history layout, upstream tracking, and attribution
- Red Hat work lives on the `red-hat-v2.1.0` branch of `rh-research` (tagged `v2.1.0-redhat`); the repo's `develop` branch tracks NVIDIA upstream while the 23-commit upstream-merge effort is tracked separately
- Repo URL references (README, installation guide, Sphinx config, getting-started and deep-researcher notebooks) retargeted to the new canonical home including the `red-hat-v2.1.0` branch hint on clone instructions; NVIDIA upstream attribution preserved in `Fork Customizations` and "See also" sections

Release v2.1.0-redhat

- Red Hat frontend rebrand: logo (fedora SVG), colors (#76b900 to #EE0000 palette), fonts (Red Hat Display/Text via Google Fonts), app name (AI-Q to Red Hat Research), favicon
- Remapped KUI design system green and blue palette tokens to Red Hat red via CSS custom property overrides in globals.css
- New `configs/config_web_vllm.yml`: drop-in config using `_type: openai` for vLLM or any OpenAI-compatible endpoint, with env var overrides for model names and base URL
- Config validation (`config_validation.py`): skip API key requirement for local/private endpoints (localhost, 10.x, 192.168.x, 172.x)
- Model-aware thinking prefixes (`get_thinking_prefix()` in `prompt_utils.py`): Nemotron models get `/no_think` or `/think` directives; all other models get clean prompts
- Removed hardcoded `/no_think` from `plan_generation.j2` template and fallback prompts in `intent_classifier.py` and `clarifier/agent.py`; replaced with runtime model detection
- WebSocket connection timeout fix: 10-second timeout for stuck CONNECTING state prevents indefinite "Please Wait" hang
- SSE request body fix: `input_message` to `query` to match backend schema
- vLLM migration guide, frontend rebranding guide, and blog post documenting the approach

Release v2.0.0

Ground-up rewrite of the NVIDIA AI-Q Blueprint, built on the NVIDIA NeMo Agent Toolkit (NAT).

- Two-tier research architecture with automatic routing between shallow (fast, bounded) and deep (multi-phase, report-grade) research via a single-call Intent Classifier
- Deep Researcher rebuilt with a three-role subagent architecture (Orchestrator, Planner, Researcher) using the `deepagents` library, with configurable research loops and per-role LLM assignment
- New Shallow Researcher agent with tool-call budgets, context compaction, and synthesis anchors for citation-backed answers
- Clarifier agent with human-in-the-loop plan generation, approval, and feedback before deep research
- Shallow-to-deep escalation when the shallow researcher detects insufficient results
- Async Jobs REST API (`/v1/jobs/async/`) with SSE streaming, event replay, reconnection support, and cooperative cancellation
- Dask-based distributed execution with configurable workers, heartbeats, and stale job reaping
- PostgreSQL persistence for job store, event store, LangGraph checkpoints, and document summaries
- Pluggable Knowledge Layer with factory/registry pattern — swap between LlamaIndex (local ChromaDB) and Foundational RAG (hosted NVIDIA RAG Blueprint) without code changes
- Multimodal document extraction (VLM-powered image captioning and chart data extraction)
- Document summaries injected into agent prompts for file-aware research
- Deterministic citation verification pipeline with five-level URL matching, report sanitization, and audit trail
- New Next.js frontend with conversational UI, document upload, collection management, and real-time progress streaming
- Optional OAuth/OIDC authentication with configurable providers
- Multi-backend observability: Phoenix, LangSmith, W&B Weave, and OpenTelemetry Collector with privacy redaction
- FreshQA benchmark for shallow researcher factuality evaluation via `nat eval`
- Docker Compose and Helm chart deployments with distroless runtime images, non-root execution, and horizontal scaling
- Native NAT integration — all configuration through YAML with `nat run` / `nat serve` / `nat eval`
- Four pre-built configs: CLI default, Web + LlamaIndex, Web + Foundational RAG, Hybrid Frontier Model
- uv workspace monorepo, Jupyter notebook tutorial series, and debug console at `/debug`
- Pinned to NeMo Agent Toolkit (NAT) v1.4.0; Python 3.11–3.13; Node.js 22+
- AI-Q holds top positions on both DeepResearch Bench and DeepResearch Bench II leaderboards (see `drb1` and `drb2` branches)

Release v1.2.1
- Upgraded llama-3.3-70b-instruct NIM from version 1.13.1 to 1.14.0
- Aligned Helm values and referenced Docker image tags with the new nim-llm version
- Adopted RAG 2.3.2
- Removed manual NIM_MODEL_PROFILE configuration from Helm values and Docker Compose to rely on automatic profile detection, updated documentation accordingly

Release v1.2.0
- Added support for Helm deployments
- Add support and documentation for evaluation
- Simplified the configuration and integration with RAG, removing nginx
- Adopted RAG 2.3.0
- Tested for compatability with RTX Pro 6000

Release v1.1.0
- Tested for compatability with RAG 2.2.0 release and B200
- Adds support for NVIDIA Workbench

Release v1.0.0

Initial release of the NVIDIA AI-Q Research Assistant Blueprint featuring:
- Multi-modal PDF document upload and processing, compatible with the NVIDIA RAG 2.1 blueprint release
- Demo web application
- Deep research report writing including human-in-the-loop feedback
