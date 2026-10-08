# ISO evidence packet — fpf-thinking-map / v2.0.1

Aggregates ISO-grade references for one release. **Alignment only — no
certification claim.** The anchors are ISO/IEC 25010 (product quality),
ISO/IEC 27001 (security controls), and ISO 9001 (process control), used as
checklists.

- **Project**: `fpf-thinking-map` (`Consolidare-Continuum/fpf-agentic-thinking-map`)
- **Release**: `v2.0.1` — tag `v2.0.1` → commit `e749bb1`
- **Date**: 2026-10-08
- **Owner**: CONSOLIDARE CONTINUUM S.R.L.
- **Processed on**: dual-socket Intel Westmere server (Xeon X5675), Chieftec Vita 80 PLUS Bronze PSU

## 1) Scope and acceptance

- **Acceptance criteria source**: [`docs/deep/SPEC_V2_0_BUILD.md`](deep/SPEC_V2_0_BUILD.md)
  (2.0 line, including its regression guarantee); [`CHANGELOG.md`](../CHANGELOG.md) `[2.0.1]`.
- **Scope baseline**: 2.0.1 is docs and metadata only; the runtime is
  identical to 2.0.0. Delta `v2.0.0..v2.0.1`: `09f4fa2`, `c834421`, `d8822a4`,
  `bb4bbfc`, `34e236f`, `e749bb1`, none touching `fpf_thinking_map/`.
- **Acceptance confirmation**: verification suite 39/39 on the source tree
  and on a clean-venv install from the `v2.0.1` tag.

## 2) Quality evidence (ISO/IEC 25010 alignment)

| Characteristic | Evidence | Result |
| --- | --- | --- |
| Functional correctness | `python -m fpf_thinking_map.verify` | 39/39 PASS |
| Functional completeness (integration) | `python -m dev_mcp.test_server` | 45/45 PASS |
| Functional appropriateness | `python -m fpf_thinking_map.examples` | runs clean |
| Installability | `pip install "git+…@v2.0.1"` in a fresh venv, then `verify` | 2.0.1 installs; 39/39 |
| Compatibility | Zero runtime dependencies (stdlib-only import scan); Python ≥ 3.12 | confirmed |
| Maintainability | `ruff check fpf_thinking_map` (default rules) | 117 findings: 114 F401 unused-import, 2 E701, 1 F841. No functional defects; mostly public re-exports. Open item, not a release blocker. |
| Reliability (known limits) | [`docs/deep/ADVISORIES.md`](deep/ADVISORIES.md) | documented sharp edges ADV-01…ADV-17 |

## 3) Security evidence (ISO/IEC 27001 alignment)

- **Security baseline**: zero-dependency runtime; no network, subprocess,
  `eval`/`exec` or deserialization calls in `fpf_thinking_map/` (source scan).
  The authorization boundary is documented in
  [`docs/deep/IGNITION_LOCK_WIND_TUNNEL.md`](deep/IGNITION_LOCK_WIND_TUNNEL.md).
- **Scan/check evidence**:
  - `pip-audit -r dev_mcp/requirements.txt`: no known vulnerabilities.
  - GitHub: Dependabot security updates, secret scanning, and push
    protection are enabled.
  - `main` is protected: force-push and deletion are disallowed.
  - Publishing uses OIDC Trusted Publisher only, with no stored API token.
- **Residual risk / exceptions**:
  - Branch protection does not require signed commits or reviews.
  - Correct map authoring and host integration remain inside the trust
    boundary (see README "Scope").

## 4) Traceability and atomic commits (ISO 9001 process control)

- **Source repo**: `Consolidare-Continuum/fpf-agentic-thinking-map`, branch `main`
- **Target**: GitHub release `v2.0.1`; PyPI `fpf-thinking-map` (blocked, see §5)
- **Atomic commit chain**: `e749bb1` (release content) → `6e70b3e` (distribution-state record), one concern each
- **Change/review record**: [`CHANGELOG.md`](../CHANGELOG.md),
  [`docs/VERSION_TRACKER.md`](VERSION_TRACKER.md),
  [GitHub release v2.0.1](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/releases/tag/v2.0.1)
- **Integrity**: [`SHA256SUMS`](../SHA256SUMS) covers every tracked file
  except itself and `.github/`; `sha256sum -c SHA256SUMS` passes.

## 5) Deployment readiness

| Channel | State | Evidence |
| --- | --- | --- |
| GitHub tag + release | **Done** | `v2.0.1` |
| Versioned docs (Pages) | **Done** | `pages.yml` run 37754636459: success |
| PyPI | **Blocked** | `publish.yml` run 37754636474: build and verify pass, upload `invalid-publisher`. PyPI serves 1.9.5. Fix is on pypi.org only; see [`PUBLISH-TRUSTED-PUBLISHER.md`](PUBLISH-TRUSTED-PUBLISHER.md). |

- **Rollback path**: docs-only release. Users pin `@v2.0.0` (identical
  runtime) or PyPI `1.9.5`. Tags are immutable and nothing is overwritten.
- **Monitoring verification**: the publish-run status above, plus
  `https://pypi.org/pypi/fpf-thinking-map/json` for the live version.

## 6) Final gate

- **Status**: **GO** for GitHub distribution · **BLOCKED** for PyPI
- **Block reason**: PyPI Trusted Publisher binding does not match the
  verified OIDC claims (`Consolidare-Continuum/fpf-agentic-thinking-map`,
  `publish.yml`, environment `pypi`).
- **Approvals**:
  - Scope (Grace): pending
  - Quality (Olivia): pending
  - Security (Daniel): pending
  - Deploy readiness (Sophia): pending
  - Final release (operator): pending

---

SIGNED: Felix (Claude Code) | fpf-thinking-map | 2026-10-08 | evidence compiled; approvals not given
