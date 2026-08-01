"""Compiled FPF semantic primitives.

These are the "circuit board components" — the pre-shaped semantic field
extracted from FPF spec patterns. Each primitive maps to one or more
FPF spec sections and carries the structural semantics the LLM navigates.

Not a 1:1 copy of FPF. A compiled distillation: enough structure to
constrain reasoning, enough openness for the LLM to interpret.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fpf_thinking_map.agentic_structure import (
    ClaimScope,
    ContextSlice,
    FormalityLevel,
    ReliabilityPath,
)

# ---------------------------------------------------------------------------
# Product-native runtime frame (not an upstream U-kind)
# ---------------------------------------------------------------------------

@dataclass
class ContextPrimitive:
    """Product-native frame for partitioning traversal state.

    It is not FPF U.BoundedContext or BoundedModelUseStructure. context_id
    references express runtime scoping only — not containment, parthood,
    model applicability, or upstream boundary identity.
    """
    context_id: str
    label: str
    glossary: dict[str, str] = field(default_factory=dict)
    invariants: list[str] = field(default_factory=list)
    bridges_to: list[ContextBridge] = field(default_factory=list)

    def term_defined(self, term: str) -> bool:
        return term in self.glossary

    def resolve_term(self, term: str) -> str | None:
        return self.glossary.get(term)


@dataclass
class ContextBridge:
    """Product-native routing and translation record between runtime frames.

    Presence does not establish an upstream F.9 relation, a boundary, or
    permission to rely on a translation.
    """
    target_context_id: str
    mapping: dict[str, str] = field(default_factory=dict)
    translation_loss: str = ""
    substitution_license: bool = False


# ---------------------------------------------------------------------------
# A.2 — Role Taxonomy + A.2.1 U.RoleAssignment + A.13 Agency Spectrum
# ---------------------------------------------------------------------------

class AgencyLevel(Enum):
    """FPF A.13: agency is a spectrum, not binary."""
    PASSIVE = "passive"
    REACTIVE = "reactive"
    AUTONOMOUS = "autonomous"
    DELIBERATIVE = "deliberative"


@dataclass
class RolePrimitive:
    """A role assignment within a bounded context.

    FPF A.2: Role ≠ Method ≠ Work (A.7 strict distinction).
    A role is an assignment/mask, not an identity. The same holder
    can have multiple roles in different contexts.

    FPF A.2.7: roles have algebra — specialization (≤),
    incompatibility (⊥), bundles (⊗).
    """
    role_id: str
    label: str
    context_id: str
    agency_level: AgencyLevel = AgencyLevel.REACTIVE
    responsibilities: list[str] = field(default_factory=list)
    incompatible_with: list[str] = field(default_factory=list)
    specializes: str | None = None
    required_evidence_roles: list[str] = field(default_factory=list)

    def conflicts_with(self, other_role_id: str) -> bool:
        return other_role_id in self.incompatible_with


# ---------------------------------------------------------------------------
# A.2.1 — U.RoleAssignment: Contextual Role Assignment
# ---------------------------------------------------------------------------

@dataclass
class RoleAssignment:
    """A binding of a holder to a role inside a bounded context.

    FPF A.2.1: assignment is distinct from role definition and from
    role enactment (work done under the assignment).
    The assignment can have a validity window — expired assignments
    should not authorize new work.
    """
    assignment_id: str
    holder_id: str
    role_id: str
    context_id: str
    valid_from: str = ""
    valid_until: str = ""
    expired: bool = False


# ---------------------------------------------------------------------------
# A.15, A.15.1, A.15.2 — Work & WorkPlan
# ---------------------------------------------------------------------------

@dataclass
class WorkPrimitive:
    """A record of occurrence (enactment).

    FPF A.15.1 (U.Work): the record of what actually happened.
    Work is execution/occurrence, distinct from Role, Method, and Plan.
    A plan does NOT constitute having done the work.
    """
    work_id: str
    label: str
    context_id: str
    method_id: str | None = None
    performed_under: str | None = None
    performed_by: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class WorkPlanPrimitive:
    """A schedule of intent — NOT a record of work done.

    FPF A.15.2 (U.WorkPlan): what is intended to happen.
    Distinct type from WorkPrimitive — the type IS the distinction.
    A plan existing does not mean the work was executed.
    """
    plan_id: str
    label: str
    context_id: str
    method_id: str | None = None
    intended_role_id: str | None = None
    planned_evidence: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# A.2.9 — U.SpeechAct: Communicative Work Object
# ---------------------------------------------------------------------------

class SpeechActType(Enum):
    """What the speech act does."""
    APPROVE = "approve"
    AUTHORIZE = "authorize"
    REVOKE = "revoke"
    PUBLISH = "publish"
    REQUEST = "request"


@dataclass
class SpeechActPrimitive:
    """A communicative work occurrence — approval, authorization, revocation.

    FPF A.2.9: a U.Work whose primary effect is communicative.
    The act can institute, update, or revoke commitments, role assignments,
    and statuses by reference.

    Agentic behavior change: "owner_approval" stops being a magic string
    evidence ID. It becomes a speech act with: who approved, when, what it
    institutes, whether it's still valid. Guards can check these.
    """
    act_id: str
    act_type: SpeechActType
    actor_id: str
    context_id: str
    performed_under: str | None = None
    addressed_to: str = ""
    institutes: list[str] = field(default_factory=list)
    revokes: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    expired: bool = False


# ---------------------------------------------------------------------------
# A.2.8 — U.Commitment: Deontic Commitment Object
# ---------------------------------------------------------------------------

class DeonticModality(Enum):
    """RFC 2119 / BCP-14 aligned normative force.

    MAY means non-binding allowance in the normative statement. It is not a
    strong permission grant, proof of non-prohibition, or authorization to
    enact a transition. Those remain separate relations and gates.
    """
    MUST = "must"
    SHOULD = "should"
    MAY = "may"
    MUST_NOT = "must_not"
    SHOULD_NOT = "should_not"


@dataclass
class CommitmentPrimitive:
    """A deontic commitment — obligation or prohibition.

    FPF A.2.8: commitments are scoped, have validity windows,
    require evidence refs, and have adjudication hooks.
    Separate from admissibility gates (those are structural,
    commitments are deontic).

    DeonticModality.MAY is retained for RFC-style source compatibility but
    never institutes A.2.8.PER granted permission and carries no execution
    authority in this runtime.
    """
    commitment_id: str
    label: str
    modality: DeonticModality
    context_id: str
    subject: str = ""
    scope: str = ""
    validity_window: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    adjudication_hook: str | None = None

    @property
    def is_binding(self) -> bool:
        return self.modality in (DeonticModality.MUST, DeonticModality.MUST_NOT)


# ---------------------------------------------------------------------------
# A.21 — GateProfilization: OperationalGate
# ---------------------------------------------------------------------------

class GateDecision(Enum):
    """Gate outcome lattice — FPF A.21: abstain ≤ pass ≤ degrade ≤ block.

    ABSTAIN = neutral/inactive or insufficient evidence (usually resolvable)
    PASS    = all checks satisfied
    DEGRADE = partial checks satisfied (proceed with caution)
    BLOCK   = hard denial (cannot proceed regardless of evidence)
    """
    ABSTAIN = "insufficient"
    PASS = "pass"
    DEGRADE = "partial"
    BLOCK = "block"

    @property
    def lattice_rank(self) -> int:
        """A.21 join order: abstain <= pass <= degrade <= block."""
        return {
            GateDecision.ABSTAIN: 0,
            GateDecision.PASS: 1,
            GateDecision.DEGRADE: 2,
            GateDecision.BLOCK: 3,
        }[self]


@dataclass
class GateCheck:
    """A single check within a gate profile.

    ``failure_decision`` is an opt-in policy for a check whose required
    evidence is not complete. Existing checks retain the legacy split:
    partial evidence degrades and wholly absent evidence abstains. A
    safety-critical check can now declare ``GateDecision.BLOCK`` without
    changing the behavior of any pre-existing check.
    """
    check_id: str
    description: str
    required_evidence: list[str] = field(default_factory=list)
    failure_decision: GateDecision | None = None

    def __post_init__(self) -> None:
        if self.failure_decision == GateDecision.PASS:
            raise ValueError("failure_decision cannot be PASS when evidence is missing")

    def evaluate(self, available_evidence: set[str]) -> GateDecision:
        missing = set(self.required_evidence) - available_evidence
        if not missing:
            return GateDecision.PASS
        if self.failure_decision is not None:
            return self.failure_decision
        if len(missing) < len(self.required_evidence):
            return GateDecision.DEGRADE
        return GateDecision.ABSTAIN


@dataclass
class GatePrimitive:
    """An operational gate that aggregates checks into a decision.

    FPF A.21: gates aggregate GateChecks via join-semilattice.
    Gate ≠ commitment (structural vs deontic).
    Gates are the deterministic validation layer before action.
    """
    gate_id: str
    label: str
    context_id: str
    checks: list[GateCheck] = field(default_factory=list)
    fail_closed: bool = True

    def evaluate(self, available_evidence: set[str]) -> GateDecision:
        if not self.checks:
            return GateDecision.ABSTAIN if self.fail_closed else GateDecision.PASS

        decisions = [c.evaluate(available_evidence) for c in self.checks]
        return max(decisions, key=lambda decision: decision.lattice_rank)

    def missing_evidence(self, available_evidence: set[str]) -> list[str]:
        """Return only the evidence this gate is missing."""
        missing: set[str] = set()
        for c in self.checks:
            missing.update(set(c.required_evidence) - available_evidence)
        return sorted(missing)


# ---------------------------------------------------------------------------
# Semantic Floor — vertical amplification levels from FPF spec layering
# ---------------------------------------------------------------------------

class SemanticFloor(Enum):
    """Vertical amplification levels — where the hop counter stops.

    Derived from FPF spec section layering. Each floor has a base TTL.
    Lower floors = foundational/stable. Higher floors = operational/ephemeral.

    Floor 0 STRUCTURAL: A.1.1, A.2, A.3.3, A.6.9, A.21 defs — the building itself
    Floor 1 BINDING:    A.2.1, A.2.8, A.15.2 — session-stable, can expire
    Floor 2 EVIDENTIARY: A.10, B.3, B.3.4 — decays with FGR: max(1, round(F*R*8))
    Floor 3 OPERATIONAL: A.2.9, A.15.1, A.21 eval — per-step ephemeral
    Floor 4 PUBLICATION: E.17 — inherited from source freshness
    """
    STRUCTURAL = 0
    BINDING = 1
    EVIDENTIARY = 2
    OPERATIONAL = 3
    PUBLICATION = 4


FLOOR_BASE_TTL: dict[SemanticFloor, int | None] = {
    SemanticFloor.STRUCTURAL: None,
    SemanticFloor.BINDING: 10,
    SemanticFloor.EVIDENTIARY: 8,
    SemanticFloor.OPERATIONAL: 2,
    SemanticFloor.PUBLICATION: None,
}


# ---------------------------------------------------------------------------
# A.10 — Evidence Graph + A.2.4 EvidenceRole + B.3 F-G-R
# ---------------------------------------------------------------------------

class Freshness(Enum):
    """Evidence freshness — CURRENT decays to STALE then EXPIRED via TTL."""
    CURRENT = "current"
    STALE = "stale"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass
class FGR:
    """Typed assurance tuple with detectable legacy scalar compatibility.

    Current shape:
      F = C.2.3 ordinal FormalityLevel
      G = A.2.6 set-valued ClaimScope
      R = C.2.2 pathwise effective reliability

    Earlier releases accepted three floats. Numeric F/G remain readable so
    stored maps do not crash, but `is_structurally_typed` is False and the
    development MCP reports that form as drift. New maps should use the typed
    objects; numeric G is never interpreted as a scope set.
    """
    formality: FormalityLevel | float = FormalityLevel.F0
    scope: ClaimScope | float | None = None
    reliability: float = 0.0
    reliability_paths: list[ReliabilityPath] = field(default_factory=list)

    @property
    def formality_ratio(self) -> float:
        if isinstance(self.formality, FormalityLevel):
            return self.formality.normalized
        return min(1.0, max(0.0, float(self.formality)))

    @property
    def effective_reliability(self) -> float:
        if not self.reliability_paths:
            return min(1.0, max(0.0, self.reliability))
        values = [path.effective_reliability for path in self.reliability_paths]
        if len(values) > 1 and not all(
            path.independence_basis_ref for path in self.reliability_paths
        ):
            return min(values)
        return max(values)

    @property
    def is_structurally_typed(self) -> bool:
        return isinstance(self.formality, FormalityLevel) and isinstance(self.scope, ClaimScope)

    def sufficient(self, min_f: float = 0.0, min_r: float = 0.0) -> bool:
        return self.formality_ratio >= min_f and self.effective_reliability >= min_r


@dataclass
class EvidencePrimitive:
    """An evidence record with provenance and trust assessment.

    FPF A.10: claims must be supported by evidence with traceability.
    FPF B.3: trust is computed as F-G-R tuple, not a feeling.
    FPF B.3.4: evidence decays — freshness matters.

    TTL resolution order:
    1. Explicit ttl_steps (if set) — always wins
    2. semantic_floor + FGR → computed_ttl (auto-derived)
    3. None — no decay
    """
    evidence_id: str
    label: str
    context_id: str
    claim: str = ""
    source: str = ""
    fgr: FGR = field(default_factory=FGR)
    freshness: Freshness = Freshness.UNKNOWN
    ttl_steps: int | None = None
    semantic_floor: SemanticFloor | None = None
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)

    @property
    def computed_ttl(self) -> int | None:
        """Auto-derive TTL from semantic floor + FGR trust factors.

        Explicit ttl_steps always wins. Otherwise:
        EVIDENTIARY floor: max(1, round(F × R × 8))
        Other floors: base TTL from FLOOR_BASE_TTL
        None floor: no decay
        """
        if self.ttl_steps is not None:
            return self.ttl_steps
        if self.semantic_floor is None:
            return None
        base = FLOOR_BASE_TTL.get(self.semantic_floor)
        if base is None:
            return None
        if self.semantic_floor == SemanticFloor.EVIDENTIARY:
            trust_factor = self.fgr.formality_ratio * self.fgr.effective_reliability
            return max(1, round(trust_factor * base))
        return base


# ---------------------------------------------------------------------------
# A.3.3 U.Dynamics + B.4 Canonical Evolution Loop
# ---------------------------------------------------------------------------

@dataclass
class TransitionPrimitive:
    """A state transition in the semantic map.

    FPF A.3.3 (U.Dynamics): state evolution as law of change.
    FPF B.4: canonical evolution loop (Run-Observe-Refine-Deploy).
    FPF A.2.5 (U.RoleStateGraph): roles have state machines.

    Transitions connect states. Guards on transitions are evaluated
    before the transition fires.

    requires_human_authorization: "Ignition Lock" — the HITL gate for
    destructive/irreversible moves. FPF legality (evidence fresh, gate
    satisfied) doesn't know a delete from a deploy — both get CONTINUE
    on their own merits. requires_human_authorization=True is how a
    transition opts into "legal is not the same as fireable": the model
    still sees it (step()/slice() report it, evidence and gate status
    included), it just cannot invoke it — only a caller passing
    authorized=True can, checked in ActiveState.transition_to() so there
    is no lower-level call that skips it. That authorized flag must come
    from a channel the agent's own tool-calling loop can't reach — see
    README "Ignition Lock — human-in-the-loop for destructive moves" for
    how to wire it, and docs/deep/ADOPTED_IGNITION_LOCK.md for why this
    is a general "needs a second party's say-so" primitive, not a
    destructive-actions-only feature.

    safe_alternatives: "Abort to Orbit" — other transition_ids this one
    names as its non-destructive twins — e.g. an archive/soft-delete
    instead of a hard delete. Explicit and declared, never inferred: two
    transitions merely sharing a from_state are not assumed to be
    substitutes for each other. Surfaced in slice() before the model ever
    attempts this transition, and folded into the ESCALATE Outcome if it
    does — the engine only makes the
    option visible, it never picks one. Whether an alternative actually
    satisfies the goal is a domain judgment outside this library's scope.

    guard_expression: names a DecisionRule (fpf_thinking_map.logic) that
    must currently recommend *this* transition_id for the fire to
    proceed unopposed — the routing-policy counterpart to
    required_gate_id/required_evidence. Checked in
    ThinkingMapTraversal.attempt_transition(), not by the guard engine
    despite the name (guards.py stays pure ActiveState predicates; a
    LogicLayer reference only ThinkingMapTraversal can resolve doesn't
    belong there).

    Deliberately not an ESCALATE: a routing-policy mismatch is not
    "needs a human," it's "the map disagrees with the proposed move and
    knows what it would prefer instead" — the same shape as
    COLLECT_EVIDENCE, not requires_human_authorization. Fires
    REVISE_PLAN (declared in OutcomeKind since the traversal engine's
    outcome space was first drawn up, never previously returned by any
    code path) with the rule's actual current recommendation in
    Outcome.alternatives, so an agentic caller can retry the recommended
    transition_id in the same turn — solution-seeking stays inside the
    map's own vocabulary, no external tool, no waiting on a person.

    For compatibility, runtime remains a silent no-op when no logic_layer is
    bound or the named rule does not exist. New integrations should call
    `ThinkingMapTraversal.validate_map()` after assembly; that opt-in preflight
    fails closed on dangling `guard_expression` and `required_gate_id`
    references before runtime. A valid rule with no active recommendation
    (condition false with no
    action_if_false, or a HINT/WARN rule's vacuous-implication
    suppression) — "the policy has no opinion right now" defaults to
    allow, same as not setting guard_expression at all. Only an active
    recommendation for a *different* transition_id blocks.
    """
    transition_id: str
    label: str
    context_id: str
    from_state: str
    to_state: str
    required_gate_id: str | None = None
    required_evidence: list[str] = field(default_factory=list)
    readiness_refs: list[str] = field(default_factory=list)
    guard_expression: str = ""
    requires_human_authorization: bool = False
    safe_alternatives: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    call_plan_id: str | None = None
    requires_autonomy_budget_id: str | None = None
    action_token_cost: int = 0
    decision_token_cost: int = 0
    resource_costs: dict[str, float] = field(default_factory=dict)
    scope_target: ContextSlice | None = None


# ---------------------------------------------------------------------------
# E.17 MVPK — Multi-View Publication
# ---------------------------------------------------------------------------

class PublicationFace(Enum):
    """MVPK faces — same content, different audiences."""
    PLAIN = "plain"
    TECHNICAL = "technical"
    INTEROP = "interop"
    ASSURANCE = "assurance"


@dataclass
class PublicationPrimitive:
    """A publication surface for making results visible.

    FPF E.17 (MVPK): consistent views from the same underlying model.
    Publication faces do not add new semantics — they are views.
    Out of the default step path — only consulted for publish moves.
    """
    publication_id: str
    label: str
    context_id: str
    face: PublicationFace = PublicationFace.TECHNICAL
    audience: str = ""
    source_work_ids: list[str] = field(default_factory=list)
    required_gate_id: str | None = None
