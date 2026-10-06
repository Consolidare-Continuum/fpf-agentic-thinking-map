# v2.0.0 release publish recovery

## Outcome

- Rename the GitHub release title from `v2.0.0 — Positive Control (ADV-17)` to `v2.0.0 — Adjacency Clearance (ADV-17)`.
- Keep the distribution name `fpf-thinking-map`, Python import name, tag, version, artifacts, and ADV-17 implementation unchanged.
- Publish the existing v2.0.0 artifacts to PyPI.

## Authentication and publishing

1. Authenticate the existing PyPI account `igareosh` using trustmaster-held recovery material where required.
2. Bind the `fpf-thinking-map` trusted publisher to:
   - owner: `Consolidare-Continuum`
   - repository: `fpf-agentic-thinking-map`
   - workflow: `publish.yml`
   - environment: `pypi`
3. Rerun failed workflow run `35451832909`; do not create another tag or version.

## Verification

- GitHub release title is the approved replacement.
- Publish workflow succeeds.
- PyPI JSON reports version `2.0.0`.
- A clean environment installs `fpf-thinking-map==2.0.0` and its verification command passes.

## Failure handling

- Do not expose credentials or recovery codes.
- If account authentication cannot be completed, keep ATM-ADV-083 paused with the exact missing input.
- Do not rename package or import identifiers.
