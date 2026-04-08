<!--
SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->

# Customization

## Customization vs Extending
**Customization** is for changing what already exists in the blueprint — models, prompts, tool configuration, and agent behavior. No new code or plugins required.

**Extending** is for adding new functionality — new tools, data sources, or integrations that don't exist today. Refer to [Extending](../extending/index.md).


- **[Configuration Reference](./configuration-reference.md)** — Complete YAML schema with all parameters
- **[Swapping Models](./swapping-models.md)** — Use different LLMs (hosted NIM, self-hosted NIM, mixing models)
- **[Tools and Sources](./tools-and-sources.md)** — Enable, disable, and configure search tools
- **[MCP Tools](./mcp-tools.md)** — Add external tools through Model Context Protocol
- **[Knowledge Layer](./knowledge-layer.md)** — Add document retrieval (LlamaIndex or Foundational RAG)
- **[Prompts](./prompts.md)** — Modify agent behavior through Jinja2 prompt templates
- **[Human-in-the-Loop](./hitl.md)** — Configure the clarifier and plan approval workflow
- **[vLLM Migration](./vllm-migration.md)** — Use vLLM or any OpenAI-compatible endpoint instead of NVIDIA NIM
- **[vLLM Model Recipes](./vllm-recipes.md)** — Tested model configurations with Docker commands, env settings, and performance data
- **[vLLM Migration Decisions](./vllm-decisions.md)** — Design decisions, trade-offs, and lessons learned
- **[Rebranding](./rebranding.md)** — Replace NVIDIA branding with your own organization's identity
