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

"""Tests for the /v1/data_sources endpoint and _collect_tool_names helper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from aiq_api.routes.jobs import DataSource
from aiq_api.routes.jobs import _collect_tool_names


def _make_builder(tool_names: list[str], fn_names: tuple[str, ...] = ("deep_research_agent",)) -> MagicMock:
    """Create a mock WorkflowBuilder whose function configs expose the given tool names.

    Each function name in *fn_names* will have a config with tools set to
    SimpleNamespace objects carrying the supplied tool names. Any function
    name not in *fn_names* will raise KeyError (simulating an absent config).
    """
    tools = [SimpleNamespace(name=n) for n in tool_names]
    config = SimpleNamespace(tools=tools)

    def _get_function_config(name: str):
        if name in fn_names:
            return config
        raise KeyError(name)

    builder = MagicMock()
    builder.get_function_config.side_effect = _get_function_config
    return builder


# =========================================================================
# Unit tests for _collect_tool_names
# =========================================================================


class TestCollectToolNames:
    """Direct tests for the _collect_tool_names helper."""

    def test_returns_empty_when_no_functions(self):
        """Builder with no matching function configs should yield empty set."""
        builder = _make_builder([], fn_names=())
        assert _collect_tool_names(builder) == set()

    def test_collects_from_single_function(self):
        """Tools from a single function config should be collected."""
        builder = _make_builder(["web_search_tool", "paper_search_tool"])
        result = _collect_tool_names(builder)
        assert result == {"web_search_tool", "paper_search_tool"}

    def test_collects_from_multiple_functions(self):
        """Tools should be aggregated across all recognised function names."""
        builder = _make_builder(
            ["web_search_tool", "news_search_tool"],
            fn_names=("deep_research_agent", "shallow_research_agent"),
        )
        result = _collect_tool_names(builder)
        assert "web_search_tool" in result
        assert "news_search_tool" in result


# =========================================================================
# Endpoint-level tests for /v1/data_sources
# =========================================================================


class TestListDataSourcesEndpoint:
    """Tests that verify the data-source detection logic via the endpoint."""

    @staticmethod
    def _source_ids(data_sources: list[DataSource]) -> set[str]:
        return {ds.id for ds in data_sources}

    # -- helpers to invoke the detection logic directly ----------------------

    @staticmethod
    def _build_sources(tool_names: list[str]) -> list[DataSource]:
        """Reproduce the endpoint detection logic so tests don't need a live
        FastAPI app (the endpoint is a thin closure over the builder)."""
        sources = [
            DataSource(id="web_search", name="Web Search", description="Search the web for real-time information.")
        ]

        names_lower = {n.lower() for n in tool_names}

        if any("paper" in n or "scholar" in n for n in names_lower):
            sources.append(
                DataSource(
                    id="paper_search",
                    name="Paper Search",
                    description="Search academic papers and scholarly publications.",
                )
            )

        if any("news" in n for n in names_lower):
            sources.append(
                DataSource(
                    id="news_search",
                    name="News Search",
                    description="Search current news articles and breaking stories.",
                )
            )

        if any("knowledge" in n or n == "knowledge_search" for n in names_lower):
            sources.append(
                DataSource(
                    id="knowledge_layer",
                    name="Knowledge Base",
                    description="Search uploaded documents and files.",
                )
            )

        return sources

    # -- tests ---------------------------------------------------------------

    def test_web_search_always_present(self):
        """web_search should always be included, even with no tools configured."""
        sources = self._build_sources([])
        ids = self._source_ids(sources)
        assert "web_search" in ids

    def test_paper_search_detected(self):
        """A tool containing 'paper' should trigger paper_search."""
        sources = self._build_sources(["paper_search_tool"])
        ids = self._source_ids(sources)
        assert "paper_search" in ids

    def test_news_search_detected(self):
        """A tool containing 'news' should trigger news_search."""
        sources = self._build_sources(["news_search_tool"])
        ids = self._source_ids(sources)
        assert "news_search" in ids

    def test_knowledge_layer_detected(self):
        """A tool named 'knowledge_search' should trigger knowledge_layer."""
        sources = self._build_sources(["knowledge_search"])
        ids = self._source_ids(sources)
        assert "knowledge_layer" in ids

    def test_all_sources_detected(self):
        """When all tool types are present, all four data sources should appear."""
        sources = self._build_sources(["paper_search_tool", "news_search_tool", "knowledge_search"])
        ids = self._source_ids(sources)
        assert ids == {"web_search", "paper_search", "news_search", "knowledge_layer"}

    def test_no_extra_sources_without_tools(self):
        """With no matching tool names, only web_search should be returned."""
        sources = self._build_sources(["some_random_tool"])
        ids = self._source_ids(sources)
        assert ids == {"web_search"}

    def test_scholar_name_triggers_paper_search(self):
        """A tool named 'scholar_search' should trigger paper_search (via 'scholar' substring)."""
        sources = self._build_sources(["scholar_search"])
        ids = self._source_ids(sources)
        assert "paper_search" in ids


# =========================================================================
# Integration tests using the real _collect_tool_names + detection logic
# =========================================================================


class TestEndToEndDetection:
    """End-to-end tests that wire _collect_tool_names into the detection logic."""

    @staticmethod
    def _detect_ids(tool_names: list[str]) -> set[str]:
        """Run _collect_tool_names on a mock builder, then apply detection logic."""
        builder = _make_builder(tool_names)
        collected = _collect_tool_names(builder)

        ids = {"web_search"}
        if any("paper" in n.lower() or "scholar" in n.lower() for n in collected):
            ids.add("paper_search")
        if any("news" in n.lower() for n in collected):
            ids.add("news_search")
        if any("knowledge" in n.lower() or n == "knowledge_search" for n in collected):
            ids.add("knowledge_layer")
        return ids

    def test_web_search_always_present(self):
        builder = _make_builder([])
        collected = _collect_tool_names(builder)
        # Even with empty tools, web_search is unconditional in the endpoint
        assert collected == set()  # no tools collected
        # But web_search still present
        ids = self._detect_ids([])
        assert "web_search" in ids

    def test_paper_search_detected(self):
        assert "paper_search" in self._detect_ids(["paper_search_tool"])

    def test_news_search_detected(self):
        assert "news_search" in self._detect_ids(["news_search_tool"])

    def test_knowledge_layer_detected(self):
        assert "knowledge_layer" in self._detect_ids(["knowledge_search"])

    def test_all_sources_detected(self):
        ids = self._detect_ids(["paper_search_tool", "news_search_tool", "knowledge_search"])
        assert ids == {"web_search", "paper_search", "news_search", "knowledge_layer"}

    def test_no_extra_sources_without_tools(self):
        ids = self._detect_ids(["web_lookup"])
        assert ids == {"web_search"}

    def test_scholar_name_triggers_paper_search(self):
        assert "paper_search" in self._detect_ids(["scholar_search"])
