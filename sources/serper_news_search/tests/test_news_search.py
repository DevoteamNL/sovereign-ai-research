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

"""Tests for NewsSearchTool class."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from serper_news_search.news_search import NewsSearchTool


class TestNewsSearchToolInit:
    """Tests for NewsSearchTool initialization."""

    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        tool = NewsSearchTool(serper_api_key="test-key")  # pragma: allowlist secret

        assert tool.serper_api_key == "test-key"  # pragma: allowlist secret
        assert tool.timeout == 30  # default
        assert tool.max_results == 10  # default

    def test_init_with_all_params(self):
        """Test initialization with all parameters."""
        tool = NewsSearchTool(
            serper_api_key="test-key",  # pragma: allowlist secret
            timeout=60,
            max_results=20,
        )

        assert tool.serper_api_key == "test-key"  # pragma: allowlist secret
        assert tool.timeout == 60
        assert tool.max_results == 20

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        tool = NewsSearchTool(serper_api_key="test-key", timeout=120)  # pragma: allowlist secret

        assert tool.timeout == 120

    def test_init_with_custom_max_results(self):
        """Test initialization with custom max_results."""
        tool = NewsSearchTool(serper_api_key="test-key", max_results=50)  # pragma: allowlist secret

        assert tool.max_results == 50


class TestFormatResults:
    """Tests for format_results static method."""

    def test_format_results_empty_list(self):
        """Test formatting empty results returns appropriate message."""
        result = NewsSearchTool.format_results([])

        assert result == "No news articles found."

    def test_format_results_single_article(self, sample_articles):
        """Test formatting a single article."""
        result = NewsSearchTool.format_results([sample_articles[0]])

        assert "1. **Test Article 1**" in result
        assert "**Source**: Test Source" in result
        assert "**Date**: 1 hour ago" in result
        assert "**Snippet**: This is a test snippet." in result
        assert "**Link**: https://example.com/article1" in result

    def test_format_results_multiple_articles(self, sample_articles):
        """Test formatting multiple articles."""
        result = NewsSearchTool.format_results(sample_articles)

        assert "1. **Test Article 1**" in result
        assert "2. **Test Article 2**" in result
        assert "\n\n" in result  # Articles should be separated

    def test_format_results_missing_fields(self):
        """Test formatting articles with missing fields uses defaults."""
        articles = [{"title": "Only Title"}]
        result = NewsSearchTool.format_results(articles)

        assert "1. **Only Title**" in result
        assert "**Source**: Unknown Source" in result
        assert "**Date**: Unknown Date" in result

    def test_format_results_all_fields_missing(self):
        """Test formatting articles with all fields missing."""
        articles = [{}]
        result = NewsSearchTool.format_results(articles)

        assert "1. **Unknown Title**" in result


class TestSearch:
    """Tests for search method."""

    @pytest.mark.asyncio
    async def test_search_empty_query(self, news_search_tool):
        """Test search with empty query returns error."""
        result = await news_search_tool.search("")

        assert result == "Error: 'query' argument is required"

    @pytest.mark.asyncio
    async def test_search_success(self, news_search_tool, sample_news_response):
        """Test successful search with mocked API response."""
        with patch.object(
            news_search_tool,
            "_fetch_news",
            new_callable=AsyncMock,
            return_value=sample_news_response,
        ):
            result = await news_search_tool.search("AI regulation")

        assert "AI Regulation Bill Passes Senate" in result
        assert "NVIDIA Announces New GPU Architecture" in result

    @pytest.mark.asyncio
    async def test_search_timeout_error(self, news_search_tool):
        """Test search handles timeout error gracefully."""
        with patch.object(
            news_search_tool,
            "_fetch_news",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Request timed out"),
        ):
            result = await news_search_tool.search("test query")

        assert "News search timed out" in result
        assert "30s" in result

    @pytest.mark.asyncio
    async def test_search_general_exception(self, news_search_tool):
        """Test search handles general exceptions gracefully."""
        with patch.object(
            news_search_tool,
            "_fetch_news",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            result = await news_search_tool.search("test query")

        assert "News search failed" in result
        assert "API Error" in result


class TestFetchNews:
    """Tests for _fetch_news internal method."""

    @pytest.mark.asyncio
    async def test_fetch_builds_correct_payload(self, news_search_tool):
        """Test that fetch builds correct API payload."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"news": []})

        mock_session = MagicMock()
        mock_context = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(),
        )
        mock_session.post = MagicMock(return_value=mock_context)

        with patch("aiohttp.ClientSession") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock()

            await news_search_tool._fetch_news(  # noqa: SLF001
                query="test query",
                num=10,
            )

        # Verify post was called with correct arguments
        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args[1]
        payload = call_kwargs["json"]

        assert payload["q"] == "test query"
        assert payload["num"] == 10

    @pytest.mark.asyncio
    async def test_fetch_num_capped_at_20(self, news_search_tool):
        """Test that num parameter is capped at 20 (API limit)."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"news": []})

        mock_session = MagicMock()
        mock_context = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(),
        )
        mock_session.post = MagicMock(return_value=mock_context)

        with patch("aiohttp.ClientSession") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock()

            await news_search_tool._fetch_news(  # noqa: SLF001
                query="test",
                num=50,  # More than limit
            )

        call_kwargs = mock_session.post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["num"] == 20  # Should be capped
