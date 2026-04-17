# SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Agent-local prompt loading utilities.

This module provides utilities for loading prompts co-located with agents.
Each agent package has a prompts/ directory containing its Jinja2 templates.

Also provides model-aware thinking prefix helpers so that Nemotron/NIM models
get their ``/no_think`` or ``/think`` directives while other models (vLLM,
OpenAI, etc.) get clean prompts.
"""

import logging
import re
from pathlib import Path
from typing import Any

import jinja2
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

# Regex matching NVIDIA Nemotron model names that understand /think and /no_think.
# Matches HF names (nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) and vLLM served
# names (nvidia/nemotron-3-nano-30b-a3b) alike.
_NEMOTRON_PATTERN = re.compile(r"(nvidia[/-])?.*nemotron", re.IGNORECASE)


class PromptError(Exception):
    """Error loading or rendering prompts."""

    pass


def load_prompt(path: Path, name: str) -> str:
    """
    Load a prompt template from an agent's prompts/ directory.

    Args:
        path: Path to the prompts directory.
        name: Name of the prompt file (e.g., 'system' or 'system.j2').

    Returns:
        The prompt template as a string.

    Raises:
        PromptError: If the prompt file cannot be found.
    """
    # Try exact name first, then with .j2 extension
    prompt_path = path / name
    if not prompt_path.exists() and not name.endswith(".j2"):
        prompt_path = path / f"{name}.j2"

    if not prompt_path.exists():
        raise PromptError(f"Prompt file not found: {name} in {path}")

    try:
        return prompt_path.read_text()
    except Exception as e:
        raise PromptError(f"Failed to load prompt {name}: {e}") from e


def render_prompt_template(template: str, **kwargs: Any) -> str:
    """
    Render a Jinja2 template with the given variables.

    Args:
        template: The template string.
        **kwargs: Variables to substitute in the template.

    Returns:
        The rendered template.

    Raises:
        PromptError: If template rendering fails.
    """
    try:
        jinja_template = jinja2.Template(template, undefined=jinja2.Undefined)
        return jinja_template.render(**kwargs)
    except jinja2.TemplateError as e:
        raise PromptError(f"Failed to render template: {e}") from e


def _get_model_name(llm: BaseChatModel) -> str:
    """Extract model name from a LangChain chat model, regardless of provider."""
    for attr in ("model_name", "model", "azure_deployment"):
        val = getattr(llm, attr, None)
        if isinstance(val, str):
            return val
    return ""


def _is_nim_endpoint(llm: BaseChatModel) -> bool:
    """Return True if *llm* is served by the NVIDIA NIM API (not vLLM/OpenAI-compatible)."""
    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        return isinstance(llm, ChatNVIDIA)
    except ImportError:
        return False


def is_nemotron(llm: BaseChatModel) -> bool:
    """Return True if *llm* is a Nemotron model on a NIM endpoint that understands /think directives.

    vLLM serves the same models but does not interpret /think or /no_think
    directives — they get echoed as literal text. Only NIM endpoints handle them.
    """
    return _is_nim_endpoint(llm) and bool(_NEMOTRON_PATTERN.search(_get_model_name(llm)))


def get_thinking_prefix(llm: BaseChatModel, *, enable: bool = False) -> str:
    """Return the thinking directive prefix appropriate for *llm*.

    For Nemotron models this returns ``/think\\n\\n`` or ``/no_think\\n\\n``.
    For all other models an empty string is returned so prompts stay clean.

    Args:
        llm: The LangChain chat model that will receive the prompt.
        enable: Whether to enable (True) or disable (False) extended thinking.

    Returns:
        A string to prepend to the system prompt, possibly empty.
    """
    if not is_nemotron(llm):
        return ""
    return "/think\n\n" if enable else "/no_think\n\n"
