"""Agentic structures whose semantics must remain explicit at runtime.

This module is deliberately smaller than the upstream patterns it responds to.
It compiles only the parts that change lawful agent traversal:

* A.2.6 + C.2.2/C.2.3: exact set-valued claim scope, ordinal formality,
  and pathwise reliability;
* C.24: call-plan closure before budgeted tool enactment;
* E.16: named autonomy budgets and a work-facing consumption ledger.

The classes are runtime frames, not claims that this package implements every
upstream authoring, publication, or governance object in those patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from types import MappingProxyType
from typing import Any, Mapping


class MembershipJudgment(Enum):
    """Result of evaluating a bivalent scope-membership predicate.

    UNKNOWN means the interpretation basis is unavailable; it is not a third
    world-side truth value and must never be coerced to False.
    """

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ContextSlice:
    """One exact selector tuple under one effective reference scheme."""

    reference_scheme: str
    selector_schema: tuple[str, ...]
    selectors: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.reference_scheme:
            raise ValueError("ContextSlice requires an effective reference scheme")
        expected = set(self.selector_schema)
        actual = set(self.selectors)
        if expected != actual:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(
                f"ContextSlice selectors must exactly match schema; "
                f"missing={missing}, extra={extra}"
            )
        object.__setattr__(self, "selectors", MappingProxyType(dict(self.selectors)))

    def same_value_as(self, other: "ContextSlice") -> bool:
        return (
            self.reference_scheme == other.reference_scheme
            and self.selector_schema == other.selector_schema
            and self.selectors == other.selectors
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_scheme": self.reference_scheme,
            "selector_schema": list(self.selector_schema),
            "selectors": dict(self.selectors),
        }


@dataclass
class ClaimScope:
    """A.2.6 set-valued claim scope over exact ContextSlice values."""

    scope_id: str
    extension: list[ContextSlice] = field(default_factory=list)
    interpretation_basis_ref: str = ""
    support_basis_refs: list[str] = field(default_factory=list)

    def contains(self, target: ContextSlice) -> bool:
        return any(item.same_value_as(target) for item in self.extension)

    def evaluate_membership(
        self,
        target: ContextSlice,
        *,
        interpretation_available: bool = True,
    ) -> MembershipJudgment:
        if not interpretation_available or not self.interpretation_basis_ref:
            return MembershipJudgment.UNKNOWN
        return MembershipJudgment.TRUE if self.contains(target) else MembershipJudgment.FALSE

    def subset_of(self, other: "ClaimScope") -> bool:
        return all(other.contains(item) for item in self.extension)

    def intersection(self, other: "ClaimScope", scope_id: str) -> "ClaimScope":
        return ClaimScope(
            scope_id=scope_id,
            extension=[item for item in self.extension if other.contains(item)],
            interpretation_basis_ref=(
                self.interpretation_basis_ref
                if self.interpretation_basis_ref == other.interpretation_basis_ref
                else ""
            ),
            support_basis_refs=list(dict.fromkeys(
                self.support_basis_refs + other.support_basis_refs
            )),
        )

    @classmethod
    def span_union(
        cls,
        scopes: list["ClaimScope"],
        scope_id: str,
        *,
        independence_basis_ref: str,
    ) -> "ClaimScope":
        if len(scopes) < 2:
            raise ValueError("SpanUnion requires at least two exact scopes")
        if not independence_basis_ref:
            raise ValueError("SpanUnion requires an explicit independence basis")
        extension: list[ContextSlice] = []
        for scope in scopes:
            for item in scope.extension:
                if not any(existing.same_value_as(item) for existing in extension):
                    extension.append(item)
        basis_refs = {scope.interpretation_basis_ref for scope in scopes}
        basis_ref = basis_refs.pop() if len(basis_refs) == 1 else ""
        return cls(
            scope_id,
            extension,
            basis_ref,
            list(dict.fromkeys(
                [ref for scope in scopes for ref in scope.support_basis_refs]
                + [independence_basis_ref]
            )),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_id": self.scope_id,
            "extension": [item.to_dict() for item in self.extension],
            "interpretation_basis_ref": self.interpretation_basis_ref,
            "support_basis_refs": list(self.support_basis_refs),
        }


class FormalityLevel(IntEnum):
    """C.2.3's ordinal F0...F9 anchor family."""

    F0 = 0
    F1 = 1
    F2 = 2
    F3 = 3
    F4 = 4
    F5 = 5
    F6 = 6
    F7 = 7
    F8 = 8
    F9 = 9

    @property
    def normalized(self) -> float:
        return int(self) / 9


