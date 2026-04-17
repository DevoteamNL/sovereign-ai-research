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

"""Pytest fixtures for news search tests."""

import pytest
from serper_news_search.news_search import NewsSearchTool


@pytest.fixture
def news_search_tool():
    """Create a NewsSearchTool instance for testing."""
    return NewsSearchTool(
        serper_api_key="test-api-key",  # pragma: allowlist secret
        timeout=30,
        max_results=10,
    )


@pytest.fixture
def sample_news_response():
    """Sample Serper News API response for testing."""
    return {
        "news": [
            {
                "title": "AI Regulation Bill Passes Senate",
                "link": "https://example.com/ai-regulation",
                "snippet": "The US Senate passed a landmark AI regulation bill...",
                "date": "2 hours ago",
                "source": "Reuters",
            },
            {
                "title": "NVIDIA Announces New GPU Architecture",
                "link": "https://example.com/nvidia-gpu",
                "snippet": "NVIDIA unveiled its next-generation GPU architecture...",
                "date": "5 hours ago",
                "source": "TechCrunch",
            },
        ]
    }


@pytest.fixture
def sample_articles():
    """Sample article data for format testing."""
    return [
        {
            "title": "Test Article 1",
            "link": "https://example.com/article1",
            "snippet": "This is a test snippet.",
            "date": "1 hour ago",
            "source": "Test Source",
        },
        {
            "title": "Test Article 2",
            "link": "https://example.com/article2",
            "snippet": "Another test snippet.",
            "date": "3 hours ago",
            "source": "Another Source",
        },
    ]
