<p align="center">
  <img src="https://raw.githubusercontent.com/Consolidare-Continuum/fpf-agentic-thinking-map/main/docs/assets/fpf-agentic-thinking-map-header-v20260818.png" alt="FPF Agentic Thinking Map - Agent freedom. Explicit movement rules." width="100%" />
</p>

# FPF Agentic Thinking Map

A small, deterministic Python runtime for agents that may reason freely but
must move through a workflow lawfully.

It keeps operational state, evidence freshness, transition legality,
authorization boundaries, and waiting conditions outside the model's prose
context. The model can inspect the map and choose; the runtime decides whether
the move is valid.

[![PyPI](https://img.shields.io/pypi/v/fpf-thinking-map?style=flat-square&label=PyPI&color=3775A9)](https://pypi.org/project/fpf-thinking-map/)
[![Downloads (honest)](https://img.shields.io/badge/downloads%20%28honest%29-4.5k-1f6feb?style=flat-square)](https://pypistats.org/packages/fpf-thinking-map)
[![Python](https://img.shields.io/pypi/pyversions/fpf-thinking-map?style=flat-square&label=Python&color=f0b429)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![License](https://img.shields.io/pypi/l/fpf-thinking-map?style=flat-square&label=license&color=57c7bd)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/LICENSE)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-ff9f43?style=flat-square)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/pyproject.toml)
[![Verification](https://img.shields.io/badge/verify-35%2F35-59d18c?style=flat-square)](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/fpf_thinking_map/verify.py)
[![Live demo](https://img.shields.io/badge/live-demo-dd8cff?style=flat-square)](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

```bash
pip install fpf-thinking-map
python -m fpf_thinking_map.verify
```

## Important links

- [ARCHITECTURE.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/ARCHITECTURE.md)
- [VERSION_TRACKER.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md)
- [TRIPLE_TAX_CALCULUS.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/TRIPLE_TAX_CALCULUS.md)
- [REFLECTIONS.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/REFLECTIONS.md)
- [CONTRIBUTING.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/CONTRIBUTING.md)
- [ADVISORIES.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md)
- [`dev_mcp/`](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/tree/main/dev_mcp)

The `dev_mcp` development and compliance harness is genuinely tested against
the package and updated whenever runtime behavior, compliance checks, or
integration requirements change.

## The problem

An agent can explain a workflow rule and still lose track of it during a long
run. Prose instructions compete with task content, earlier decisions, tool
output, and context compression.

FPF Agentic Thinking Map moves the parts that should not depend on narration
into ordinary code:

- current context and state;
- evidence presence and TTL freshness;
- gates, guards, and lawful transitions;
- cross-context bridges;
- human authorization;
- external dependencies and wake conditions;
- concrete move identity and trace lineage;
- typed claim scope and pathwise assurance;
- tool-call plan closure and hard autonomy budgets.

This is not another reasoning prompt. It is a compact control surface around
reasoning.

## Why this works across model sizes

The map clips interpretive slack at both ends. Strong models stop
free-associating past what a constraint actually says; lighter models receive
enough scaffolding that they do not have to infer the workflow's intent from
scratch.

Building a good map still requires real judgment, so new controls should be
designed and challenged with strong models first. Consuming the finished map
does not require the same reasoning capacity. Once a workflow is encoded as
explicit constraints and gates instead of tacit prose, following it correctly
stops depending on frontier-level inference. A lighter model does not have to
understand the workflow deeply; it has to respect the map.

That is what makes the result portable down to smaller models, not merely
across flagship ones: the hard reasoning was front-loaded into the encoding,
once, by the map author.

## The contract

The division of responsibility is deliberate:

| Agent or application | Thinking map runtime |
| --- | --- |
| Interprets the task | Holds explicit traversal state |
| Generates and compares options | Computes which moves are legal |
| Collects evidence | Checks presence and freshness |
| Proposes a concrete move | Inspects or attempts that move |
| Explains the result | Returns a bounded outcome and trace |
| Requests human input | Enforces the authorization boundary |
| Executes tools and jobs | Never executes, polls, or schedules them |

The map constrains movement, not meaning. It does not replace the model,
application logic, retrieval, tools, or a task scheduler.

## Structural agentic controls

| Concern | Runtime structure | Enforced effect |
| --- | --- | --- |
| Claim applicability and assurance | `ContextSlice`, `ClaimScope`, `FormalityLevel`, `ReliabilityPath` | Numeric G is no longer treated as scope; unknown membership stays unknown; R folds pathwise |
| Tool-call planning | `CallPlanPrimitive`, `BudgetEnvelope`, `CheckpointReturn` | Incomplete or mismatched declared tool plans return `REVISE_PLAN` and cannot fire |
| Autonomous enactment | `AutonomyBudgetDecl`, `AutonomyLedgerEntry` | A transition opts in with `requires_autonomy_budget_id`; failed assignment/gate/envelope returns `ESCALATE` and successful burn is recorded |
| Performed-work attribution | `WorkPrimitive.performed_under`, `validate_work_attribution()` | Once a map declares RoleAssignments, a dangling or wrong-holder work record cannot satisfy completion |
| Gate decisions | `GateDecision`, `GateCheck.failure_decision`, `OutcomeCause` | `ABSTAIN` means the gate lacks enough basis to say yes; an explicit `BLOCK` means policy says no for the current evaluation. Traversal preserves the distinction as `cause=gate_block` without breaking the existing outcome enum |
| Map integrity | `ThinkingMapTraversal.validate_map()` | Opt-in preflight fails on dangling gate/rule references; explicit unknown transition IDs return typed `ABSTAIN` |

These are bounded runtime compilations, not a port of the full FPF framework.

## Live runtime visual

[![Four test-backed traces of the traversal runtime](https://raw.githubusercontent.com/Consolidare-Continuum/fpf-agentic-thinking-map/main/docs/assets/three-runs-preview.png)](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)

**[Open the interactive four-run trace](https://consolidare-continuum.github.io/fpf-agentic-thinking-map/demos/three-runs.html)**

The visual follows evidence recovery, `PendingInput`/`AWAIT`, `MoveIntent`,
state-bound authorization, and the v1.9.5 distinction between an undecided
gate (`ABSTAIN`) and an explicit hard denial (`BLOCK`).

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

print(inspection.kind)
print(result.kind)
print(state.current_state)
```

The map is domain-agnostic. Replace the deployment vocabulary with your own
contexts, roles, evidence, gates, and transitions.

Run the packaged scenarios:

```bash
python -m fpf_thinking_map.examples
```

## What is enforced

### Explicit state

The active position is a first-class object, not a conclusion the model must
repeatedly reconstruct from chat history.

### Evidence with age

Transitions can require evidence. Evidence can decay by semantic floor and
TTL, allowing the runtime to distinguish present evidence from usable
evidence.

### Gates, guards, and logic

Gates test declared conditions. Guards enforce hard constraints. A small
propositional layer composes facts without asking the model to reinterpret the
rules on every step.

When a gate cannot return `PASS`, v1.9.5 keeps two different situations apart:

| Gate result | Plain-language meaning | Typical traversal response |
| --- | --- | --- |
| `ABSTAIN` (`"insufficient"`) | The gate does not have enough basis to say yes | `COLLECT_EVIDENCE` when the missing evidence is declared; otherwise a denied outcome |
| `BLOCK` | A check explicitly says no under the current declared policy and state | denied with `cause=OutcomeCause.GATE_BLOCK` |

`BLOCK` is hard for that evaluation, not necessarily permanent. It must not be
downgraded by another check or treated as an invitation to guess, but the gate
may evaluate differently after its declared evidence, state, or policy changes.
Existing checks do not become hard blocks automatically; a check opts in with
`failure_decision=GateDecision.BLOCK`.

### Validated bridges

Cross-context movement is explicit. High-risk substitution without a
sufficient bridge contract is refused or escalated rather than silently
treated as equivalent.

### Human authorization

`requires_human_authorization` separates "structurally legal" from "authorized
to execute."

For stronger integrations, `AuthorizationReceipt` binds approval to:

- one transition;
- the exact inspected state fingerprint;
- an expiry boundary;
- single consumption.

A denied move may expose declared `safe_alternatives`, so escalation does not
have to become a dead end.

### External waiting

`PendingInput` and `AWAIT` distinguish "the workflow is finished" from "the
workflow is alive but waiting for something outside the map." The host owns
polling and resolution.

### Concrete move identity

`MoveIntent` distinguishes a reusable transition type from one particular
proposed move. `inspect_move()` evaluates it without mutation; a successful
transition can stamp move lineage into the trace.

## Why the versions matter

The project has grown by closing specific ambiguities in traversal state, not
by expanding into a general agent framework.

| Release line | Capability added |
| --- | --- |
| v1.0 | Runnable semantic primitives, deterministic guards, lawful traversal |
| v1.2 | Evidence TTL, response contracts, `IDLE` and `BRIDGE` |
| v1.3 | Enforced bridge crossing and lean state slices |
| v1.4 | Stagnation detection, integrator advisories, verified documentation |
| v1.5 | Stable public package boundary |
| v1.6 | Human authorization and safe denial routes |
| v1.7 | State-bound, expiring authorization receipts |
| v1.8 | External dependency tracking and `AWAIT` |
| v1.9 | Concrete move identity, inspection, lineage, authorization-clock fix |
| v1.9.5 "Ground Stop" | Correct A.21 gate join; explicit `BLOCK` versus insufficient `ABSTAIN`; typed denial causes; opt-in structural controls |

The complete reader-facing history is in
[docs/VERSION_TRACKER.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md).
Technical changes are in
[CHANGELOG.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/CHANGELOG.md),
and full release bodies remain in
[GitHub Releases](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/releases).

This separation is intentional: the README describes the stable product; the
tracker records how that product became stronger.

## Evidence, verification, and limits

The repository includes three different kinds of support. They should not be
confused:

- Deterministic verification checks runtime invariants directly.
- Scenario and adversarial tests exercise integration behavior and known
  failure shapes.
- Model experiments show behavior under stated conditions; they are evidence,
  not universal guarantees.

```bash
python -m fpf_thinking_map.verify
python -m fpf_thinking_map.examples
```

The 1.9.5 gate distinction was also replayed through `dev_mcp` with the same
missing `release_permit` under two policies:

```text
default check       -> gate: insufficient -> outcome: collect_evidence
explicit BLOCK      -> gate: block        -> outcome: denied (cause: gate_block)
permit present      -> gate: pass         -> outcome: continue
```

That is the release contract in one view: uncertainty requests a resolution
path; a declared hard denial stops the move and remains identifiable to the
caller.

The compiled state slice was also measured against injecting the corresponding
raw FPF sections at five shipped decision points. The measured slice was much
smaller, but this is a traversal-context result, not a claim about general
intelligence or total application cost. Method and limitations:
[TRIPLE_TAX_CALCULUS.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/TRIPLE_TAX_CALCULUS.md).

For the authorization experiments, threat boundaries, failures found, and
claims deliberately not made, see
[IGNITION_LOCK_WIND_TUNNEL.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/IGNITION_LOCK_WIND_TUNNEL.md).

## Scope

Use this library when you need:

- bounded multi-step traversal;
- explicit next-move legality;
- evidence-aware workflow state;
- inspectable reasons for blocking or escalation;
- human authorization for selected transitions;
- a clean distinction between waiting, resting, and acting;
- compact state projections for an LLM or agent host.

Do not use it as:

- a universal reasoning engine;
- a semantic ingestion system for all of FPF;
- an embeddings or vector database;
- a tool runner, queue, scheduler, or worker supervisor;
- a substitute for application-specific policy;
- a certification that an entire agent system is safe.

Correct map authoring and correct host integration remain part of the trust
boundary. Known sharp edges and deliberate non-goals are recorded in
[ADVISORIES.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md).

## Repository guide

| Path | Purpose |
| --- | --- |
| [`fpf_thinking_map/`](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/tree/main/fpf_thinking_map) | Zero-dependency runtime published to PyPI |
| [`dev_mcp/`](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/tree/main/dev_mcp) | Separate development and compliance-testing harness |
| [ARCHITECTURE.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/ARCHITECTURE.md) | Verified control flow and module architecture |
| [docs/VERSION_TRACKER.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/VERSION_TRACKER.md) | Every release, with three practical consequences |
| [docs/DECISIONS_REJECTIONS_ADOPTIONS.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/DECISIONS_REJECTIONS_ADOPTIONS.md) | Design provenance and rejected scope |
| [docs/deep/ADVISORIES.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/ADVISORIES.md) | Integration boundaries and known sharp edges |
| [SHA256SUMS](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/SHA256SUMS) | Repository-wide source fingerprints |

## Design rules

1. Keep the model free to generate and compare.
2. Keep movement legality explicit and deterministic.
3. Add structure only when it changes observable behavior.
4. Keep each decision payload small.
5. Keep host responsibilities outside the core.
6. Record rejected ideas as carefully as adopted ones.
7. Prefer a narrow mechanism with inspectable limits over a broad claim.

## Relationship to FPF

This project is inspired by [ailev/FPF](https://github.com/ailev/FPF) by
Anatoly Levenchuk. It is an independent, MIT-licensed implementation with its
own runtime scope.

FPF provides the broad conceptual frame. This package compiles a selected part
of that frame into a practical traversal runtime. It may omit or reject
patterns that do not improve this package's observable agent behavior.

See [NOTICE](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/NOTICE)
and [SOURCES.md](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/docs/deep/SOURCES.md)
for attribution and scope boundaries.

## License and contact

MIT License. See
[LICENSE](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/blob/main/LICENSE).

Maintained by [igareosh.com](https://igareosh.com) ·
[@igareosh](https://github.com/igareosh) ·
[igareosh@igareosh.com](mailto:igareosh@igareosh.com)

**Agent freedom. Explicit movement rules.**
