# Publish to PyPI — Trusted Publisher

**Package:** `fpf-thinking-map`  
**Repo:** `Consolidare-Continuum/fpf-agentic-thinking-map`  
**Workflow:** `.github/workflows/publish.yml` (release `published` → build → `pypa/gh-action-pypi-publish` with OIDC)  
**GitHub environment:** `pypi`

## Status (2026-10-08)

Blocked. PyPI serves **1.9.5**. Publish runs for `v1.9.6`, `v2.0.0` and
`v2.0.1` all fail at upload with `invalid-publisher`; build and
`fpf_thinking_map.verify` pass in each run. The OIDC claims GitHub sends are
correct (`repository: Consolidare-Continuum/fpf-agentic-thinking-map`,
`repository_owner_id: 309344304`, `environment: pypi`, workflow
`publish.yml`), so the fix is entirely on pypi.org. Until then, install from
the git tag (see README).

## Required PyPI Trusted Publisher binding

Configure at  
https://pypi.org/manage/project/fpf-thinking-map/settings/publishing/

| Field | Value |
|-------|--------|
| Owner | `Consolidare-Continuum` |
| Repository | `fpf-agentic-thinking-map` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

Mismatch → Actions error `invalid-publisher` (valid OIDC token, no matching publisher).

## Re-publish a tag

After the binding matches the table above:

1. Re-run the failed **Publish to PyPI** workflow for the release, **or**
2. Re-publish the GitHub Release for that tag (only if safe / intentional).

## Authority (CC_ brain)

Standing policy: brain `governance/SPEC-ETHAN-PYPI-TRUSTED-PUBLISHER-CUSTODY.md` (APPROVED 2026-10-06).  
Secrets / recovery codes: trustmaster custody only.

## Release note naming

- Tag / commit: v2.0.0 “Positive Control” — ADV-17  
- GitHub Release title may say “Adjacency Clearance (ADV-17)”  
Both mean the same ADV-17 / 2.0.0 ship.

SIGNED: Team lead (Ethan) escalate → Felix land | 2026-10-06 | publish artifact
