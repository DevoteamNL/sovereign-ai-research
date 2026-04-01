# Security Dependency Updates

**Date:** 2026-03-31
**Branch:** `fix/dependency-vulnerabilities`

## Summary

Addressed 45 Dependabot alerts (16 high, 25 medium, 4 low) by updating dependency version pins and lock files. Reduced to 0 npm vulnerabilities and resolved all fixable Python vulnerabilities.

## Python Dependency Updates

Minimum version pins added to `pyproject.toml` to force transitive dependency upgrades:

| Package | From | To | Severity | CVE / Issue | Notes |
|---------|------|----|----------|-------------|-------|
| `langchain-core` | 1.2.12 | >=1.2.22 | **High** | Path traversal in legacy `load_prompt` functions | We use our own `load_prompt` in `prompt_utils.py`, not LangChain's. Upgraded defensively. |
| `langgraph` | 1.0.8 | >=1.0.10 | **Medium** | Unsafe msgpack deserialization in checkpoint loading | We use LangGraph checkpoints for conversation persistence. Direct exposure via `AsyncSqliteSaver` and `AsyncPostgresSaver`. |
| `pyasn1` | 0.6.2 | >=0.6.3 | **High** | DoS via unbounded recursion | Transitive via `cryptography` chain. Low practical risk but easy fix. |
| `cryptography` | 46.0.5 | >=46.0.6 | **Low** | Incomplete DNS name constraint enforcement on peer names | Minor TLS verification edge case. |
| `pypdf` | 6.7.0 | >=6.9.2 | **Medium** (x9) + **Low** (x1) | Multiple DoS: infinite loops, memory exhaustion on malformed PDFs | 10 separate CVEs. Only relevant if users upload untrusted PDFs via the knowledge layer. Upgraded to latest patch covering all known issues. |
| `Pygments` | 2.19.2 | >=2.20.0 | **Low** | ReDoS in GUID matching regex | Transitive via Sphinx/docs tooling. |
| `nltk` | 3.9.3 | >=3.9.4 | **High** + **Medium** | Unauthenticated remote shutdown in wordnet_app; XSS | The wordnet_app vuln requires running NLTK's web server (we don't). XSS fix available in 3.9.4. One additional recursion DoS has no fix yet. |

### Not Updated

| Package | Reason |
|---------|--------|
| `requests` (2.32.5 → 2.33.0) | Blocked by `ragaai-catalyst` which pins `requests>=2.32.3,<2.33.dev0`. Vulnerability is medium-severity insecure temp file reuse — low risk for our usage pattern. Will resolve when `ragaai-catalyst` updates its pin. |
| `diskcache` (5.6.3) | No fix available. Unsafe pickle deserialization — only exploitable if attacker can write to the cache directory. Not a concern for our deployment model. |
| `nltk` recursion DoS | No fix available upstream. Low practical risk — requires crafted JSONTaggedDecoder input. |

## npm Dependency Updates

| Package | From | To | Severity | Issue | Notes |
|---------|------|----|----------|-------|-------|
| `next` | ^16.1.1 | ^16.1.7 | **Medium** | Unbounded `/next/image` disk cache growth | Direct dependency. Updated minimum version pin. |
| `happy-dom` | ^20.3.4 | ^20.8.9 | **High** (x2) | Unsanitized export names as executable code; cookie origin mismatch | Dev dependency (test environment only). No production risk, but updated for hygiene. |
| `picomatch` | 4.0.3 / 2.3.1 | >=4.0.4 | **High** + **Medium** | ReDoS via extglob quantifiers; method injection in POSIX char classes | Transitive. Applied npm override to force minimum version. |
| `brace-expansion` | 1.1.12 / 2.0.2 | >=2.0.3 | **Medium** (x2) | Zero-step sequence causes process hang and memory exhaustion | Transitive. Applied npm override. |
| `dompurify` | 3.3.1 | >=3.3.2 | **Medium** | Mutation-XSS via re-contextualization | Transitive via `isomorphic-dompurify`. Applied npm override. |
| `minimatch` | (old) | (latest) | **High** | Multiple ReDoS vulnerabilities | Resolved via `npm audit fix`. |
| `rollup` | 4.x | (patched) | **High** | Arbitrary file write via path traversal | Dev dependency. Resolved via `npm audit fix`. |

## Verification

After updates:
- `npm audit`: 0 vulnerabilities
- `npx tsc --noEmit`: passes (no type errors)
- `uv lock`: resolves successfully with updated versions
- Python packages verified: `langchain-core>=1.2.22`, `langgraph>=1.0.10`, `pyasn1>=0.6.3`, `pypdf>=6.9.2`, `nltk>=3.9.4`, `cryptography>=46.0.6`, `Pygments>=2.20.0`

## Risk Assessment

**Residual risk after updates:**
- `requests` temp file vulnerability — mitigated by deployment model (containers with ephemeral filesystems)
- `diskcache` pickle deserialization — mitigated by filesystem access controls
- `nltk` recursion DoS — mitigated by not exposing NLTK's JSONTaggedDecoder to untrusted input
- `pypdf` DoS class vulnerabilities — now patched, but document upload feature should validate file sizes and types as defense-in-depth
