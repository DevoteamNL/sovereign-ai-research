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

"""NAT register function for Serper news search tool."""

import logging
import os

from pydantic import Field
from pydantic import SecretStr

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from .news_search import NewsSearchTool

logger = logging.getLogger(__name__)

# Track if we've already warned about missing API key to avoid duplicate warnings
_missing_key_warned = False


class NewsSearchToolConfig(FunctionBaseConfig, name="news_search"):
    """
    Configuration for the news search tool.

    Tool that searches for current news articles using Google News (Serper).
    Requires a SERPER_API_KEY environment variable or config.
    """

    timeout: int = Field(
        default=30,
        description="Timeout in seconds for the search requests",
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of news results to return",
    )
    serper_api_key: SecretStr | None = Field(
        default=None,
        description="The API key for Serper (Google News)",
    )


@register_function(config_type=NewsSearchToolConfig)
async def news_search(tool_config: NewsSearchToolConfig, builder: Builder):
    """Register news search tool using Google News (Serper)."""
    # Set environment variable if provided in config
    if not os.environ.get("SERPER_API_KEY") and tool_config.serper_api_key:
        os.environ["SERPER_API_KEY"] = tool_config.serper_api_key.get_secret_value()

    serper_api_key = os.environ.get("SERPER_API_KEY")

    if not serper_api_key:
        global _missing_key_warned
        if not _missing_key_warned:
            logger.warning(
                "SERPER_API_KEY not found. The news search tool will be registered but will "
                "return an error when called. To enable: set SERPER_API_KEY in your environment, "
                ".env file, or specify the API key in your workflow config (SERPER_API_KEY)."
            )
            _missing_key_warned = True

        async def _news_search_stub(query: str) -> str:
            """News search tool (unavailable - missing SERPER_API_KEY)."""
            return (
                "Error: News search is unavailable because SERPER_API_KEY is not set.\n"
                "To enable this tool:\n"
                "1. Get an API key from https://serper.dev/\n"
                "2. Set the API key in your environment or .env file\n"
                "   (alternatively, specify the API key in your workflow config)\n"
                "3. Restart the application"
            )

        yield FunctionInfo.from_fn(
            _news_search_stub,
            description=_news_search_stub.__doc__,
        )
        return

    tool = NewsSearchTool(
        serper_api_key=serper_api_key,
        timeout=tool_config.timeout,
        max_results=tool_config.max_results,
    )

    async def _news_search(query: str) -> str:
        """Searches for current news articles and breaking stories.

        This tool returns recent news from Google News with publication dates,
        sources, and snippets for queries about current events, recent
        developments, industry news, product launches, policy changes,
        and time-sensitive topics.

        Args:
            query (str): The search query string.

        Returns:
            str: Formatted string with news search results.
        """
        return await tool.search(query)

    yield FunctionInfo.from_fn(
        _news_search,
        description=_news_search.__doc__,
    )
