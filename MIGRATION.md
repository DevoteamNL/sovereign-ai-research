<!--
SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-->

# Migration: project home moved to `rh-ai-quickstart/rh-research`

On **2026-04-20**, active development of this Red Hat-flavored fork of the NVIDIA AI-Q Blueprint moved from a private personal fork (`RobbieJ/aiq`) to the Red Hat AI Quickstarts organization at [`rh-ai-quickstart/rh-research`](https://github.com/rh-ai-quickstart/rh-research).

This file explains the relationship between the three repositories involved, how git history is laid out, and how to set up your local clone.

## Repository layout

| Role | Repository | Purpose |
|---|---|---|
| **Canonical home** | [`rh-ai-quickstart/rh-research`](https://github.com/rh-ai-quickstart/rh-research) | Where current development, releases, issues, and pull requests live. Clone this. |
| **Upstream** | [`NVIDIA-AI-Blueprints/aiq`](https://github.com/NVIDIA-AI-Blueprints/aiq) | The original NVIDIA AI-Q Blueprint. Used as a source of periodic merges for new NVIDIA features and fixes. |
| **Personal mirror** | `RobbieJ/aiq` (private) | Preserved as-is for historical reference. No new work lands here. |

## History

`rh-ai-quickstart/rh-research` was initialized as a GitHub fork of `NVIDIA-AI-Blueprints/aiq`, so its commit history is a strict superset of NVIDIA's. On top of the NVIDIA base, this fork adds approximately 30 commits of Red Hat-flavored customizations across three broad areas:

- **vLLM / open-model support** — `configs/config_web_vllm.yml`, intent-LLM base URL override, config validation that skips API-key checks for local and private endpoints, vLLM e2e test coverage, and model-aware thinking prefixes so Nemotron retains `/think` directives while other models get clean prompts
- **Additional data sources** — `paper_search` (Google Scholar via Serper) and `news_search` (Serper news) registered across the clarifier, shallow agent, and `/v1/data_sources` API
- **Frontend rebrand** — logo (fedora SVG), Red Hat palette (#EE0000), Red Hat Display/Text fonts, app name "Red Hat Research", favicon; KUI design-system palette tokens overridden via `globals.css`

See `CHANGELOG.md` for the full feature list.

The migration itself landed as a single fast-forward push of `develop`, tagged `v2.1.0-redhat`, with no history rewrites. Every commit in the personal-fork history remains intact and visible on `rh-research`.

## Setting up a clone

```bash
git clone https://github.com/rh-ai-quickstart/rh-research.git
cd rh-research

# Add NVIDIA upstream for periodic syncs
git remote add upstream https://github.com/NVIDIA-AI-Blueprints/aiq.git
git fetch upstream
```

### Syncing from NVIDIA upstream

```bash
git checkout develop
git fetch upstream
git merge upstream/develop         # or rebase; both work since history is compatible
git push origin develop
```

Upstream merge windows are batched rather than continuous. See the open issue on `rh-research` tagged `upstream-merge` for the current queue.

## Attribution

This project remains Apache-2.0 licensed. All copyright headers continue to read `Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.` — that attribution is a requirement of the upstream license, not a statement of current maintainership.

Red Hat contributions are layered on top of the NVIDIA base and are similarly Apache-2.0 licensed. See `LICENSE` and `LICENSE-THIRD-PARTY` for the full legal text and third-party dependencies.

## Deferred work

A follow-up merge of the 8 NVIDIA upstream commits dated 2026-04-15 through 2026-04-17 (data-source registry refactor, authlib bump, WebSocket auth revert, periodic cleanup fix, CVE-driven pytest bump, and unavailable-tool error surfacing) is tracked on `rh-research` as a separate issue and will land after the migration settles.

## Where to find old pull requests and issues

Pull requests and issues filed on `RobbieJ/aiq` are preserved at the personal mirror. Their discussion threads do not migrate automatically with `git push`; each PR closed during migration has a comment pointing to its landing commit on `rh-research`.
