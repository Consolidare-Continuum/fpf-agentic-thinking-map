<p align="center">
  <img src="https://raw.githubusercontent.com/Consolidare-Continuum/fpf-agentic-thinking-map/main/docs/assets/fpf-agentic-thinking-map-header-v20260818.png" alt="FPF Agentic Thinking Map — Agent freedom. Explicit movement rules." width="100%" />
</p>

# FPF Agentic Thinking Map

Deterministic Python runtime for agents that may reason freely but must move
through a workflow lawfully.

Operational state, evidence freshness, transition legality, authorization,
waiting, and move identity live **outside** model prose. The model proposes;
the runtime decides whether the move is valid.

**PyPI:** [`fpf-thinking-map`](https://pypi.org/project/fpf-thinking-map/) · **Current:** **2.0.1**

[![PyPI](https://img.shields.io/pypi/v/fpf-thinking-map?style=flat-square&label=PyPI&color=3775A9)](https://pypi.org/project/fpf-thinking-map/)
[![Python](https://img.shields.io/pypi/pyversions/fpf-thinking-map?style=flat-square&label=Python&color=f0b429)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-ff9f43?style=flat-square)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![Verification](https://img.shields.io/badge/verify-39%2F39-59d18c?style=flat-square)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/fpf_thinking_map/verify.py)
[![Live demo](https://img.shields.io/badge/live-demo-dd8cff?style=flat-square)](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

## Install

Requires **Python ≥ 3.12**. Zero runtime dependencies.

```bash
pip install "fpf-thinking-map==2.0.1"
python -m fpf_thinking_map.verify    # 39/39
python -m fpf_thinking_map.examples
```

Full 2.0 line is on the index: [`2.0.0`](https://pypi.org/project/fpf-thinking-map/2.0.0/), [`2.0.1`](https://pypi.org/project/fpf-thinking-map/2.0.1/) (also [`1.9.6`](https://pypi.org/project/fpf-thinking-map/1.9.6/)).

## What it is

Agents lose workflow rules in long runs. This package moves the non-negotiable
parts into ordinary code:

- current context and state
- evidence presence and TTL freshness
- gates, guards, and lawful transitions
- cross-context bridges
- human authorization (`AuthorizationReceipt`)
- external wait (`PendingInput` / `AWAIT`)
- concrete move identity (`MoveIntent`)
- typed claim scope / pathwise reliability
- tool-call plan closure and autonomy budgets

Not a prompt. A compact **control surface** around reasoning.

## Contract

| Agent / host | This runtime |
| --- | --- |
| Interprets the task | Holds explicit traversal state |
| Generates options | Computes which moves are legal |
| Collects evidence | Checks presence and freshness |
| Proposes a move | Inspects or attempts that move |
| Explains the result | Returns a bounded outcome and trace |
| Requests human input | Enforces the authorization boundary |
| Runs tools and jobs | Never executes, polls, or schedules them |

## Structural controls (shipped)

| Concern | Structures | Effect |
| --- | --- | --- |
| Claim / assurance | `ContextSlice`, `ClaimScope`, `FormalityLevel`, `ReliabilityPath` | Typed scope; unknown stays unknown |
| Tool plans | `CallPlanPrimitive`, `BudgetEnvelope` | Incomplete plans → `REVISE_PLAN` |
| Autonomy | `AutonomyBudgetDecl`, `AutonomyLedgerEntry` | Opt-in budget; fail → `ESCALATE` |
| Work attribution | `WorkPrimitive.performed_under` | Wrong holder/context cannot complete |
| Gate join | `GateDecision`, `OutcomeCause` | `ABSTAIN` ≠ `BLOCK` (`cause=gate_block`) |
| Map integrity | `ThinkingMapTraversal.validate_map()` | Dangling refs / unknown IDs fail closed |
| Adjacency (2.0) | `AdjacencyClearanceRule`, `AdjacentlyCleared` | Confirmed-absent percept clears declared neighbors |

## Demo

[![Four test-backed traces](https://raw.githubusercontent.com/Consolidare-Continuum/fpf-agentic-thinking-map/main/docs/assets/three-runs-preview.png)](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

**[Interactive four-run trace](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)** — evidence recovery, `AWAIT`, `MoveIntent`, authorization, and `ABSTAIN` vs `BLOCK`.

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
```

Replace the deploy vocabulary with your own contexts, roles, evidence, and gates.

## Gate join (keep these apart)

| Gate result | Meaning | Typical outcome |
| --- | --- | --- |
| `ABSTAIN` (`insufficient`) | Not enough basis to say yes | `COLLECT_EVIDENCE` when evidence is declared |
| `BLOCK` | Declared policy says no for this evaluation | Denied with `cause=GATE_BLOCK` |

`BLOCK` is hard for that evaluation; it is not automatically permanent. Checks
opt into `BLOCK` with `failure_decision=GateDecision.BLOCK`.

## Release line

| Line | Capability |
| --- | --- |
| v1.0–v1.5 | Primitives, TTL, bridges, stagnation, stable public boundary |
| v1.6–v1.8 | Human authorization, receipts, `AWAIT` |
| v1.9 / 1.9.5 | Move identity; A.21 gate join (`ABSTAIN` vs `BLOCK`) |
| v1.9.6 | Failed-run revert terminal (XOR + distance bound) |
| **v2.0.0** | Adjacency Clearance (`ADV-17`) |
| **v2.0.1** | Current — docs/metadata/reference hardware; runtime verify **39/39** |

History: [VERSION_TRACKER.md](docs/VERSION_TRACKER.md) · [CHANGELOG.md](CHANGELOG.md) · [Releases](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/releases)

## Integrator notes (read before production)

Deliberate minimal defaults — not defects. Full text: [ADVISORIES.md](docs/deep/ADVISORIES.md).

| Priority | Advisory | One line |
| --- | --- | --- |
| Sharp | **ADV-03** | `active_context_id` is self-asserted — harness must own continuity |
| Sharp | **ADV-07** | `RiskAbove` string match is case-sensitive and fails silent |
| Common | **ADV-01** | Stale evidence warns; it does not block unless gated |
| Common | **ADV-10** | `requires_human_authorization` defaults off |
| 2.0 | **ADV-17** | Adjacency clearance is only as sound as your declared biconditional |

MCP harness: [`dev_mcp/`](dev_mcp/) — `run_scenario`, `get_advisories`, `run_verify`.

## Scope

**Use when you need:** bounded multi-step legality, evidence-aware state,
inspectable block/escalate reasons, human authorization, wait vs idle,
compact LLM state slices.

**Do not use as:** a universal reasoner, vector store, tool runner/scheduler,
or a certificate that an entire agent system is safe.

## Docs

| Path | Purpose |
| --- | --- |
| [`fpf_thinking_map/`](fpf_thinking_map/) | Zero-dependency runtime (PyPI **2.0.1**) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Control flow |
| [docs/deep/ADVISORIES.md](docs/deep/ADVISORIES.md) | Integrator boundaries |
| [SHA256SUMS](SHA256SUMS) | Source fingerprints |

## Product continuation

**CONSOLIDARE CONTINUUM S.R.L.** designs, owns, and ships this runtime for its own products and client work. No third-party framework affiliation. No external attribution required for use of this package.

## ISO evidence

[docs/ISO_EVIDENCE_PACKET.md](docs/ISO_EVIDENCE_PACKET.md) — ISO/IEC 25010 · 27001 · 9001 alignment for **v2.0.1** (**not** certification).

**Agent freedom. Explicit movement rules.**