@dataclass
class ReliabilityPath:
    """One C.2.2 justification path with weakest-link and loss penalties."""

    path_id: str
    spine_reliabilities: list[float]
    congruence_penalties: list[float] = field(default_factory=list)
    independence_basis_ref: str = ""

    def __post_init__(self) -> None:
        if not self.spine_reliabilities:
            raise ValueError("ReliabilityPath requires at least one spine value")
        if any(value < 0 or value > 1 for value in self.spine_reliabilities):
            raise ValueError("Reliability spine values must be within [0,1]")
        if any(value < 0 for value in self.congruence_penalties):
            raise ValueError("Congruence penalties cannot be negative")

    @property
    def effective_reliability(self) -> float:
        return max(0.0, min(1.0, min(self.spine_reliabilities) - sum(self.congruence_penalties)))


@dataclass
class BudgetEnvelope:
    """C.24 ex-ante ceilings; actual burn belongs to Work/ledger records."""

    time_limit: float | None = None
    compute_limit: float | None = None
    cost_limit: float | None = None
    risk_ceiling: str = ""
    units: dict[str, str] = field(default_factory=dict)

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("time_limit", self.time_limit),
            ("compute_limit", self.compute_limit),
            ("cost_limit", self.cost_limit),
        ):
            if value is None or value < 0:
                errors.append(f"{name} is not declared as a non-negative ceiling")
        if not self.risk_ceiling:
            errors.append("risk_ceiling is not declared")
        return errors


@dataclass
class CallPlanPrimitive:
    """C.24 enactment-facing tool-call plan, still distinct from Work."""

    plan_id: str
    objective: str
    context_id: str
    route_refs_in_order: list[str]
    budget: BudgetEnvelope
    stop_conditions: list[str] = field(default_factory=list)
    replan_conditions: list[str] = field(default_factory=list)
    next_planned_transition_id: str = ""
    policy_ref: str = ""
    choice_result_ref: str = ""

    def validation_errors(self) -> list[str]:
        errors = self.budget.validation_errors()
        if not self.objective:
            errors.append("objective is missing")
        if not self.route_refs_in_order:
            errors.append("route_refs_in_order is empty")
        if not self.stop_conditions and not self.replan_conditions:
            errors.append("no stop or replan condition is declared")
        if not self.next_planned_transition_id:
            errors.append("next_planned_transition_id is missing")
        if not self.choice_result_ref:
            errors.append("choice_result_ref is missing; planning may still be upstream choice")
        return errors

    @property
    def complete(self) -> bool:
        return not self.validation_errors()


@dataclass
class CheckpointReturn:
    """C.24 bounded probe result; a positive probe is not committed rollout."""

    checkpoint_id: str
    objective: str
    tested_routes: list[str]
    evidence_refs: list[str]
    burned_budget: dict[str, float]
    residual_budget: dict[str, float]
    recommended_next_action: str
    commit_trigger: str

    @property
    def complete(self) -> bool:
        return bool(
            self.objective
            and self.tested_routes
            and self.recommended_next_action
            and self.commit_trigger
        )


@dataclass
class AutonomyBudgetDecl:
    """E.16 named autonomy envelope used as a hard enactment gate."""

    budget_id: str
    version: str
    context_id: str
    scope: ClaimScope
    consumer_role_id: str
    action_limit: int | None = None
    decision_limit: int | None = None
    risk_ceiling: str = "normal"
    resource_caps: dict[str, float] = field(default_factory=dict)
    admissibility_gate_id: str = ""
    override_protocol_ref: str = ""
    override_role_ids: list[str] = field(default_factory=list)

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.version:
            errors.append("version is missing")
        if not self.scope.scope_id:
            errors.append("scope is missing")
        if not self.consumer_role_id:
            errors.append("consumer_role_id is missing")
        if self.action_limit is None and self.decision_limit is None and not self.resource_caps:
            errors.append("no action, decision, or resource cap is declared")
        if self.action_limit is not None and self.action_limit < 0:
            errors.append("action_limit cannot be negative")
        if self.decision_limit is not None and self.decision_limit < 0:
            errors.append("decision_limit cannot be negative")
        if not self.admissibility_gate_id:
            errors.append("admissibility_gate_id is missing")
        if not self.override_protocol_ref:
            errors.append("override_protocol_ref is missing")
        if self.consumer_role_id in self.override_role_ids:
            errors.append("consumer role cannot also be an override role")
        return errors


@dataclass(frozen=True)
class AutonomyLedgerEntry:
    """One immutable record of autonomy-budget consumption by an enacted move."""

    move_ref: str
    transition_id: str
    performed_under_assignment_id: str
    budget_id: str
    budget_version: str
    action_delta: int = 0
    decision_delta: int = 0
    resource_deltas: Mapping[str, float] = field(default_factory=dict)
    guard_verdicts: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "resource_deltas", MappingProxyType(dict(self.resource_deltas))
        )
        object.__setattr__(
            self, "guard_verdicts", MappingProxyType(dict(self.guard_verdicts))
        )
