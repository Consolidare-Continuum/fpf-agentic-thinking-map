# v2.0.0 Release Publish Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the v2.0.0 release to “Adjacency Clearance” and publish the existing verified artifacts to PyPI.

**Architecture:** Keep the immutable `v2.0.0` tag and package identifiers. Change only GitHub release presentation, repair the PyPI trusted-publisher identity, rerun the existing release workflow, and verify the public artifact.

**Tech Stack:** GitHub CLI, GitHub Actions OIDC, PyPI trusted publishing, Python 3.12.

## Global Constraints

- Keep distribution name `fpf-thinking-map`.
- Keep Python import name `fpf_thinking_map`.
- Do not create another tag or version.
- Do not expose passwords, tokens, or recovery codes.

---

### Task 1: Rename the GitHub release

**Files:**
- Modify: GitHub release `v2.0.0` metadata only.

**Interfaces:**
- Consumes: existing release tag `v2.0.0`.
- Produces: release title `v2.0.0 — Adjacency Clearance (ADV-17)`.

- [ ] **Step 1: Rename the release**

```bash
gh release edit v2.0.0 \
  --repo Consolidare-Continuum/fpf-agentic-thinking-map \
  --title "v2.0.0 — Adjacency Clearance (ADV-17)"
```

- [ ] **Step 2: Verify the release title**

```bash
gh release view v2.0.0 \
  --repo Consolidare-Continuum/fpf-agentic-thinking-map \
  --json name,tagName,url
```

Expected: `name` is `v2.0.0 — Adjacency Clearance (ADV-17)` and `tagName` remains `v2.0.0`.

### Task 2: Repair PyPI trusted publishing

**Files:**
- Modify: PyPI project `fpf-thinking-map` publishing settings only.

**Interfaces:**
- Consumes: authenticated PyPI account `igareosh`.
- Produces: trusted publisher matching the GitHub OIDC claims.

- [ ] **Step 1: Authenticate the existing account**

Open:

```text
https://pypi.org/manage/project/fpf-thinking-map/settings/publishing/
```

Authenticate account `igareosh`. Use trustmaster-held 2FA recovery material only when PyPI requests the second factor. Never print or copy recovery material into logs.

- [ ] **Step 2: Replace the stale publisher binding**

Configure exactly:

```text
Owner: Consolidare-Continuum
Repository: fpf-agentic-thinking-map
Workflow: publish.yml
Environment: pypi
```

Expected: the publisher matches the OIDC claims emitted by workflow run `35451832909`.

### Task 3: Publish and verify v2.0.0

**Files:**
- Modify: no repository files.

**Interfaces:**
- Consumes: corrected PyPI publisher binding and existing release workflow.
- Produces: public PyPI version `2.0.0`.

- [ ] **Step 1: Rerun the failed workflow**

```bash
gh run rerun 35451832909 \
  --failed \
  --repo Consolidare-Continuum/fpf-agentic-thinking-map
gh run watch 35451832909 \
  --exit-status \
  --repo Consolidare-Continuum/fpf-agentic-thinking-map
```

Expected: build and publish jobs succeed.

- [ ] **Step 2: Verify public PyPI metadata**

```bash
python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen(
    "https://pypi.org/pypi/fpf-thinking-map/json",
    timeout=30,
) as response:
    payload = json.load(response)

assert payload["info"]["version"] == "2.0.0", payload["info"]["version"]
print(payload["info"]["version"])
PY
```

Expected: `2.0.0`.

- [ ] **Step 3: Verify installation from PyPI**

```bash
python3.12 -m venv /tmp/fpf-thinking-map-v2-verify
/tmp/fpf-thinking-map-v2-verify/bin/pip install --no-cache-dir fpf-thinking-map==2.0.0
/tmp/fpf-thinking-map-v2-verify/bin/python -m fpf_thinking_map.verify
```

Expected: version installs from PyPI and all package verification checks pass.
