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
"""News search tool using Serper (Google News).

This module contains the NAT-independent NewsSearchTool class.
"""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

SERPER_NEWS_API_URL = "https://google.serper.dev/news"


class NewsSearchTool:
    """
    News search tool for current news articles using Google News (Serper).

    This class is NAT-independent and receives all dependencies via constructor.

    Example:
        >>> tool = NewsSearchTool(
        ...     serper_api_key="your-key",  # pragma: allowlist secret
        ...     timeout=30,
        ...     max_results=10,
        ... )
        >>> result = await tool.search("AI regulation 2026")
    """

    def __init__(
        self,
        serper_api_key: str,
        *,
        timeout: int = 30,
        max_results: int = 10,
    ) -> None:
        self.serper_api_key = serper_api_key
        self.timeout = timeout
        self.max_results = max_results

    async def _fetch_news(
        self,
        query: str,
        num: int,
    ) -> dict[str, Any]:
        """Fetch news results from Serper."""
        payload: dict[str, Any] = {
            "q": query,
            "num": min(num, 20),
        }

        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                SERPER_NEWS_API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Serper News API error: {response.status} - {text}")
                return await response.json()

    @staticmethod
    def format_results(results: list[dict[str, Any]]) -> str:
        """Format Serper News results."""
        if not results:
            return "No news articles found."

        formatted_articles = []
        for i, article in enumerate(results, 1):
            title = article.get("title", "Unknown Title")
            link = article.get("link", "")
            snippet = article.get("snippet", "")
            date = article.get("date", "Unknown Date")
            source = article.get("source", "Unknown Source")

            article_str = (
                f"{i}. **{title}**\n"
                f"   - **Source**: {source}\n"
                f"   - **Date**: {date}\n"
                f"   - **Snippet**: {snippet}\n"
                f"   - **Link**: {link}"
            )
            formatted_articles.append(article_str)

        return "\n\n".join(formatted_articles)

    async def search(self, query: str) -> str:
        """
        Search for current news articles.

        Args:
            query: The search query string.

        Returns:
            Formatted string with news search results.
        """
        if not query:
            return "Error: 'query' argument is required"

        logger.info(f"News search (serper) for: {query}")

        try:
            result = await self._fetch_news(query, self.max_results)
            articles = result.get("news", [])[: self.max_results]
            return self.format_results(articles)

        except TimeoutError:
            logger.error(f"News search timed out for query: {query}")
            return f"News search timed out after {self.timeout}s for query: {query}"
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return f"News search failed: {str(e)}"
