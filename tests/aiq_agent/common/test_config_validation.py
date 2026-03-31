# SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for config_validation, focusing on local endpoint detection and API key requirements."""

import os
from unittest.mock import patch

import pytest

from aiq_agent.common.config_validation import _get_llm_api_key_requirements
from aiq_agent.common.config_validation import _is_local_or_private_endpoint
from aiq_agent.common.config_validation import validate_llm_configs


class TestIsLocalOrPrivateEndpoint:
    """Tests for _is_local_or_private_endpoint()."""

    @pytest.mark.parametrize(
        "base_url",
        [
            "http://localhost:8000/v1",
            "http://127.0.0.1:8000/v1",
            "http://0.0.0.0:8000/v1",
            "http://localhost/v1",
        ],
    )
    def test_localhost_variants(self, base_url):
        assert _is_local_or_private_endpoint({"base_url": base_url}) is True

    @pytest.mark.parametrize(
        "base_url",
        [
            "http://10.0.0.5:8000/v1",
            "http://10.255.255.255:8000/v1",
            "http://192.168.1.100:8000/v1",
            "http://192.168.0.1/v1",
            "http://172.16.0.1:8000/v1",
            "http://172.31.255.255:8000/v1",
        ],
    )
    def test_private_ip_ranges(self, base_url):
        assert _is_local_or_private_endpoint({"base_url": base_url}) is True

    @pytest.mark.parametrize(
        "base_url",
        [
            "https://api.openai.com/v1",
            "https://integrate.api.nvidia.com/v1",
            "https://my-company.example.com/v1",
            "https://vllm.cloud-provider.io:8000/v1",
        ],
    )
    def test_public_endpoints(self, base_url):
        assert _is_local_or_private_endpoint({"base_url": base_url}) is False

    def test_env_var_with_local_default(self):
        config = {"base_url": "${VLLM_BASE_URL:-http://localhost:8000}/v1"}
        assert _is_local_or_private_endpoint(config) is True

    def test_env_var_with_private_ip_default(self):
        config = {"base_url": "${VLLM_BASE_URL:-http://192.168.1.50:8000}/v1"}
        assert _is_local_or_private_endpoint(config) is True

    def test_env_var_with_public_default(self):
        config = {"base_url": "${VLLM_BASE_URL:-https://api.openai.com}/v1"}
        assert _is_local_or_private_endpoint(config) is False

    def test_env_var_without_default(self):
        config = {"base_url": "${VLLM_BASE_URL}"}
        assert _is_local_or_private_endpoint(config) is False

    def test_missing_base_url(self):
        assert _is_local_or_private_endpoint({}) is False

    def test_empty_base_url(self):
        assert _is_local_or_private_endpoint({"base_url": ""}) is False

    def test_non_string_base_url(self):
        assert _is_local_or_private_endpoint({"base_url": 12345}) is False


class TestGetLlmApiKeyRequirements:
    """Tests for _get_llm_api_key_requirements()."""

    def test_nim_requires_nvidia_key(self):
        config = {"_type": "nim", "model_name": "nvidia/nemotron"}
        assert _get_llm_api_key_requirements(config) == ["NVIDIA_API_KEY"]

    def test_openai_requires_openai_key(self):
        config = {"_type": "openai", "model_name": "gpt-4", "base_url": "https://api.openai.com/v1"}
        assert _get_llm_api_key_requirements(config) == ["OPENAI_API_KEY"]

    def test_openai_local_endpoint_no_key_required(self):
        config = {"_type": "openai", "model_name": "llama", "base_url": "http://localhost:8000/v1"}
        assert _get_llm_api_key_requirements(config) == []

    def test_explicit_env_var_api_key(self):
        config = {"_type": "nim", "api_key": "${MY_CUSTOM_KEY}"}
        assert _get_llm_api_key_requirements(config) == ["MY_CUSTOM_KEY"]

    def test_literal_api_key_no_env_required(self):
        config = {"_type": "openai", "api_key": "sk-literal-key-value"}  # pragma: allowlist secret
        assert _get_llm_api_key_requirements(config) == []

    def test_unknown_type_no_key_required(self):
        config = {"_type": "custom_provider"}
        assert _get_llm_api_key_requirements(config) == []


class TestValidateLlmConfigs:
    """Tests for validate_llm_configs()."""

    def test_empty_config(self):
        valid, missing = validate_llm_configs({})
        assert valid is True
        assert missing == []

    def test_vllm_local_config_valid_without_env(self):
        config = {
            "llms": {
                "intent_llm": {
                    "_type": "openai",
                    "model_name": "meta-llama/Llama-3.1-8B",
                    "base_url": "http://localhost:8000/v1",
                    "api_key": "no-key",  # pragma: allowlist secret
                },
            }
        }
        valid, missing = validate_llm_configs(config)
        assert valid is True
        assert missing == []

    @patch.dict(os.environ, {}, clear=True)
    def test_nim_config_missing_key(self):
        config = {
            "llms": {
                "test_llm": {
                    "_type": "nim",
                    "model_name": "nvidia/nemotron",
                },
            }
        }
        valid, missing = validate_llm_configs(config)
        assert valid is False
        assert "NVIDIA_API_KEY" in missing

    @patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"})  # pragma: allowlist secret
    def test_nim_config_with_key(self):
        config = {
            "llms": {
                "test_llm": {
                    "_type": "nim",
                    "model_name": "nvidia/nemotron",
                },
            }
        }
        valid, missing = validate_llm_configs(config)
        assert valid is True
        assert missing == []

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_cloud_missing_key(self):
        config = {
            "llms": {
                "test_llm": {
                    "_type": "openai",
                    "model_name": "gpt-4",
                    "base_url": "https://api.openai.com/v1",
                },
            }
        }
        valid, missing = validate_llm_configs(config)
        assert valid is False
        assert "OPENAI_API_KEY" in missing

    def test_mixed_providers_local_vllm_valid(self):
        """vLLM on local endpoint should not require any API key."""
        config = {
            "llms": {
                "vllm_llm": {
                    "_type": "openai",
                    "model_name": "llama",
                    "base_url": "http://192.168.1.50:8000/v1",
                },
            }
        }
        valid, missing = validate_llm_configs(config)
        assert valid is True
        assert missing == []
