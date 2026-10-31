# fpf-thinking-map

A small Python library that tracks the state of a multi-step agent workflow
and answers one question: *is this next move allowed right now, and if not,
why?*

You describe a workflow as a graph (contexts, roles, evidence, gates,
transitions). Your agent harness feeds the library the current state and the
move the agent proposes. The library returns a legal/illegal outcome with the
reason and a trace. It does not call a model, run tools, poll, or schedule
anything.

**PyPI:** [`fpf-thinking-map`](https://pypi.org/project/fpf-thinking-map/) · **Current:** **2.1.0** · **License:** MIT

[![PyPI](https://img.shields.io/pypi/v/fpf-thinking-map?style=flat-square&label=PyPI)](https://pypi.org/project/fpf-thinking-map/)
[![Python](https://img.shields.io/pypi/pyversions/fpf-thinking-map?style=flat-square&label=Python)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

## Install

Requires **Python ≥ 3.12**. No runtime dependencies.

```bash
pip install "fpf-thinking-map==2.1.0"
python -m fpf_thinking_map.verify    # the package's own self-tests, 40 checks
python -m fpf_thinking_map.examples
```

Other releases on the index: [`2.0.1`](https://pypi.org/project/fpf-thinking-map/2.0.1/), [`2.0.0`](https://pypi.org/project/fpf-thinking-map/2.0.0/), [`1.9.6`](https://pypi.org/project/fpf-thinking-map/1.9.6/).

## Minimal example

```python
from fpf_thinking_map import (
    SemanticMap,
    ContextPrimitive,
    RolePrimitive,
    GatePrimitive,
    GateCheck,
    TransitionPrimitive,
    RuntimeBinding,
    ThinkingMapTraversal,
)

semantic_map = SemanticMap()
semantic_map.register_context(ContextPrimitive("deploy", "Deploy"))
semantic_map.register_role(RolePrimitive("owner", "Owner", "deploy"))
semantic_map.register_gate(
    GatePrimitive(
        "release_gate",
        "Release gate",
        "deploy",
        checks=[
            GateCheck(
                "tests",
                "Tests are green",
                required_evidence=["test_results"],
            )
        ],
    )
)
semantic_map.register_transition(
    TransitionPrimitive(
        "ship",
        "Ship release",
        "deploy",
        "candidate",
        "released",
        required_gate_id="release_gate",
        required_evidence=["test_results"],
    )
)

traversal = ThinkingMapTraversal(semantic_map)
state = traversal.build_active_state(
    RuntimeBinding(
        task="release",
        actor_role_ids=["owner"],
        active_context_id="deploy",
        current_evidence=["test_results"],
    ),
    current_state="candidate",
)

inspection = traversal.step(state)
result = traversal.attempt_transition(state, "ship")
print(inspection.kind, result.kind, state.current_state)
# OutcomeKind.CONTINUE OutcomeKind.CONTINUE released
```

Replace the deploy vocabulary with your own contexts, roles, evidence and gates.

## What it does

- Holds explicit traversal state: current context, state, and evidence.
- Checks evidence presence and freshness. Freshness decays over **traversal
  steps**, not wall-clock time.
- Evaluates gates, guards and transitions and says which moves are legal.
- Supports cross-context bridges with validated writeback.
- Supports human authorization (`AuthorizationReceipt`): scoped, non-replayable.
- Distinguishes waiting on external input (`PendingInput` / `AWAIT`) from idle.
- Gives a proposed move a concrete identity (`MoveIntent`) that can be inspected.
- Can checkpoint and restore a paused traversal (`ActiveState.checkpoint()`,
  `from_checkpoint()`); restore is all-or-nothing and never repairs.

Given the same map, state, evidence and receipts, it returns the same result.
The core modules call no clock, random source, network or model.

## Division of work

| Agent / host | This library |
| --- | --- |
| Interprets the task | Holds explicit traversal state |
| Generates options | Computes which moves are legal |
| Collects evidence | Checks presence and freshness |
| Proposes a move | Inspects or attempts that move |
| Explains the result | Returns a bounded outcome and trace |
| Requests human input | Enforces the authorization boundary |
| Runs tools and jobs | Never executes, polls or schedules them |

## Limits

- **It only constrains what is routed through it.** A harness or agent that
  does not call the library is not constrained. There is no sandbox.
- **State lives in the host process.** The library keeps no storage of its
  own; use `checkpoint()` to persist a paused traversal.
- **Several inputs are self-asserted.** For example `active_context_id`
  (advisory ADV-03): the harness must own continuity.
- **Defaults are minimal.** Stale evidence warns but does not block unless a
  gate requires it, and `requires_human_authorization` defaults off.
- **It is not a universal reasoner,** a vector store, a tool runner or
  scheduler, or a certificate that an agent system is safe.

Full list of integrator boundaries: [ADVISORIES.md](docs/deep/ADVISORIES.md).

## What the evidence shows

- **Self-tests.** `python -m fpf_thinking_map.verify` (40 checks) and
  `dev_mcp/test_server.py` (45 checks) are written and run by the authors. They
  check that the library does what it is specified to do. They have not been
  audited by a third party.
- **Does it make agents safer?** One small benchmark exists
  ([bench/RESULTS.md](bench/RESULTS.md)): two tasks, one frontier-model class,
  5 runs per condition, 20 runs total. The model made **no policy violations
  with or without** the library, so there is **no measured compliance
  improvement** for a cooperative model on a clearly stated task. With the
  library the model made *more* tool calls (4.4 vs 1.0 and 2.0 vs 1.0), because
  it used the inspection calls before acting. Weaker or adversarial models were
  not tested.
- **ISO.** [docs/ISO_EVIDENCE_PACKET.md](docs/ISO_EVIDENCE_PACKET.md) maps
  release 2.0.1 against ISO/IEC 25010, 27001 and 9001 as a self-assessed
  checklist. It is **not** an audit and **not** a certification.

## Shipped structures

| Concern | Structures | Effect |
| --- | --- | --- |
| Claim / assurance | `ContextSlice`, `ClaimScope`, `FormalityLevel`, `ReliabilityPath` | Typed scope; unknown stays unknown |
| Tool plans | `CallPlanPrimitive`, `BudgetEnvelope` | Incomplete plans → `REVISE_PLAN` |
| Autonomy | `AutonomyBudgetDecl`, `AutonomyLedgerEntry` | Opt-in budget; failure → `ESCALATE` |
| Work attribution | `WorkPrimitive.performed_under` | Wrong holder/context cannot complete |
| Gate join | `GateDecision`, `OutcomeCause` | `ABSTAIN` ≠ `BLOCK` (`cause=gate_block`) |
| Map integrity | `ThinkingMapTraversal.validate_map()` | Dangling refs / unknown IDs fail closed |
| Adjacency (2.0) | `AdjacencyClearanceRule`, `AdjacentlyCleared` | A confirmed-absent percept clears declared neighbours |
| Continuity (2.0.2) | `ActiveState.checkpoint()`, `from_checkpoint()` | Persist and restore a paused traversal |

### Gate join

| Gate result | Meaning | Typical outcome |
| --- | --- | --- |
| `ABSTAIN` (`insufficient`) | Not enough basis to say yes | `COLLECT_EVIDENCE` when evidence is declared |
| `BLOCK` | Declared policy says no for this evaluation | Denied with `cause=GATE_BLOCK` |

`BLOCK` is hard for that evaluation; it is not automatically permanent. Checks
opt into `BLOCK` with `failure_decision=GateDecision.BLOCK`.

## Demo

[Four interactive traces](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)
(evidence recovery, `AWAIT`, `MoveIntent` with authorization, `ABSTAIN` vs
`BLOCK`). They follow behavior covered by the test suite as of v1.9.5; they are
not a recording of a live model run and do not show later features.

## Releases

| Line | Change |
| --- | --- |
| v1.0–v1.5 | Primitives, TTL, bridges, stagnation, stable public boundary |
| v1.6–v1.8 | Human authorization, receipts, `AWAIT` |
| v1.9 / 1.9.5 | Move identity; A.21 gate join (`ABSTAIN` vs `BLOCK`) |
| v1.9.6 | Failed-run revert terminal (XOR + distance bound) |
| v2.0.0 | Adjacency clearance (`ADV-17`) |
| v2.0.1 | Docs and metadata only; runtime identical to 2.0.0 |
| v2.0.2 | Copyright and SPDX notices on every source file (license unchanged); includes traversal checkpoint and restore (`ADV-08`) |
| v2.0.3 | Docs and metadata only; runtime identical to 2.0.2. Removes the upstream-intake advisory (`ADV-16`) and every named reference to the external specification this package was historically informed by; independence disclaimer reworded |
| **v2.1.0** | Docs only; runtime identical to 2.0.3. Fixes a stale doc line claiming checkpoint/restore was unbuilt |

History: [VERSION_TRACKER.md](docs/VERSION_TRACKER.md) · [CHANGELOG.md](CHANGELOG.md) · [Releases](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/releases)

## Integrator notes

| Priority | Advisory | One line |
| --- | --- | --- |
| Sharp | **ADV-03** | `active_context_id` is self-asserted: the harness must own continuity |
| Sharp | **ADV-07** | `RiskAbove` string match is case-sensitive and fails silently |
| Common | **ADV-01** | Stale evidence warns; it does not block unless gated |
| Common | **ADV-10** | `requires_human_authorization` defaults off |
| 2.0 | **ADV-17** | Adjacency clearance is only as sound as your declared biconditional |

MCP test harness: [`dev_mcp/`](dev_mcp/) (`run_scenario`, `get_advisories`, `run_verify`).

## Repository

| Path | Purpose |
| --- | --- |
| [`fpf_thinking_map/`](fpf_thinking_map/) | The runtime (no dependencies) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Control flow |
| [docs/deep/ADVISORIES.md](docs/deep/ADVISORIES.md) | Integrator boundaries |
| [bench/](bench/) | The ablation benchmark and its raw results |
| [SHA256SUMS](SHA256SUMS) | Source file checksums |

## License and ownership

MIT. Copyright (c) 2026 CONSOLIDARE CONTINUUM S.R.L.

Copyrighted build: release **2.0.2**, commit
[`f0a17a543a23cbc8a33071b170a02ccf41fd33b7`](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/commit/f0a17a543a23cbc8a33071b170a02ccf41fd33b7)
(signed tag `v2.0.2`). Every source file in that commit carries the copyright
and SPDX notice.

The MIT license requires
that the copyright notice and license text be kept in copies and substantial
portions of the software; see [LICENSE](LICENSE) and [NOTICE](NOTICE).

This is an independent implementation, out of scope of and not derived from
any third-party framework's document or ontology. It is not affiliated
with, sponsored by, or endorsed by any such project.
