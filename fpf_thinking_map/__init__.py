"""FPF Thinking Map — compiled semantic substrate for agentic traversal.

A structured board for LLM reasoning: the model navigates a pre-shaped
semantic field with deterministic guards and propositional logic constraints.
Evidence decays via TTL hop counter. The model reads small JSON slices and
picks moves — no re-reasoning about state the code already computed.

Modules:
  primitives    — core runtime objects + 5 product semantic floors
  state         — runtime binding, active state, TTL tracking, per-move slices
  guards        — 12 deterministic guards (hard constraints, not LLM judgments)
  logic         — 6 propositional operators + freshness-aware decision rules
  traversal     — step engine with 11 lawful outcomes
  authorization — receipts scoping a human's yes to one transition + one state
  pending_input — declared external dependencies distinguishing AWAIT from IDLE
  move_intent   — a concrete proposed move, distinct from its transition type
  agentic_structure — typed scope/assurance, call plans, autonomy budgets
  examples      — deploy decision scenarios demonstrating the full system
  reachability  — discrete reachability analysis over a map's transition graph
  verify        — self-verification harness
"""

# --- Primitives: the semantic field ---
from fpf_thinking_map.agentic_structure import (
    AutonomyBudgetDecl,
    AutonomyLedgerEntry,
    BudgetEnvelope,
    CallPlanPrimitive,
    CheckpointReturn,
    ClaimScope,
    ContextSlice,
    FormalityLevel,
    MembershipJudgment,
    ReliabilityPath,
)

# --- Authorization: receipts scoping approval to one transition + one state ---
from fpf_thinking_map.authorization import (
    AuthorizationReceipt,
    compute_state_fingerprint,
    issue_authorization_receipt,
)

# --- Guards: deterministic hard constraints ---
from fpf_thinking_map.guards import (
    Guard,
    GuardEngine,
    GuardResult,
    GuardScope,
    GuardVerdict,
)

# --- Logic: propositional decision glue ---
from fpf_thinking_map.logic import (
    CommitmentMet,
    CustomProp,
    DecisionRule,
    EvidenceFresh,
    EvidencePresent,
    GateAbstained,
    GateBlocked,
    GatePasses,
    HasMissingEvidence,
    InState,
    LogicLayer,
    Prop,
    RiskAbove,
    RoleActive,
    RuleKind,
    TransitionAvailable,
)

# --- Move intent: concrete proposed move, distinct from transition type ---
from fpf_thinking_map.move_intent import MoveIntent

# --- Pending input: declared external dependencies, AWAIT vs IDLE ---
from fpf_thinking_map.pending_input import PendingInput, PendingInputStatus
from fpf_thinking_map.primitives import (
    FGR,
    FLOOR_BASE_TTL,
    AgencyLevel,
    CommitmentPrimitive,
    ContextBridge,
    ContextPrimitive,
    DeonticModality,
    EvidencePrimitive,
    Freshness,
    GateCheck,
    GateDecision,
    GatePrimitive,
    PublicationFace,
    PublicationPrimitive,
    RoleAssignment,
    RolePrimitive,
    SemanticFloor,
    SpeechActPrimitive,
    SpeechActType,
    TransitionPrimitive,
    WorkPlanPrimitive,
    WorkPrimitive,
)

# --- Reachability: discrete reachability analysis over the transition graph ---
from fpf_thinking_map.reachability import (
    forward_reachable,
    graph_roots,
    unreachable_transitions,
)

# --- State: binding + active state + slicing ---
from fpf_thinking_map.state import (
    ActiveState,
    MoveTrace,
    RuntimeBinding,
    SemanticMap,
)

# --- Traversal: the step engine ---
from fpf_thinking_map.traversal import (
    MapValidationError,
    Outcome,
    OutcomeCause,
    OutcomeKind,
    ThinkingMapTraversal,
)
