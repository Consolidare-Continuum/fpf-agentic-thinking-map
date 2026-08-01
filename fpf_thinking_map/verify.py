#!/usr/bin/env python3
"""Self-verification harness for the FPF thinking map package.

Run: python -m fpf_thinking_map.verify
Exit 0 = all checks pass. Exit 1 = failure.
"""

from __future__ import annotations

import contextlib
import io
import sys
import traceback

from fpf_thinking_map.agentic_structure import (
    AutonomyBudgetDecl,
    BudgetEnvelope,
    CallPlanPrimitive,
    ClaimScope,
    ContextSlice,
    FormalityLevel,
    MembershipJudgment,
    ReliabilityPath,
)
from fpf_thinking_map.authorization import (
    AuthorizationReceipt,
    compute_state_fingerprint,
    issue_authorization_receipt,
)
from fpf_thinking_map.examples import (
    build_deploy_decision_map,
    build_deploy_rules,
    build_destructive_action_map,
    run_logic_scenario,
    run_scenario_full_traversal,
    run_scenario_missing_evidence,
    run_scenario_role_conflict,
    run_truth_table_demo,
)
from fpf_thinking_map.guards import GuardEngine, GuardScope, GuardVerdict
from fpf_thinking_map.logic import (
    CustomProp,
    DecisionRule,
    EvidenceFresh,
    EvidencePresent,
    GateAbstained,
    GateBlocked,
    LogicLayer,
    RiskAbove,
    RuleKind,
)
from fpf_thinking_map.move_intent import MoveIntent
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
    RoleAssignment,
    RolePrimitive,
    SemanticFloor,
    SpeechActPrimitive,
    SpeechActType,
    TransitionPrimitive,
    WorkPrimitive,
)
from fpf_thinking_map.reachability import unreachable_transitions
from fpf_thinking_map.state import ActiveState, MoveTrace, RuntimeBinding, SemanticMap
from fpf_thinking_map.traversal import (
    MapValidationError,
    Outcome,
    OutcomeCause,
    OutcomeKind,
    ThinkingMapTraversal,
)


def check(name: str, fn):
    try:
        fn()
        print(f"  PASS  {name}")
        return True
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        return False


def check_imports():
    from fpf_thinking_map import (
        ActiveState,
        AuthorizationReceipt,
        CommitmentMet,
        CommitmentPrimitive,
        ContextPrimitive,
        CustomProp,
        DecisionRule,
        EvidencePresent,
        EvidencePrimitive,
        Freshness,
        GateAbstained,
        GateBlocked,
        GatePasses,
        GatePrimitive,
        Guard,
        GuardEngine,
        GuardScope,
        GuardVerdict,
        HasMissingEvidence,
        InState,
        LogicLayer,
        MapValidationError,
        MoveIntent,
        MoveTrace,
        Outcome,
        OutcomeCause,
        OutcomeKind,
        PendingInput,
        PendingInputStatus,
        Prop,
        PublicationPrimitive,
        RiskAbove,
        RoleActive,
        RolePrimitive,
        RuleKind,
        RuntimeBinding,
        SemanticMap,
        ThinkingMapTraversal,
        TransitionAvailable,
        TransitionPrimitive,
        WorkPrimitive,
        compute_state_fingerprint,
        issue_authorization_receipt,
    )


def check_primitives():
    ctx = ContextPrimitive("c1", "Test", glossary={"x": "y"})
    assert ctx.term_defined("x")
    assert ctx.resolve_term("x") == "y"

    role = RolePrimitive("r1", "Tester", "c1", incompatible_with=["r2"])
    assert role.conflicts_with("r2")
    assert not role.conflicts_with("r3")

    c = CommitmentPrimitive("cm1", "Must test", DeonticModality.MUST, "c1")
    assert c.is_binding

    gc = GateCheck("gc1", "check", required_evidence=["e1", "e2"])
    assert gc.evaluate({"e1", "e2"}) == GateDecision.PASS
    assert gc.evaluate({"e1"}) == GateDecision.DEGRADE
    assert gc.evaluate(set()) == GateDecision.ABSTAIN

    gate = GatePrimitive("g1", "Gate", "c1", checks=[gc])
    assert gate.evaluate({"e1", "e2"}) == GateDecision.PASS
    assert gate.missing_evidence({"e1"}) == ["e2"]

    assert Freshness.STALE.value == "stale"

    fgr = FGR(0.8, 0.6, 0.9)
    assert fgr.sufficient(0.5, 0.5)


def check_state():
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("c1", "Ctx1"))
    sm.register_role(RolePrimitive("r1", "Role1", "c1"))
    sm.register_gate(GatePrimitive("g1", "Gate", "c1", checks=[
        GateCheck("gc1", "check", required_evidence=["e1"]),
    ]))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "c1", from_state="s1", to_state="s2",
        required_gate_id="g1", required_evidence=["e1"],
    ))

    assert len(sm.transitions_for("c1", "s1")) == 1
    assert len(sm.transitions_for("c1", "s2")) == 0
    assert len(sm.transitions_for("other", "s1")) == 0

    transitions = sm.transitions_for("c1", "s1")
    gates = sm.gates_for_transitions(transitions)
    assert len(gates) == 1

    binding = RuntimeBinding(active_context_id="c1", current_evidence=["e1"])
    state = ActiveState(sm, binding, current_state="s1")
    assert len(state.active_roles) == 0

    binding2 = RuntimeBinding(
        active_context_id="c1", actor_role_ids=["r1"], current_evidence=["e1"],
    )
    state2 = ActiveState(sm, binding2, current_state="s1")
    assert len(state2.active_roles) == 1

    binding3 = RuntimeBinding(active_context_id="c1", current_evidence=[])
    state3 = ActiveState(sm, binding3, current_state="s1")
    assert state3.missing_evidence_for("t1") == ["e1"]
    assert state3.missing_evidence_for("nonexistent") == []

    sl = state2.slice("t1")
    assert sl["move"]["id"] == "t1"
    assert sl["can_fire"] is True

    prompt = state2.to_llm_prompt_state()
    assert prompt["active_context"] == "c1"
    assert prompt["trace"] is None  # no previous move


def check_guards():
    sm = build_deploy_decision_map()

    b = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s = ActiveState(sm, b, current_state="ready_for_decision")
    engine = GuardEngine()

    results_focused = engine.evaluate(s, transition_id="ready_to_deploy")
    assert len(results_focused) > 0

    # Correct A.21 join: PASS outranks neutral ABSTAIN. The transition's own
    # required_evidence still exposes owner_approval as missing, so fixing the
    # gate lattice does not manufacture the evidence or make the move fire.
    gate_results = engine.evaluate(
        s, transition_id="ready_to_deploy",
        scopes={GuardScope.TRANSITION},
    )
    denials = [r for r in gate_results if r.verdict == GuardVerdict.DENY]
    assert len(denials) == 0
    assert s.missing_evidence_for("ready_to_deploy") == ["owner_approval"]

    # Role conflict
    b2 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst", "approver"],
        current_evidence=["test_results", "owner_approval"],
    )
    s2 = ActiveState(sm, b2, current_state="ready_for_decision")
    role_results = engine.evaluate(s2, scopes={GuardScope.ROLE})
    role_denials = [r for r in role_results if r.verdict == GuardVerdict.DENY]
    assert len(role_denials) == 1

    # Full evidence, single role → all allow
    b3 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
    )
    s3 = ActiveState(sm, b3, current_state="ready_for_decision")
    allowed, _ = engine.is_action_allowed(s3, transition_id="ready_to_deploy")
    assert allowed


def check_logic_operators():
    sm = SemanticMap()
    p = EvidencePresent("p")
    q = EvidencePresent("q")

    def ev(p_val, q_val, prop):
        e = []
        if p_val: e.append("p")
        if q_val: e.append("q")
        return prop.evaluate(ActiveState(sm, RuntimeBinding(current_evidence=e)))

    assert ev(True, True, p.NOT()) is False
    assert ev(False, True, p.NOT()) is True

    assert ev(True, True, p.AND(q)) is True
    assert ev(True, False, p.AND(q)) is False

    assert ev(False, False, p.OR(q)) is False
    assert ev(True, False, p.OR(q)) is True

    assert ev(True, True, p.XOR(q)) is False
    assert ev(True, False, p.XOR(q)) is True

    assert ev(True, False, p.IMPLIES(q)) is False
    assert ev(False, False, p.IMPLIES(q)) is True

    assert ev(True, True, p.IFF(q)) is True
    assert ev(True, False, p.IFF(q)) is False


def check_logic_layer():
    sm = build_deploy_decision_map()
    logic = build_deploy_rules()

    b = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s = ActiveState(sm, b, current_state="ready_for_decision")

    ctx = logic.to_llm_context(s)
    assert "facts" in ctx
    assert "actions" in ctx
    assert ctx["consistency"]["consistent"]

    deploy_ctx = logic.to_llm_context(s, tags={"deploy"})
    role_ctx = logic.to_llm_context(s, tags={"roles"})
    assert len(deploy_ctx["facts"]) + len(deploy_ctx["actions"]) >= 1
    assert len(role_ctx["actions"]) >= 1

    all_results = logic.evaluate_all(s)
    kinds = {r["kind"] for r in all_results}
    assert "route" in kinds or "block" in kinds or "hint" in kinds


def check_traversal():
    sm = build_deploy_decision_map()
    logic = build_deploy_rules()
    engine = ThinkingMapTraversal(sm, logic_layer=logic)

    b1 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results"],
    )
    s1 = engine.build_active_state(b1, "ready_for_decision")
    o1 = engine.step(s1, transition_id="ready_to_deploy")
    assert o1.kind == OutcomeKind.COLLECT_EVIDENCE
    assert "logic" in o1.llm_prompt_state
    assert "move" in o1.llm_prompt_state  # slice view

    # Full evidence → CONTINUE
    b2 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
    )
    s2 = engine.build_active_state(b2, "ready_for_decision")
    o2 = engine.step(s2)
    assert o2.kind == OutcomeKind.CONTINUE

    # Transition
    o3 = engine.attempt_transition(s2, "ready_to_deploy")
    assert o3.kind == OutcomeKind.CONTINUE
    assert o3.next_state == "deploying"

    # No context → CHANGE_FRAME
    s3 = engine.build_active_state(RuntimeBinding(task="orphan"))
    o4 = engine.step(s3)
    assert o4.kind == OutcomeKind.CHANGE_FRAME

    b5 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
        candidate_actions=["deploy"],
    )
    outcomes = engine.demo_walk(b5)
    assert len(outcomes) >= 1


def check_boundary_enforcement():
    """Verify the 4 findings are fixed: no cross-context leaks, no advisory evidence."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx_a", "Context A"))
    sm.register_context(ContextPrimitive("ctx_b", "Context B"))
    sm.register_role(RolePrimitive("role_a", "Role A", "ctx_a"))
    sm.register_role(RolePrimitive("role_b", "Role B", "ctx_b"))
    sm.register_transition(TransitionPrimitive(
        "t_a", "Move A", "ctx_a", "start", "done_a", required_evidence=["ev1"],
    ))
    sm.register_transition(TransitionPrimitive(
        "t_b", "Move B", "ctx_b", "start", "done_b",
    ))

    engine = ThinkingMapTraversal(sm)

    # --- Finding 1: cross-context transition blocked ---
    b = RuntimeBinding(active_context_id="ctx_a", current_evidence=["ev1"])
    s = engine.build_active_state(b, "start")
    o = engine.attempt_transition(s, "t_b")
    assert o.kind == OutcomeKind.ABSTAIN, f"Cross-context transition should be denied, got {o.kind}"
    assert s.current_state == "start", "State should not have changed"

    # step() also blocks cross-context transition_id
    o2 = engine.step(s, transition_id="t_b")
    assert o2.kind == OutcomeKind.ABSTAIN

    # same-context transition works
    o3 = engine.attempt_transition(s, "t_a")
    assert o3.kind == OutcomeKind.CONTINUE
    assert o3.next_state == "done_a"

    # --- Finding 2: required_evidence enforced on execution ---
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("c", "C"))
    sm2.register_transition(TransitionPrimitive(
        "t_ev", "Needs evidence", "c", "init", "ready", required_evidence=["proof"],
    ))
    engine2 = ThinkingMapTraversal(sm2)
    b2 = RuntimeBinding(active_context_id="c", current_evidence=[])
    s2 = engine2.build_active_state(b2, "init")

    # attempt_transition must deny when evidence missing
    o4 = engine2.attempt_transition(s2, "t_ev")
    assert o4.kind == OutcomeKind.COLLECT_EVIDENCE, f"Should deny missing evidence, got {o4.kind}"
    assert s2.current_state == "init"

    # transition_to must also deny
    assert s2.transition_to("t_ev") is False

    # with evidence, it works
    s2.add_evidence("proof")
    assert s2.transition_to("t_ev") is True
    assert s2.current_state == "ready"

    # --- Finding 3: roles validated against active context ---
    b3 = RuntimeBinding(
        active_context_id="ctx_a",
        actor_role_ids=["role_a", "role_b"],
    )
    s3 = ActiveState(sm, b3, "start")
    active = s3.active_roles
    assert len(active) == 1, f"Foreign role should be filtered, got {len(active)} roles"
    assert active[0].role_id == "role_a"

    # --- Finding 4: risk_sensitive enforced ---
    logic = LogicLayer()
    logic.add_rule(DecisionRule(
        name="risk_rule",
        condition=RiskAbove("high"),
        action_if_true="escalate",
        kind=RuleKind.ROUTE,
        risk_sensitive=True,
    ))
    logic.add_rule(DecisionRule(
        name="normal_rule",
        condition=CustomProp("always_true", lambda s: True),
        action_if_true="proceed",
        kind=RuleKind.ROUTE,
        risk_sensitive=False,
    ))

    b_low = RuntimeBinding(risk_level="normal")
    s_low = ActiveState(SemanticMap(), b_low)
    actions_low = logic.satisfied_actions(s_low)
    assert "escalate" not in actions_low, "risk_sensitive rule should be skipped at normal risk"
    assert "proceed" in actions_low

    b_high = RuntimeBinding(risk_level="high")
    s_high = ActiveState(SemanticMap(), b_high)
    actions_high = logic.satisfied_actions(s_high)
    assert "escalate" in actions_high, "risk_sensitive rule should fire at high risk"
    assert "proceed" in actions_high


def check_audit_fixes():
    """Verify R07/R08, R09, R17, R20/R21 from the FPF audit."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_role(RolePrimitive("dev", "Developer", "ctx"))

    # --- R07/R08: RoleAssignment ---
    ra = RoleAssignment(
        assignment_id="assign_1", holder_id="alice", role_id="dev", context_id="ctx",
    )
    sm.register_role_assignment(ra)
    assert "assign_1" in sm.role_assignments

    b = RuntimeBinding(actor="alice", active_context_id="ctx")
    s = ActiveState(sm, b)
    assert len(s.active_assignments) == 1
    assert len(s.active_roles) == 1
    assert s.active_roles[0].role_id == "dev"

    # Expired assignment → no active roles
    ra_expired = RoleAssignment(
        assignment_id="assign_2", holder_id="bob", role_id="dev",
        context_id="ctx", expired=True,
    )
    sm.register_role_assignment(ra_expired)
    b2 = RuntimeBinding(actor="bob", active_context_id="ctx")
    s2 = ActiveState(sm, b2)
    assert len(s2.active_assignments) == 0
    assert len(s2.active_roles) == 0

    # Guard catches expired assignment
    engine = GuardEngine()
    results = engine.evaluate(s2)
    expired_denials = [r for r in results if r.guard_name == "expired_assignment" and r.verdict == GuardVerdict.DENY]
    assert len(expired_denials) == 1

    # --- R09: performed_under on WorkPrimitive ---
    w = WorkPrimitive(
        work_id="w1", label="Deploy", context_id="ctx",
        performed_under="assign_1",
    )
    assert w.performed_under == "assign_1"

    # --- R17: subject on CommitmentPrimitive ---
    c = CommitmentPrimitive(
        "cm1", "Must deploy", DeonticModality.MUST, "ctx",
        subject="alice",
    )
    assert c.subject == "alice"

    # --- R20/R21: SpeechActPrimitive ---
    sa = SpeechActPrimitive(
        act_id="approval_1",
        act_type=SpeechActType.APPROVE,
        actor_id="manager",
        context_id="ctx",
        addressed_to="alice",
        institutes=["cm1"],
        evidence_refs=["test_results"],
    )
    sm.register_speech_act(sa)
    assert "approval_1" in sm.speech_acts

    # Valid speech act as evidence → guard allows
    b3 = RuntimeBinding(actor="alice", active_context_id="ctx", current_evidence=["approval_1"])
    s3 = ActiveState(sm, b3)
    results3 = engine.evaluate(s3)
    sa_denials = [r for r in results3 if r.guard_name == "speech_act_validity" and r.verdict == GuardVerdict.DENY]
    assert len(sa_denials) == 0

    # Expired speech act → guard denies
    sa.expired = True
    results4 = engine.evaluate(s3)
    sa_denials2 = [r for r in results4 if r.guard_name == "speech_act_validity" and r.verdict == GuardVerdict.DENY]
    assert len(sa_denials2) == 1

    # GateDecision.BLOCK exists
    assert GateDecision.BLOCK.value == "block"


def check_end_to_end():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_scenario_missing_evidence()
        run_scenario_role_conflict()
        run_scenario_full_traversal()
    output = buf.getvalue()
    assert "SCENARIO:" in output


def check_logic_end_to_end():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_logic_scenario()
        run_truth_table_demo()
    output = buf.getvalue()
    assert "LOGIC GLUE SCENARIO" in output
    assert "TRUTH TABLE" in output


def check_horizontal_properties():
    """Verify the 25 horizontal improvements are structurally present."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("c1", "Ctx"))
    sm.register_role(RolePrimitive("r1", "R1", "c1"))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "c1", "s1", "s2",
        required_gate_id="g1", required_evidence=["e1"],
    ))
    sm.register_gate(GatePrimitive("g1", "G1", "c1", checks=[
        GateCheck("gc1", "chk", required_evidence=["e1"]),
    ]))

    assert hasattr(sm, "transitions_for")

    assert hasattr(sm, "gates_for_transitions")

    b = RuntimeBinding(active_context_id="c1", actor_role_ids=["r1"], current_evidence=["e1"])
    s = ActiveState(sm, b, "s1")
    assert "move" in s.slice("t1")

    assert RuleKind.BLOCK.value == "block"
    assert RuleKind.HINT.value == "hint"

    dr = DecisionRule("test", EvidencePresent("x"), "a", exclusive_with=["b"])
    assert dr.exclusive_with == ["b"]

    s2 = ActiveState(sm, RuntimeBinding(active_context_id="c1"), "s1")
    assert s2.active_roles == []

    assert hasattr(sm, "register_work")

    assert GuardScope.TRANSITION.value == "transition"

    assert Freshness.STALE.value == "stale"
    assert Freshness.EXPIRED.value == "expired"

    mt = MoveTrace()
    assert hasattr(mt, "previous_state")
    assert hasattr(mt, "evidence_delta")


def check_ttl_decay():
    """Verify TTL evidence decay over traversal steps."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_evidence(EvidencePrimitive(
        evidence_id="fast_ev", label="Fast Evidence", context_id="ctx",
        freshness=Freshness.CURRENT, ttl_steps=2,
        fgr=FGR(0.8, 0.6, 0.9),
    ))
    sm.register_evidence(EvidencePrimitive(
        evidence_id="stable_ev", label="Stable Evidence", context_id="ctx",
        freshness=Freshness.CURRENT, ttl_steps=None,
    ))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "ctx", "s1", "s2", required_evidence=["fast_ev"],
    ))

    b = RuntimeBinding(
        active_context_id="ctx", current_evidence=["fast_ev", "stable_ev"],
    )
    s = ActiveState(sm, b, current_state="s1")

    # Step 0: both CURRENT
    assert s.effective_freshness("fast_ev") == Freshness.CURRENT
    assert s.effective_freshness("stable_ev") == Freshness.CURRENT

    # Step 2: fast_ev decays to STALE (age == ttl_steps)
    s.step_count = 2
    assert s.effective_freshness("fast_ev") == Freshness.STALE
    assert s.effective_freshness("stable_ev") == Freshness.CURRENT

    # Step 4: fast_ev decays to EXPIRED (age == 2 * ttl_steps)
    s.step_count = 4
    assert s.effective_freshness("fast_ev") == Freshness.EXPIRED

    # Unknown evidence returns UNKNOWN
    assert s.effective_freshness("nonexistent") == Freshness.UNKNOWN

    # Guard catches TTL-decayed evidence
    engine = GuardEngine()
    s2 = ActiveState(sm, RuntimeBinding(
        active_context_id="ctx", current_evidence=["fast_ev"],
    ), current_state="s1")
    s2.step_count = 3
    results = engine.evaluate(s2, transition_id="t1")
    freshness_warnings = [
        r for r in results
        if r.guard_name == "evidence_freshness" and r.verdict == GuardVerdict.WARN
    ]
    assert len(freshness_warnings) == 1, f"Expected TTL decay warning, got {freshness_warnings}"

    # Evidence added mid-traversal starts aging from that step
    s3 = ActiveState(sm, RuntimeBinding(active_context_id="ctx"), current_state="s1")
    s3.step_count = 10
    s3.add_evidence("fast_ev")
    assert s3._evidence_added_at["fast_ev"] == 10
    assert s3.effective_freshness("fast_ev") == Freshness.CURRENT
    s3.step_count = 12
    assert s3.effective_freshness("fast_ev") == Freshness.STALE


def check_stagnation_counter():
    """#28: visit counter + countdown for repeated (context, state) with no new evidence."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "ctx", "stuck", "done", required_evidence=["missing_ev"],
    ))

    b = RuntimeBinding(active_context_id="ctx")
    engine = ThinkingMapTraversal(sm)
    s = engine.build_active_state(b, current_state="stuck")

    # First visit: 1 visit registered, threshold default 3, 2 remaining, not stagnant
    o1 = engine.step(s)
    st1 = o1.llm_prompt_state["stagnation"]
    assert st1["visits"] == 1, st1
    assert st1["remaining"] == 2, st1
    assert st1["threshold"] == 3
    assert st1["is_stagnant"] is False

    # Same state, same (empty) evidence, no progress — counter climbs
    o2 = engine.step(s)
    o3 = engine.step(s)
    st3 = o3.llm_prompt_state["stagnation"]
    assert st3["visits"] == 3, st3
    assert st3["remaining"] == 0, st3
    assert st3["is_stagnant"] is True

    # New evidence arrives — counter resets, this is not a loop anymore
    s.add_evidence("missing_ev")
    o4 = engine.step(s)
    st4 = o4.llm_prompt_state["stagnation"]
    assert st4["visits"] == 1, "new evidence must reset the stagnation counter"
    assert st4["is_stagnant"] is False

    # slice() carries the same signal for a transition-focused call
    s2 = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="stuck")
    o5 = engine.step(s2, transition_id="t1")
    assert "stagnation" in o5.llm_prompt_state
    assert o5.llm_prompt_state["stagnation"]["visits"] == 1

    # Custom threshold is honored
    s3 = ActiveState(sm, RuntimeBinding(active_context_id="ctx"), current_state="stuck", stagnation_threshold=1)
    s3.register_visit()
    assert s3.is_stagnant is True
    assert s3.visits_remaining == 0

    # attempt_transition (a real move) does not itself register a visit —
    # only step() (the "what can I do" scan) counts as one
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("ctx2", "Test2"))
    sm2.register_transition(TransitionPrimitive("t2", "Go", "ctx2", "a", "b"))
    engine2 = ThinkingMapTraversal(sm2)
    s4 = engine2.build_active_state(RuntimeBinding(active_context_id="ctx2"), current_state="a")
    engine2.attempt_transition(s4, "t2")
    assert s4.visit_count == 0


def check_idle_outcome():
    """Verify IDLE outcome for clean terminal states."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive(
        "t1", "Start to Done", "ctx", "start", "done",
    ))

    engine = ThinkingMapTraversal(sm)

    # At "done" state with no transitions, no actions → IDLE
    b = RuntimeBinding(active_context_id="ctx")
    s = engine.build_active_state(b, current_state="done")
    o = engine.step(s)
    assert o.kind == OutcomeKind.IDLE, f"Expected IDLE, got {o.kind}"

    # At "done" with candidate_actions → CONTINUE (model can still work)
    b2 = RuntimeBinding(
        active_context_id="ctx", candidate_actions=["report"],
    )
    s2 = engine.build_active_state(b2, current_state="done")
    o2 = engine.step(s2)
    assert o2.kind == OutcomeKind.CONTINUE, f"Expected CONTINUE, got {o2.kind}"

    # At "start" with transitions → CONTINUE (normal flow)
    b3 = RuntimeBinding(active_context_id="ctx")
    s3 = engine.build_active_state(b3, current_state="start")
    o3 = engine.step(s3)
    assert o3.kind == OutcomeKind.CONTINUE

    # demo_walk stops on IDLE
    b4 = RuntimeBinding(
        active_context_id="ctx",
        current_evidence=[],
    )
    outcomes = engine.demo_walk(b4, max_steps=10)
    final = outcomes[-1]
    assert final.kind in (OutcomeKind.IDLE, OutcomeKind.CONTINUE), \
        f"Demo walk should reach IDLE or stop, got {final.kind}"


def check_bridge_outcome():
    """Verify BRIDGE outcome for cross-context escape."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive(
        context_id="ctx_a", label="Context A",
        bridges_to=[ContextBridge(
            target_context_id="ctx_b",
            mapping={"deploy": "release"},
            translation_loss="ops uses 'release' where dev uses 'deploy'",
        )],
    ))
    sm.register_context(ContextPrimitive(context_id="ctx_b", label="Context B"))
    sm.register_transition(TransitionPrimitive(
        "t_a", "A start", "ctx_a", "start", "done",
    ))
    sm.register_transition(TransitionPrimitive(
        "t_b1", "B entry", "ctx_b", "ready", "active",
    ))
    sm.register_transition(TransitionPrimitive(
        "t_b2", "B work", "ctx_b", "active", "complete",
    ))

    engine = ThinkingMapTraversal(sm)

    # In ctx_a at "done" — no transitions, but bridge to ctx_b exists
    b = RuntimeBinding(active_context_id="ctx_a")
    s = engine.build_active_state(b, current_state="done")
    o = engine.step(s)
    assert o.kind == OutcomeKind.BRIDGE, f"Expected BRIDGE, got {o.kind}"
    assert "ctx_b" in o.reason
    assert "bridge_options" in o.llm_prompt_state
    opts = o.llm_prompt_state["bridge_options"]
    assert len(opts) == 1
    assert opts[0]["target_context"] == "ctx_b"
    assert "ready" in opts[0]["entry_states"]
    assert "active" in opts[0]["entry_states"]

    # Bridge precomputation: SemanticMap.bridge_options
    bridge_opts = sm.bridge_options("ctx_a")
    assert len(bridge_opts) == 1
    assert bridge_opts[0]["target_context"] == "ctx_b"

    # No bridges from ctx_b
    assert sm.bridge_options("ctx_b") == []

    # Context without bridges at dead end → IDLE, not BRIDGE
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("iso", "Isolated"))
    engine2 = ThinkingMapTraversal(sm2)
    b2 = RuntimeBinding(active_context_id="iso")
    s2 = engine2.build_active_state(b2, current_state="stuck")
    o2 = engine2.step(s2)
    assert o2.kind == OutcomeKind.IDLE


def check_bridge_crossing():
    """#26: validated writeback for bridge crossing — enact, not just advertise."""
    def _make_map(license_: bool):
        sm = SemanticMap()
        sm.register_context(ContextPrimitive(
            context_id="ctx_a", label="Context A",
            bridges_to=[ContextBridge(
                target_context_id="ctx_b",
                mapping={"deploy": "release"},
                translation_loss="ops uses 'release' where dev uses 'deploy'",
                substitution_license=license_,
            )],
        ))
        sm.register_context(ContextPrimitive(context_id="ctx_b", label="Context B"))
        sm.register_transition(TransitionPrimitive(
            "t_b1", "B entry", "ctx_b", "ready", "active",
        ))
        return sm

    # Unlicensed bridge, normal risk — lossy but tolerable, crossing succeeds
    sm = _make_map(license_=False)
    engine = ThinkingMapTraversal(sm)
    b = RuntimeBinding(active_context_id="ctx_a", risk_level="normal")
    s = engine.build_active_state(b, current_state="done")
    o = engine.attempt_bridge(s, "ctx_b", "ready")
    assert o.kind == OutcomeKind.CONTINUE, f"Expected CONTINUE, got {o.kind}: {o.reason}"
    assert s.binding.active_context_id == "ctx_b"
    assert s.current_state == "ready"
    assert s.trace.bridge_target == "ctx_b"

    # Unlicensed bridge, high risk — refused, state untouched
    sm2 = _make_map(license_=False)
    engine2 = ThinkingMapTraversal(sm2)
    b2 = RuntimeBinding(active_context_id="ctx_a", risk_level="high")
    s2 = engine2.build_active_state(b2, current_state="done")
    o2 = engine2.attempt_bridge(s2, "ctx_b", "ready")
    assert o2.kind == OutcomeKind.ESCALATE, f"Expected ESCALATE, got {o2.kind}"
    assert "unlicensed" in o2.reason
    assert s2.binding.active_context_id == "ctx_a", "unlicensed+high-risk must not mutate state"
    assert s2.current_state == "done"

    # Licensed bridge, high risk — allowed despite risk level
    sm3 = _make_map(license_=True)
    engine3 = ThinkingMapTraversal(sm3)
    b3 = RuntimeBinding(active_context_id="ctx_a", risk_level="high")
    s3 = engine3.build_active_state(b3, current_state="done")
    o3 = engine3.attempt_bridge(s3, "ctx_b", "ready")
    assert o3.kind == OutcomeKind.CONTINUE
    assert s3.binding.active_context_id == "ctx_b"

    # No such bridge target
    sm4 = _make_map(license_=True)
    engine4 = ThinkingMapTraversal(sm4)
    b4 = RuntimeBinding(active_context_id="ctx_a")
    s4 = engine4.build_active_state(b4, current_state="done")
    o4 = engine4.attempt_bridge(s4, "ctx_z", "ready")
    assert o4.kind == OutcomeKind.ABSTAIN
    assert "no bridge" in o4.reason

    # Invalid entry state — not a real transition start in target context
    sm5 = _make_map(license_=True)
    engine5 = ThinkingMapTraversal(sm5)
    b5 = RuntimeBinding(active_context_id="ctx_a")
    s5 = engine5.build_active_state(b5, current_state="done")
    o5 = engine5.attempt_bridge(s5, "ctx_b", "nowhere")
    assert o5.kind == OutcomeKind.ABSTAIN
    assert "not a valid entry state" in o5.reason


def check_lean_slice():
    """#27: include_full_state=False ships the slice without the full board."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive(context_id="ctx", label="Ctx"))
    sm.register_transition(TransitionPrimitive(
        "t1", "Do it", "ctx", "start", "done",
    ))
    engine = ThinkingMapTraversal(sm)
    b = RuntimeBinding(active_context_id="ctx")
    s = engine.build_active_state(b, current_state="start")

    o_full = engine.step(s, transition_id="t1")
    assert "full_state" in o_full.llm_prompt_state
    assert "move" in o_full.llm_prompt_state

    s2 = engine.build_active_state(b, current_state="start")
    o_lean = engine.step(s2, transition_id="t1", include_full_state=False)
    assert "full_state" not in o_lean.llm_prompt_state
    assert "move" in o_lean.llm_prompt_state, "lean payload must keep the slice itself"


def check_semantic_floors():
    """Verify semantic floor TTL computation from FGR trust factors."""
    # Floor constants exist and are correct
    assert FLOOR_BASE_TTL[SemanticFloor.STRUCTURAL] is None
    assert FLOOR_BASE_TTL[SemanticFloor.BINDING] == 10
    assert FLOOR_BASE_TTL[SemanticFloor.EVIDENTIARY] == 8
    assert FLOOR_BASE_TTL[SemanticFloor.OPERATIONAL] == 2
    assert FLOOR_BASE_TTL[SemanticFloor.PUBLICATION] is None

    # --- computed_ttl from explicit ttl_steps (always wins) ---
    ev_explicit = EvidencePrimitive(
        "e1", "Explicit", "ctx", ttl_steps=5,
        semantic_floor=SemanticFloor.EVIDENTIARY,
        fgr=FGR(1.0, 0.5, 1.0),
    )
    assert ev_explicit.computed_ttl == 5, "Explicit ttl_steps must win"

    # --- computed_ttl from EVIDENTIARY floor + FGR ---
    ev_high = EvidencePrimitive(
        "e2", "Formal proof", "ctx",
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.EVIDENTIARY,
        fgr=FGR(formality=1.0, scope=0.5, reliability=1.0),
    )
    assert ev_high.computed_ttl == 8, f"F=1.0 R=1.0 → 8, got {ev_high.computed_ttl}"

    ev_mid = EvidencePrimitive(
        "e3", "CI results", "ctx",
        semantic_floor=SemanticFloor.EVIDENTIARY,
        fgr=FGR(formality=0.8, scope=0.6, reliability=0.9),
    )
    assert ev_mid.computed_ttl == 6, f"F=0.8 R=0.9 → round(0.72*8)=6, got {ev_mid.computed_ttl}"

    ev_weak = EvidencePrimitive(
        "e4", "Anecdotal", "ctx",
        semantic_floor=SemanticFloor.EVIDENTIARY,
        fgr=FGR(formality=0.2, scope=0.3, reliability=0.3),
    )
    assert ev_weak.computed_ttl == 1, f"F=0.2 R=0.3 → max(1, round(0.06*8))=1, got {ev_weak.computed_ttl}"

    # --- BINDING floor: fixed TTL ---
    ev_binding = EvidencePrimitive(
        "e5", "Assignment record", "ctx",
        semantic_floor=SemanticFloor.BINDING,
    )
    assert ev_binding.computed_ttl == 10

    # --- OPERATIONAL floor: fixed TTL ---
    ev_ops = EvidencePrimitive(
        "e6", "Gate eval result", "ctx",
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.OPERATIONAL,
    )
    assert ev_ops.computed_ttl == 2

    # --- STRUCTURAL floor: no decay ---
    ev_struct = EvidencePrimitive(
        "e7", "Context definition", "ctx",
        semantic_floor=SemanticFloor.STRUCTURAL,
    )
    assert ev_struct.computed_ttl is None

    # --- No floor: no decay ---
    ev_none = EvidencePrimitive("e8", "Plain", "ctx")
    assert ev_none.computed_ttl is None

    # --- Integration: floor-computed TTL drives effective_freshness ---
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_evidence(ev_ops)  # OPERATIONAL, TTL=2
    sm.register_evidence(ev_high)  # EVIDENTIARY F=1.0 R=1.0, TTL=8
    sm.register_transition(TransitionPrimitive(
        "t1", "Go", "ctx", "s1", "s2",
        required_evidence=["e6"],
    ))

    b = RuntimeBinding(
        active_context_id="ctx",
        current_evidence=["e6", "e2"],
    )
    s = ActiveState(sm, b, current_state="s1")

    # At step 0 both CURRENT
    assert s.effective_freshness("e6") == Freshness.CURRENT
    assert s.effective_freshness("e2") == Freshness.CURRENT

    # At step 2: ops evidence (TTL=2) goes STALE, evidentiary (TTL=8) still CURRENT
    s.step_count = 2
    assert s.effective_freshness("e6") == Freshness.STALE
    assert s.effective_freshness("e2") == Freshness.CURRENT

    # At step 4: ops evidence EXPIRED, evidentiary still CURRENT
    s.step_count = 4
    assert s.effective_freshness("e6") == Freshness.EXPIRED
    assert s.effective_freshness("e2") == Freshness.CURRENT

    # At step 8: evidentiary goes STALE
    s.step_count = 8
    assert s.effective_freshness("e2") == Freshness.STALE

    # At step 16: evidentiary EXPIRED
    s.step_count = 16
    assert s.effective_freshness("e2") == Freshness.EXPIRED


def check_evidence_fresh_prop():
    """Verify EvidenceFresh proposition — temporal check vs structural EvidencePresent."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_evidence(EvidencePrimitive(
        "ev1", "Fast decay", "ctx",
        freshness=Freshness.CURRENT,
        semantic_floor=SemanticFloor.OPERATIONAL,
    ))

    present = EvidencePresent("ev1")
    fresh = EvidenceFresh("ev1")

    # At step 0: both True
    b = RuntimeBinding(active_context_id="ctx", current_evidence=["ev1"])
    s = ActiveState(sm, b)
    assert present.evaluate(s) is True
    assert fresh.evaluate(s) is True

    # At step 2 (TTL=2 for OPERATIONAL): present still True, fresh now False
    s.step_count = 2
    assert present.evaluate(s) is True
    assert fresh.evaluate(s) is False

    # Missing evidence: both False
    s2 = ActiveState(sm, RuntimeBinding(active_context_id="ctx"))
    assert present.evaluate(s2) is False
    assert fresh.evaluate(s2) is False

    # deploy_readiness rule uses EvidenceFresh — verify it fires correctly
    deploy_sm = build_deploy_decision_map()
    logic = build_deploy_rules()

    # Fresh evidence → deploy_readiness fires
    b3 = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval"],
    )
    s3 = ActiveState(deploy_sm, b3, current_state="ready_for_decision")
    actions = logic.satisfied_actions(s3, tags={"readiness"})
    assert "proceed_to_deploy" in actions, f"Fresh evidence should allow deploy, got {actions}"

    # Decay evidence past TTL → deploy_readiness stops firing
    # test_results: F=0.8, R=0.9 → TTL=6. At step 7, it's STALE.
    s3.step_count = 7
    actions_stale = logic.satisfied_actions(s3, tags={"readiness"})
    assert "proceed_to_deploy" not in actions_stale, \
        f"Stale evidence should block deploy, got {actions_stale}"

    # decay warning rule fires when evidence present but stale
    decay_actions = logic.satisfied_actions(s3, tags={"decay"})
    assert "evidence_stale_refresh_needed" in decay_actions, \
        f"Decay warning should fire, got {decay_actions}"

    # to_llm_prompt_state includes evidence_status
    prompt = s3.to_llm_prompt_state()
    assert "evidence_status" in prompt
    assert "test_results" in prompt["evidence_status"]
    status = prompt["evidence_status"]["test_results"]
    assert status["freshness"] == "stale"
    assert status["ttl_remaining"] == 0

    # slice annotates evidence with freshness
    deploy_sm.register_transition(TransitionPrimitive(
        "t_test", "Test", "project_delivery", "ready_for_decision", "done",
        required_evidence=["test_results"],
    ))
    sl = s3.slice("t_test")
    assert len(sl["evidence"]["available"]) > 0
    ev_item = sl["evidence"]["available"][0]
    assert "freshness" in ev_item
    assert "ttl_remaining" in ev_item


def check_slice_blockers():
    """Verify slice includes blockers for HITL visibility."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_role(RolePrimitive("r1", "Role", "ctx"))
    sm.register_gate(GatePrimitive("g1", "Gate", "ctx", checks=[
        GateCheck("gc1", "Check A", required_evidence=["ev_a"]),
        GateCheck("gc2", "Check B", required_evidence=["ev_b"]),
    ]))
    sm.register_transition(TransitionPrimitive(
        "t1", "Guarded Move", "ctx", "s1", "s2",
        required_gate_id="g1", required_evidence=["ev_a", "ev_b"],
    ))

    # Missing evidence → blockers explain why
    b1 = RuntimeBinding(
        active_context_id="ctx", actor_role_ids=["r1"],
        current_evidence=["ev_a"],
    )
    s1 = ActiveState(sm, b1, current_state="s1")
    sl1 = s1.slice("t1")
    assert sl1["can_fire"] is False
    assert len(sl1["blockers"]) > 0
    assert any("ev_b" in b for b in sl1["blockers"])

    # Full evidence → no blockers
    b2 = RuntimeBinding(
        active_context_id="ctx", actor_role_ids=["r1"],
        current_evidence=["ev_a", "ev_b"],
    )
    s2 = ActiveState(sm, b2, current_state="s1")
    sl2 = s2.slice("t1")
    assert sl2["can_fire"] is True
    assert sl2["blockers"] == []

    # Guard blockers passed through
    sl3 = s1.slice("t1", guard_blockers=["role conflict: analyst ⊥ approver"])
    assert "role conflict: analyst ⊥ approver" in sl3["blockers"]

    # Nonexistent transition → error, no blockers
    sl_err = s1.slice("nonexistent")
    assert "error" in sl_err


def check_response_contract():
    """Verify response contract is precomputed from state, not empty scaffolding."""
    sm = build_deploy_decision_map()

    b = RuntimeBinding(
        active_context_id="project_delivery",
        actor_role_ids=["analyst"],
        current_evidence=["test_results", "owner_approval"],
        audience="team lead",
    )
    s = ActiveState(sm, b, current_state="ready_for_decision")

    # Contract from slice
    sl = s.slice("ready_to_deploy")
    rc = sl["response_contract"]

    # Pre-filled fields are populated, not empty
    assert rc["scope"] == "Project Delivery"
    assert rc["audience"] == "team lead"
    assert len(rc["basis"]) == 2
    assert any(e["id"] == "test_results" for e in rc["basis"])
    assert any(e["id"] == "owner_approval" for e in rc["basis"])

    # Basis includes freshness and TTL
    for e in rc["basis"]:
        assert "freshness" in e
        assert "ttl_remaining" in e

    # Canonical terms from context glossary
    assert "deploy" in rc["correct_terms"]
    assert "rollback" in rc["correct_terms"]

    # Modality from commitments
    assert len(rc["obligations"]) >= 1
    must_commit = [m for m in rc["obligations"] if m["force"] == "must"]
    assert len(must_commit) >= 1

    # Allowed use from MUST/SHOULD commitments
    assert len(rc["allowed_use"]) >= 1

    # Not-allowed includes context invariants
    assert any("no deploy without" in n for n in rc["not_allowed_use"])

    # Model-filled fields are empty (waiting for model)
    assert rc["claim"] == ""
    assert rc["risky_aliases"] == []

    # Standalone contract (no transition_id)
    rc2 = s.response_contract()
    assert rc2["scope"] == "Project Delivery"
    assert len(rc2["basis"]) == 2


def check_requires_human_authorization():
    """requires_human_authorization: legal is not auto-fireable — requires authorized=True."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive(
        "t_release", "Release", "ctx", "candidate", "released",
        requires_human_authorization=True,
    ))
    sm.register_transition(TransitionPrimitive(
        "t_other", "Unrelated self-loop", "ctx", "candidate", "candidate",
    ))
    engine = ThinkingMapTraversal(sm)

    # slice() reports it as visible but not fireable by the model
    b = RuntimeBinding(active_context_id="ctx")
    s = engine.build_active_state(b, current_state="candidate")
    sl = s.slice("t_release")
    assert sl["move"]["requires_human_authorization"] is True
    assert sl["move"]["currently_pending"] is False
    assert sl["can_fire"] is False
    assert any("requires_human_authorization" in blk for blk in sl["blockers"])
    assert s.to_llm_prompt_state()["pending_authorizations"] == []

    # attempt_transition without authorization → ESCALATE, state unchanged,
    # and pending_authorizations now names the specific transition waiting
    o1 = engine.attempt_transition(s, "t_release")
    assert o1.kind == OutcomeKind.ESCALATE, f"Expected ESCALATE, got {o1.kind}"
    assert s.current_state == "candidate"
    assert s.pending_authorizations == {"t_release"}, s.pending_authorizations
    assert s.slice("t_release")["move"]["currently_pending"] is True

    # an unrelated transition firing must NOT silently clear someone else's
    # still-unresolved pending ask
    o_other = engine.attempt_transition(s, "t_other")
    assert o_other.kind == OutcomeKind.CONTINUE
    assert s.pending_authorizations == {"t_release"}, (
        "firing an unrelated transition must not clear a different "
        "transition's pending_authorizations entry"
    )

    # step() surfaces a warning about it regardless of which move is in view
    step_outcome = engine.step(s, transition_id="t_other")
    assert any("t_release" in w and "awaiting" in w for w in step_outcome.warnings), (
        step_outcome.warnings
    )

    # direct transition_to() without authorization also refuses — no bypass
    assert s.transition_to("t_release") is False
    assert s.current_state == "candidate"

    # attempt_transition with authorized=True fires normally, and clears
    # pending_authorizations since this is the specific ask being resolved
    o2 = engine.attempt_transition(s, "t_release", authorized=True)
    assert o2.kind == OutcomeKind.CONTINUE, f"Expected CONTINUE, got {o2.kind}"
    assert s.current_state == "released"
    assert s.pending_authorizations == set()

    # resolve_pending_authorization(): stale-ask path, no history kept
    s.pending_authorizations.add("some_stale_ask")
    s.resolve_pending_authorization("some_stale_ask")
    assert s.pending_authorizations == set()
    assert "some_stale_ask" not in s.denied_authorizations

    # concurrent pending asks: escalating a second, different transition
    # must not silently erase tracking of the first — found by testing
    # against the live cursor-fpf-test-mcp deployment
    sm_concurrent = SemanticMap()
    sm_concurrent.register_context(ContextPrimitive("ctxc", "Concurrent"))
    sm_concurrent.register_transition(TransitionPrimitive(
        "delete_a", "Delete A", "ctxc", "start", "a_gone", requires_human_authorization=True,
    ))
    sm_concurrent.register_transition(TransitionPrimitive(
        "delete_b", "Delete B", "ctxc", "start", "b_gone", requires_human_authorization=True,
    ))
    engine_c = ThinkingMapTraversal(sm_concurrent)
    sc = engine_c.build_active_state(RuntimeBinding(active_context_id="ctxc"), current_state="start")
    engine_c.attempt_transition(sc, "delete_a")
    assert sc.pending_authorizations == {"delete_a"}
    engine_c.attempt_transition(sc, "delete_b")
    assert sc.pending_authorizations == {"delete_a", "delete_b"}, (
        f"escalating delete_b must not erase delete_a's still-pending ask, "
        f"got {sc.pending_authorizations}"
    )
    step_c = engine_c.step(sc)
    assert any("delete_a" in w for w in step_c.warnings), step_c.warnings
    assert any("delete_b" in w for w in step_c.warnings), step_c.warnings
    engine_c.attempt_transition(sc, "delete_a", authorized=True)
    assert sc.pending_authorizations == {"delete_b"}, (
        "resolving delete_a must not touch delete_b's still-pending ask"
    )

    # ordinary transitions are unaffected — requires_human_authorization defaults to False
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("ctx2", "Test2"))
    sm2.register_transition(TransitionPrimitive("t_norm", "Go", "ctx2", "a", "b"))
    engine2 = ThinkingMapTraversal(sm2)
    s2 = engine2.build_active_state(RuntimeBinding(active_context_id="ctx2"), current_state="a")
    o3 = engine2.attempt_transition(s2, "t_norm")
    assert o3.kind == OutcomeKind.CONTINUE
    assert s2.current_state == "b"

    # ESCALATE must surface missing evidence too, not just the auth requirement —
    # a human shouldn't say "yes" to a request that still can't fire regardless
    sm3 = SemanticMap()
    sm3.register_context(ContextPrimitive("ctx3", "Test3"))
    sm3.register_transition(TransitionPrimitive(
        "t_gated", "Gated", "ctx3", "start", "done",
        required_evidence=["proof"], requires_human_authorization=True,
    ))
    engine3 = ThinkingMapTraversal(sm3)
    s3 = engine3.build_active_state(RuntimeBinding(active_context_id="ctx3"), current_state="start")
    o4 = engine3.attempt_transition(s3, "t_gated")
    assert o4.kind == OutcomeKind.ESCALATE, f"Expected ESCALATE, got {o4.kind}"
    assert o4.missing_evidence == ["proof"], (
        f"ESCALATE must report missing evidence alongside the auth requirement, "
        f"got {o4.missing_evidence}"
    )
    assert "proof" in o4.reason

    # safe_alternatives: declared, surfaced in slice() before any attempt,
    # and folded into the ESCALATE Outcome — never auto-fired by the engine
    sm4 = SemanticMap()
    sm4.register_context(ContextPrimitive("ctx4", "Test4"))
    sm4.register_transition(TransitionPrimitive(
        "hard_delete", "Hard delete", "ctx4", "reviewed", "deleted",
        requires_human_authorization=True, safe_alternatives=["archive"],
    ))
    sm4.register_transition(TransitionPrimitive(
        "archive", "Archive instead", "ctx4", "reviewed", "archived",
    ))
    engine4 = ThinkingMapTraversal(sm4)
    s4 = engine4.build_active_state(RuntimeBinding(active_context_id="ctx4"), current_state="reviewed")

    sl4 = s4.slice("hard_delete")
    assert sl4["move"]["safe_alternatives"] == ["archive"], sl4["move"]
    assert sl4["move"]["previously_denied"] is None

    o5 = engine4.attempt_transition(s4, "hard_delete")
    assert o5.kind == OutcomeKind.ESCALATE
    assert o5.alternatives == ["archive"], o5.alternatives

    # human says no — recorded, not a void; pending clears, denial doesn't
    # block a later change of mind, and the alternative is still just sitting
    # there as an ordinary transition for the model to choose on its own
    s4.deny_pending_authorization("hard_delete", reason="not urgent enough, archive instead")
    assert s4.pending_authorizations == set()
    assert s4.denied_authorizations["hard_delete"] == "not urgent enough, archive instead"

    o6 = engine4.attempt_transition(s4, "archive")
    assert o6.kind == OutcomeKind.CONTINUE, f"Expected CONTINUE, got {o6.kind}"
    assert s4.current_state == "archived"

    # a retry after denial names the history — not silently re-asked as fresh
    sm5 = SemanticMap()
    sm5.register_context(ContextPrimitive("ctx5", "Test5"))
    sm5.register_transition(TransitionPrimitive(
        "hard_delete", "Hard delete", "ctx5", "reviewed", "deleted",
        requires_human_authorization=True,
    ))
    engine5 = ThinkingMapTraversal(sm5)
    s5 = engine5.build_active_state(RuntimeBinding(active_context_id="ctx5"), current_state="reviewed")
    s5.deny_pending_authorization("hard_delete", reason="no")
    o7 = engine5.attempt_transition(s5, "hard_delete")
    assert o7.kind == OutcomeKind.ESCALATE
    assert "previously denied" in o7.reason and "no" in o7.reason, o7.reason
    # but a later authorized=True still fires — denial isn't permanent
    o8 = engine5.attempt_transition(s5, "hard_delete", authorized=True)
    assert o8.kind == OutcomeKind.CONTINUE


def check_authorization_receipt():
    """AuthorizationReceipt: approval scoped to one transition + one inspected
    state, not an ambient boolean — closes the TOCTOU gap named but explicitly
    left untested in the 2026-07-21 Ignition Lock wind-tunnel writeup:
    inspect state A, get a receipt for A, let other moves carry the traversal
    to state B, then try to spend A's receipt against B."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx", "draft", "published",
        requires_human_authorization=True,
    ))
    sm.register_transition(TransitionPrimitive(
        "edit", "Edit draft", "ctx", "draft", "draft",
    ))
    engine = ThinkingMapTraversal(sm)
    b = RuntimeBinding(active_context_id="ctx", current_evidence=["v1"])
    s = engine.build_active_state(b, current_state="draft")

    # wrong transition: a receipt minted for a different move is rejected,
    # not silently accepted because *some* human said yes to *something*
    receipt_for_edit = issue_authorization_receipt(s, "edit", request_id="req-1")
    o_wrong = engine.attempt_transition(s, "publish", authorization=receipt_for_edit)
    assert o_wrong.kind == OutcomeKind.ESCALATE, o_wrong.kind
    assert "issued for 'edit'" in o_wrong.reason, o_wrong.reason
    assert s.current_state == "draft"

    # TOCTOU: receipt issued while inspecting the current state, then the
    # model edits the draft (state moves) before the receipt is spent —
    # the fingerprint no longer matches, receipt must be refused
    receipt_stale = issue_authorization_receipt(s, "publish", request_id="req-2")
    s.binding.current_evidence.append("v2")  # evidence changed since inspection
    o_toctou = engine.attempt_transition(s, "publish", authorization=receipt_stale)
    assert o_toctou.kind == OutcomeKind.ESCALATE, o_toctou.kind
    assert "state has changed" in o_toctou.reason, o_toctou.reason
    assert s.current_state == "draft"
    assert "req-2" not in s.consumed_authorizations

    # happy path: receipt issued against the state as it actually is right
    # now fires cleanly
    receipt_ok = issue_authorization_receipt(s, "publish", request_id="req-3")
    o_ok = engine.attempt_transition(s, "publish", authorization=receipt_ok)
    assert o_ok.kind == OutcomeKind.CONTINUE, o_ok.reason
    assert s.current_state == "published"
    assert "req-3" in s.consumed_authorizations

    # replay: the exact same receipt, presented again, is refused — the
    # decision it represents has already been spent
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("ctx2", "Test2"))
    sm2.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx2", "draft", "published",
        requires_human_authorization=True,
    ))
    sm2.register_transition(TransitionPrimitive(
        "unpublish", "Unpublish", "ctx2", "published", "draft",
    ))
    engine2 = ThinkingMapTraversal(sm2)
    s2 = engine2.build_active_state(RuntimeBinding(active_context_id="ctx2"), current_state="draft")
    receipt_replay = issue_authorization_receipt(s2, "publish", request_id="req-4")
    assert engine2.attempt_transition(s2, "publish", authorization=receipt_replay).kind == OutcomeKind.CONTINUE
    engine2.attempt_transition(s2, "unpublish")
    # back to draft with the exact same fingerprint the old receipt was cut
    # against — expiry alone wouldn't catch this, only consumption tracking does
    o_replay = engine2.attempt_transition(s2, "publish", authorization=receipt_replay)
    assert o_replay.kind == OutcomeKind.ESCALATE, o_replay.kind
    assert "already consumed" in o_replay.reason, o_replay.reason

    # expiry: a receipt outlives its ttl_steps even though nothing else
    # about the state changed
    sm3 = SemanticMap()
    sm3.register_context(ContextPrimitive("ctx3", "Test3"))
    sm3.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx3", "draft", "published",
        requires_human_authorization=True,
    ))
    engine3 = ThinkingMapTraversal(sm3)
    s3 = engine3.build_active_state(RuntimeBinding(active_context_id="ctx3"), current_state="draft")
    receipt_ttl = issue_authorization_receipt(s3, "publish", request_id="req-5", ttl_steps=0)
    engine3.step(s3)  # advances step_count past expires_at_step
    o_expired = engine3.attempt_transition(s3, "publish", authorization=receipt_ttl)
    assert o_expired.kind == OutcomeKind.ESCALATE, o_expired.kind
    assert "expired" in o_expired.reason, o_expired.reason

    # no bypass: transition_to() called directly re-verifies too, same as
    # the authorized= boolean already does
    sm4 = SemanticMap()
    sm4.register_context(ContextPrimitive("ctx4", "Test4"))
    sm4.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx4", "draft", "published",
        requires_human_authorization=True,
    ))
    engine4 = ThinkingMapTraversal(sm4)
    s4 = engine4.build_active_state(RuntimeBinding(active_context_id="ctx4"), current_state="draft")
    mismatched_receipt = AuthorizationReceipt(
        transition_id="publish",
        state_fingerprint="sha256:not-the-real-one",
        request_id="req-6",
        issued_at_step=0,
        expires_at_step=99,
    )
    assert s4.transition_to("publish", authorization=mismatched_receipt) is False
    assert s4.current_state == "draft"

    # legacy authorized=True is untouched by any of the above
    sm5 = SemanticMap()
    sm5.register_context(ContextPrimitive("ctx5", "Test5"))
    sm5.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx5", "draft", "published",
        requires_human_authorization=True,
    ))
    engine5 = ThinkingMapTraversal(sm5)
    s5 = engine5.build_active_state(RuntimeBinding(active_context_id="ctx5"), current_state="draft")
    o_legacy = engine5.attempt_transition(s5, "publish", authorized=True)
    assert o_legacy.kind == OutcomeKind.CONTINUE, o_legacy.kind

    # compute_state_fingerprint is deterministic and evidence-order-independent
    b6 = RuntimeBinding(active_context_id="ctx6", current_evidence=["a", "b"])
    s6a = ActiveState(semantic_map=SemanticMap(), binding=b6, current_state="x")
    b6b = RuntimeBinding(active_context_id="ctx6", current_evidence=["b", "a"])
    s6b = ActiveState(semantic_map=SemanticMap(), binding=b6b, current_state="x")
    assert compute_state_fingerprint(s6a) == compute_state_fingerprint(s6b)

    # round-trip TOCTOU: found via adversarial testing (2026-07-23), not
    # design review. Two receipts issued back-to-back against the SAME
    # pre-fire state; one fires (consuming itself), an unrelated transition
    # brings the traversal back to a state with an IDENTICAL fingerprint
    # (same context, current_state, evidence) purely through
    # attempt_transition() calls -- zero step() calls anywhere in between.
    # A stale, never-consumed second receipt issued against the original
    # state must not be spendable just because the fingerprint coincidentally
    # matches again -- this is exactly why expiry is bound to
    # _authorization_clock (ticks on every fire too) and not step_count
    # (ticks only on step()).
    sm7 = SemanticMap()
    sm7.register_context(ContextPrimitive("ctx7", "Test7"))
    sm7.register_transition(TransitionPrimitive(
        "publish", "Publish", "ctx7", "draft", "published",
        requires_human_authorization=True,
    ))
    sm7.register_transition(TransitionPrimitive(
        "unpublish", "Unpublish", "ctx7", "published", "draft",
    ))
    engine7 = ThinkingMapTraversal(sm7)
    s7 = engine7.build_active_state(RuntimeBinding(active_context_id="ctx7"), current_state="draft")
    r1 = issue_authorization_receipt(s7, "publish", request_id="req-round-a")
    r2 = issue_authorization_receipt(s7, "publish", request_id="req-round-b")
    assert engine7.attempt_transition(s7, "publish", authorization=r1).kind == OutcomeKind.CONTINUE
    assert engine7.attempt_transition(s7, "unpublish").kind == OutcomeKind.CONTINUE
    assert s7.step_count == 0, "this scenario must never call step() -- that's the whole point"
    o_round_trip = engine7.attempt_transition(s7, "publish", authorization=r2)
    assert o_round_trip.kind == OutcomeKind.ESCALATE, (
        f"a stale receipt must not reawaken after a fingerprint-identical "
        f"round trip achieved purely through fires, got {o_round_trip.kind}"
    )
    assert "expired" in o_round_trip.reason, o_round_trip.reason
    assert s7.current_state == "draft"


def check_pending_input_await():
    """PendingInput/AWAIT: distinguishes "done" (IDLE) from "waiting on

    something outside the map" (AWAIT) — the same visibility fix ADV-08
    forced for pending_authorizations, applied to external dependencies
    instead of human decisions."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive("t_a", "A", "ctx", "start", "mid"))
    engine = ThinkingMapTraversal(sm)

    # regression: a map that never declares pending_inputs behaves exactly
    # as before — plain IDLE, never AWAIT, when truly at rest
    b0 = RuntimeBinding(active_context_id="ctx")
    s0 = engine.build_active_state(b0, current_state="mid")
    o0 = engine.step(s0)
    assert o0.kind == OutcomeKind.IDLE, o0.kind
    assert o0.pending_input_ids == [] and o0.wake_conditions == []

    # unresolved pending input, nothing else actionable -> AWAIT, not IDLE
    pi = PendingInput(
        input_id="dep-analysis", label="Dependency analysis",
        status=PendingInputStatus.PENDING,
        expected_evidence_ids=["dependency_report"],
        wake_conditions=["dependency_report received", "dep-analysis failed"],
    )
    b1 = RuntimeBinding(active_context_id="ctx", pending_inputs=[pi])
    s1 = engine.build_active_state(b1, current_state="mid")
    o1 = engine.step(s1)
    assert o1.kind == OutcomeKind.AWAIT, o1.kind
    assert o1.pending_input_ids == ["dep-analysis"], o1.pending_input_ids
    assert o1.wake_conditions == ["dependency_report received", "dep-analysis failed"]
    assert any("dep-analysis" in w for w in o1.warnings), o1.warnings

    # expected/received evidence is never auto-added to current_evidence —
    # a PendingInput records an expectation, it doesn't manufacture proof
    assert "dependency_report" not in s1.available_evidence_ids
    pi.status = PendingInputStatus.RECEIVED
    assert "dependency_report" not in s1.available_evidence_ids
    # and once resolved, it drops out of the unresolved view and AWAIT clears
    o1b = engine.step(s1)
    assert o1b.kind == OutcomeKind.IDLE, o1b.kind

    # candidate action elsewhere still wins over AWAIT — pending input must
    # not hide an available move
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("ctx2", "Test2"))
    engine2 = ThinkingMapTraversal(sm2)
    b2 = RuntimeBinding(
        active_context_id="ctx2", candidate_actions=["do_thing"],
        pending_inputs=[PendingInput(input_id="p2", status=PendingInputStatus.EXPECTED)],
    )
    s2 = engine2.build_active_state(b2, current_state="mid")
    o2 = engine2.step(s2)
    assert o2.kind == OutcomeKind.CONTINUE, o2.kind

    # bridge elsewhere still wins over AWAIT too
    sm3 = SemanticMap()
    sm3.register_context(ContextPrimitive(
        context_id="ctx3", label="Test3",
        bridges_to=[ContextBridge(target_context_id="ctx3b")],
    ))
    sm3.register_context(ContextPrimitive(context_id="ctx3b", label="Test3b"))
    sm3.register_transition(TransitionPrimitive("t_b", "B entry", "ctx3b", "ready", "active"))
    engine3 = ThinkingMapTraversal(sm3)
    b3 = RuntimeBinding(
        active_context_id="ctx3",
        pending_inputs=[PendingInput(input_id="p3", status=PendingInputStatus.EXPECTED)],
    )
    s3 = engine3.build_active_state(b3, current_state="mid")
    o3 = engine3.step(s3)
    assert o3.kind == OutcomeKind.BRIDGE, o3.kind

    # to_llm_prompt_state() surfaces only unresolved entries, in the compact
    # shape the spec calls for — not source_ref, not resolved history
    prompt = s1.to_llm_prompt_state()
    assert prompt["pending_inputs"] == [], "already-resolved input must not appear"

    b4 = RuntimeBinding(active_context_id="ctx", pending_inputs=[pi, PendingInput(
        input_id="dep-2", label="Second dep", status=PendingInputStatus.EXPECTED,
        wake_conditions=["dep-2 received"],
    )])
    s4 = engine.build_active_state(b4, current_state="mid")
    prompt4 = s4.to_llm_prompt_state()
    assert prompt4["pending_inputs"] == [
        {
            "id": "dep-2", "label": "Second dep", "status": "expected",
            "expected_evidence": [], "wake_conditions": ["dep-2 received"],
        },
    ], prompt4["pending_inputs"]


def check_move_intent():
    """MoveIntent/inspect_move: a concrete proposed move, distinct from its

    transition type — TransitionPrimitive is the reusable "publish", a
    MoveIntent is one specific proposal to fire it (which artifact, which
    audience, requested by whom). inspect_move() evaluates one without
    firing; attempt_transition()/transition_to() stamp its identity into
    MoveTrace only when it actually fires and only when it names the
    transition that actually fired."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("ctx", "Test"))
    sm.register_transition(TransitionPrimitive("publish", "Publish", "ctx", "verified", "published"))
    sm.register_transition(TransitionPrimitive("archive", "Archive", "ctx", "verified", "archived"))
    engine = ThinkingMapTraversal(sm)
    s = engine.build_active_state(RuntimeBinding(active_context_id="ctx"), current_state="verified")

    intent = MoveIntent(
        move_id="move-019", transition_id="publish",
        parameters={"artifact": "report-v3", "audience": "public"},
        binding_revision=12,
    )

    # inspect_move() never mutates state — same current_state, and calling
    # it repeatedly while the model revises parameters is always safe
    step_count_before = s.step_count
    o1 = engine.inspect_move(s, intent)
    assert o1.kind == OutcomeKind.CONTINUE, o1.kind
    assert s.current_state == "verified", "inspect_move must not fire anything"
    assert s.step_count == step_count_before + 1, (
        "inspect_move is step()-scoped — it increments step_count exactly "
        "like any other inspection, nothing more"
    )
    o2 = engine.inspect_move(s, intent)
    assert s.current_state == "verified", "a second inspection must still not fire"

    # move_intent surfaces in the slice, compact, exactly as declared
    assert o2.llm_prompt_state["move_intent"] == {
        "move_id": "move-019", "transition_id": "publish",
        "parameters": {"artifact": "report-v3", "audience": "public"},
    }, o2.llm_prompt_state["move_intent"]

    # firing with intent stamps MoveTrace — the model's identity for this
    # specific proposal survives into the trace, not just the bare
    # transition_id every other attempt would also produce
    o3 = engine.attempt_transition(s, "publish", intent=intent)
    assert o3.kind == OutcomeKind.CONTINUE, o3.kind
    assert s.current_state == "published"
    assert s.trace.move_id == "move-019", s.trace
    assert s.trace.last_transition_id == "publish"
    assert o3.warnings == [], "a matching intent must not spuriously warn"

    # parent_move_id lineage carries through the same way
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("ctx2", "Test2"))
    sm2.register_transition(TransitionPrimitive("publish", "Publish", "ctx2", "verified", "published"))
    engine2 = ThinkingMapTraversal(sm2)
    s2 = engine2.build_active_state(RuntimeBinding(active_context_id="ctx2"), current_state="verified")
    intent_revised = MoveIntent(
        move_id="move-020", transition_id="publish",
        parameters={"artifact": "report-v4", "audience": "regulator-y"},
        parent_move_id="move-019",
    )
    engine2.attempt_transition(s2, "publish", intent=intent_revised)
    assert s2.trace.move_id == "move-020"
    assert s2.trace.parent_move_id == "move-019"

    # regression: a bare transition_id call, no intent at all, behaves
    # exactly as it did before MoveIntent existed
    sm3 = SemanticMap()
    sm3.register_context(ContextPrimitive("ctx3", "Test3"))
    sm3.register_transition(TransitionPrimitive("publish", "Publish", "ctx3", "verified", "published"))
    engine3 = ThinkingMapTraversal(sm3)
    s3 = engine3.build_active_state(RuntimeBinding(active_context_id="ctx3"), current_state="verified")
    o4 = engine3.attempt_transition(s3, "publish")
    assert o4.kind == OutcomeKind.CONTINUE
    assert s3.trace.move_id is None and s3.trace.parent_move_id is None

    # mismatched intent: naming a transition other than the one that
    # actually fired is not stamped into trace (would corrupt lineage with
    # an unrelated move's identity) — and, since intent carries no
    # legality weight, it does not block the fire either
    sm4 = SemanticMap()
    sm4.register_context(ContextPrimitive("ctx4", "Test4"))
    sm4.register_transition(TransitionPrimitive("archive", "Archive", "ctx4", "verified", "archived"))
    engine4 = ThinkingMapTraversal(sm4)
    s4 = engine4.build_active_state(RuntimeBinding(active_context_id="ctx4"), current_state="verified")
    mismatched = MoveIntent(move_id="move-099", transition_id="publish")
    o5 = engine4.attempt_transition(s4, "archive", intent=mismatched)
    assert o5.kind == OutcomeKind.CONTINUE, (
        "a mismatched intent must not block an otherwise-legal fire"
    )
    assert s4.current_state == "archived"
    assert s4.trace.move_id is None, (
        f"mismatched intent must not be credited to trace, got {s4.trace.move_id!r}"
    )
    # not fully silent, though — a caller passing the wrong MoveIntent
    # object is a real bug worth surfacing, same "advise, don't hide"
    # treatment as every other advisory-only signal in this engine
    assert any("move-099" in w and "archive" in w for w in o5.warnings), o5.warnings

    # direct transition_to() stamps intent the same way attempt_transition()
    # does — this isn't wrapper-only behavior
    sm4b = SemanticMap()
    sm4b.register_context(ContextPrimitive("ctx4b", "Test4b"))
    sm4b.register_transition(TransitionPrimitive("publish", "Publish", "ctx4b", "verified", "published"))
    s4b = ThinkingMapTraversal(sm4b).build_active_state(
        RuntimeBinding(active_context_id="ctx4b"), current_state="verified",
    )
    direct_intent = MoveIntent(move_id="move-direct", transition_id="publish")
    assert s4b.transition_to("publish", intent=direct_intent) is True
    assert s4b.trace.move_id == "move-direct"

    # boundary, explicitly not fixed by this feature: two distinct
    # MoveIntents inspected at the same (context, current_state) with the
    # same evidence snapshot still read as the same stagnant visit —
    # register_visit() has no knowledge of intent.parameters at all, and
    # inspect_move() doesn't feed it any. Folding parameters into the
    # visit-key is a separate decision this feature does not make (see
    # docs/deep/DESIGN_MOVE_INTENT.md)
    sm5 = SemanticMap()
    sm5.register_context(ContextPrimitive("ctx5", "Test5"))
    sm5.register_transition(TransitionPrimitive("publish", "Publish", "ctx5", "verified", "published"))
    engine5 = ThinkingMapTraversal(sm5)
    s5 = engine5.build_active_state(RuntimeBinding(active_context_id="ctx5"), current_state="verified")
    engine5.inspect_move(s5, MoveIntent(move_id="a", transition_id="publish", parameters={"x": 1}))
    engine5.inspect_move(s5, MoveIntent(move_id="b", transition_id="publish", parameters={"x": 2}))
    assert s5.visit_count == 2, (
        "documented boundary: different MoveIntent.parameters do not reset "
        f"the stagnation counter today, got visit_count={s5.visit_count}"
    )


def check_reachability():
    """Discrete reachability over a map's declared transition graph (val.pdf ch.10).

    Worked example, both directions, using the library's own canonical
    destructive-move map (build_destructive_action_map): delete_records and
    archive_records both declare from_state="reviewed", which is nobody's
    to_state in this map — callers arrive at "reviewed" from outside (a
    dry-run happened upstream), the same shape as the case that motivated
    this module (see reachability.py's docstring for the full story: an
    unreachable-looking from_state turned out to be an intentional external
    entry point, and the "obvious" fix of merging it onto a shared from_state
    broke four behavior tests by changing what missing_evidence aggregates
    across).

    entry_states is required, not inferred, precisely so that mistake isn't
    repeatable: declaring "reviewed" as an entry point is a one-line,
    reviewable statement of intent instead of something a reachability walk
    has to guess at.
    """
    sm = build_destructive_action_map()

    # declared correctly: "reviewed" is a named entry point, nothing is
    # unreachable
    dead = unreachable_transitions(sm, entry_states={"reviewed"})
    assert not dead, f"unexpected unreachable transitions: {[t.transition_id for t in dead]}"

    # omit the entry point on purpose: the check's whole job is to make an
    # undeclared entry point loud, not to silently let it through. All three
    # transitions rooted at "reviewed" must come back.
    undeclared = unreachable_transitions(sm, entry_states=set())
    undeclared_ids = {t.transition_id for t in undeclared}
    assert undeclared_ids == {"delete_records", "archive_records", "log_status"}, undeclared_ids

    # a genuinely orphaned transition — from_state nobody produces and
    # nobody declared as an entry point — must still be caught even when a
    # real entry point is declared correctly
    sm2 = build_destructive_action_map()
    sm2.register_transition(TransitionPrimitive(
        transition_id="orphan_move",
        label="Unreachable by construction — nothing produces 'nowhere'",
        context_id="data_ops",
        from_state="nowhere",
        to_state="deleted",
    ))
    orphaned = unreachable_transitions(sm2, entry_states={"reviewed"})
    assert [t.transition_id for t in orphaned] == ["orphan_move"], (
        [t.transition_id for t in orphaned]
    )
    assert orphaned[0].requires_human_authorization is False, (
        "orphan_move isn't gated — reachability catches dead transitions "
        "regardless of whether they happen to be destructive; it is not a "
        "substitute for requires_human_authorization, it is a separate check "
        "on a separate property (can the graph get here at all)"
    )


def check_route_gated_transition():
    """guard_expression -> DecisionRule: routing-policy legality, agentic

    not human-facing. A transition naming a DecisionRule via
    guard_expression only fires when that rule's current recommendation
    matches the attempted transition_id — mismatches return REVISE_PLAN
    (never ESCALATE: no human is asked, nothing is added to
    pending_authorizations) with the rule's actual recommendation in
    alternatives, so an agentic caller retries in the same turn, inside
    the map's own vocabulary."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("cis", "Compound Intelligence Stack"))
    sm.register_transition(TransitionPrimitive(
        "route_local", "route to local/open tier", "cis",
        "control_plane", "local_open", guard_expression="escalation_policy",
    ))
    sm.register_transition(TransitionPrimitive(
        "route_frontier", "escalate to frontier oracle", "cis",
        "control_plane", "frontier", guard_expression="escalation_policy",
    ))

    logic = LogicLayer()
    logic.add_rule(DecisionRule(
        name="escalation_policy", condition=RiskAbove("high"),
        action_if_true="route_frontier", action_if_false="route_local",
        explanation="routine load stays local; frontier is the rare escalation",
        kind=RuleKind.ROUTE,
    ))
    engine = ThinkingMapTraversal(sm, logic_layer=logic)

    # normal risk: policy recommends route_local. Attempting the
    # mismatched transition does not fire it, and — the whole point —
    # does not touch pending_authorizations the way an ESCALATE would.
    s_normal = engine.build_active_state(
        RuntimeBinding(active_context_id="cis", risk_level="normal"),
        current_state="control_plane",
    )
    o_mismatch = engine.attempt_transition(s_normal, "route_frontier")
    assert o_mismatch.kind == OutcomeKind.REVISE_PLAN, o_mismatch.kind
    assert o_mismatch.kind != OutcomeKind.ESCALATE, (
        "a routing-policy mismatch must never read as 'needs a human'"
    )
    assert o_mismatch.alternatives == ["route_local"], o_mismatch.alternatives
    assert "escalation_policy" in o_mismatch.reason
    assert s_normal.current_state == "control_plane", "mismatch must not move state"
    assert s_normal.pending_authorizations == set(), (
        "REVISE_PLAN is not an authorization ask — nothing pending for a human"
    )

    # the matching transition at the same state fires normally
    o_match = engine.attempt_transition(s_normal, "route_local")
    assert o_match.kind == OutcomeKind.CONTINUE, o_match.kind
    assert s_normal.current_state == "local_open"

    # high risk: policy now recommends route_frontier instead. Attempting
    # the now-wrong default gets REVISE_PLAN naming the correct one —
    # and the caller can retry it immediately, autonomously, same turn.
    s_high = engine.build_active_state(
        RuntimeBinding(active_context_id="cis", risk_level="high"),
        current_state="control_plane",
    )
    o_wrong_tier = engine.attempt_transition(s_high, "route_local")
    assert o_wrong_tier.kind == OutcomeKind.REVISE_PLAN, o_wrong_tier.kind
    assert o_wrong_tier.alternatives == ["route_frontier"], o_wrong_tier.alternatives
    assert s_high.current_state == "control_plane"

    o_retry = engine.attempt_transition(s_high, o_wrong_tier.alternatives[0])
    assert o_retry.kind == OutcomeKind.CONTINUE, (
        "the model's own retry, using exactly what REVISE_PLAN handed back, "
        f"must succeed — got {o_retry.kind}"
    )
    assert s_high.current_state == "frontier"

    # dangling reference / no logic_layer bound: same silent no-op as an
    # unresolved required_gate_id — backward compatible with maps that
    # never opted into routing policy at all
    sm2 = SemanticMap()
    sm2.register_context(ContextPrimitive("cis2", "Test"))
    sm2.register_transition(TransitionPrimitive(
        "t_a", "A", "cis2", "start", "mid", guard_expression="no_such_rule",
    ))
    engine_no_logic = ThinkingMapTraversal(sm2)  # no logic_layer at all
    s2 = engine_no_logic.build_active_state(
        RuntimeBinding(active_context_id="cis2"), current_state="start",
    )
    o2 = engine_no_logic.attempt_transition(s2, "t_a")
    assert o2.kind == OutcomeKind.CONTINUE, (
        f"a dangling guard_expression with no bound logic_layer must not "
        f"block — got {o2.kind}"
    )


def check_typed_assurance_scope():
    slice_a = ContextSlice(
        reference_scheme="runtime.v1",
        selector_schema=("tenant", "region"),
        selectors={"tenant": "alpha", "region": "eu"},
    )
    slice_b = ContextSlice(
        reference_scheme="runtime.v1",
        selector_schema=("tenant", "region"),
        selectors={"tenant": "beta", "region": "eu"},
    )
    scope = ClaimScope(
        "alpha-eu",
        [slice_a],
        interpretation_basis_ref="runtime-scope-scheme-v1",
    )
    assert scope.evaluate_membership(slice_a) == MembershipJudgment.TRUE
    assert scope.evaluate_membership(slice_b) == MembershipJudgment.FALSE
    assert scope.evaluate_membership(
        slice_a, interpretation_available=False,
    ) == MembershipJudgment.UNKNOWN
    scope_b = ClaimScope(
        "beta-eu", [slice_b], interpretation_basis_ref="runtime-scope-scheme-v1",
    )
    try:
        ClaimScope.span_union([scope, scope_b], "both", independence_basis_ref="")
        raise AssertionError("SpanUnion without an independence basis must fail")
    except ValueError:
        pass
    combined = ClaimScope.span_union(
        [scope, scope_b],
        "both",
        independence_basis_ref="independent-tenant-lines-v1",
    )
    assert combined.contains(slice_a) and combined.contains(slice_b)
    assert "independent-tenant-lines-v1" in combined.support_basis_refs

    path = ReliabilityPath(
        "path-1",
        spine_reliabilities=[0.95, 0.8],
        congruence_penalties=[0.1],
    )
    fgr = FGR(
        FormalityLevel.F6,
        scope,
        reliability=0.99,
        reliability_paths=[path],
    )
    assert fgr.is_structurally_typed
    assert fgr.formality_ratio == FormalityLevel.F6.normalized
    assert abs(fgr.effective_reliability - 0.7) < 1e-9

    legacy = FGR(0.8, 0.6, 0.9)
    assert not legacy.is_structurally_typed
    assert legacy.sufficient(0.7, 0.8)

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("scope-ctx", "Scope"))
    sm.register_evidence(EvidencePrimitive(
        "scoped-evidence", "Scoped", "scope-ctx", fgr=fgr,
    ))
    sm.register_transition(TransitionPrimitive(
        "in-scope", "In scope", "scope-ctx", "start", "done",
        required_evidence=["scoped-evidence"], scope_target=slice_a,
    ))
    sm.register_transition(TransitionPrimitive(
        "out-of-scope", "Out of scope", "scope-ctx", "start", "done",
        required_evidence=["scoped-evidence"], scope_target=slice_b,
    ))
    engine = ThinkingMapTraversal(sm)
    outside_state = engine.build_active_state(RuntimeBinding(
        active_context_id="scope-ctx", current_evidence=["scoped-evidence"],
    ), current_state="start")
    outside = engine.attempt_transition(outside_state, "out-of-scope")
    assert outside.kind == OutcomeKind.ABSTAIN
    assert "does not cover" in outside.reason
    assert not outside_state.transition_to("out-of-scope")

    inside_state = engine.build_active_state(RuntimeBinding(
        active_context_id="scope-ctx", current_evidence=["scoped-evidence"],
    ), current_state="start")
    inside = engine.attempt_transition(inside_state, "in-scope")
    assert inside.kind == OutcomeKind.CONTINUE


def check_work_attribution_relation():
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("work-ctx", "Work"))
    sm.register_role(RolePrimitive("operator", "Operator", "work-ctx"))
    sm.register_role_assignment(RoleAssignment(
        "assign-op", "system-1", "operator", "work-ctx",
    ))
    sm.register_work(WorkPrimitive(
        "work-good", "Run", "work-ctx",
        performed_under="assign-op",
        performed_by="system-1",
    ))
    sm.register_work(WorkPrimitive(
        "work-wrong-holder", "Run", "work-ctx",
        performed_under="assign-op",
        performed_by="system-2",
    ))
    assert sm.validate_work_attribution("work-good") == []
    assert "differs from assignment holder" in " ".join(
        sm.validate_work_attribution("work-wrong-holder")
    )

    invalid_map = SemanticMap()
    invalid_map.register_context(ContextPrimitive("invalid-work", "Invalid Work"))
    invalid_map.register_role(RolePrimitive("operator", "Operator", "invalid-work"))
    invalid_map.register_role_assignment(RoleAssignment(
        "assignment", "system-1", "operator", "invalid-work",
    ))
    invalid_map.register_work(WorkPrimitive(
        "wrong-work", "Wrong", "invalid-work",
        performed_under="assignment",
        performed_by="system-2",
    ))
    invalid_map.register_transition(TransitionPrimitive(
        "finish", "Finish", "invalid-work", "running", "report_done",
    ))
    invalid_state = ActiveState(
        invalid_map,
        RuntimeBinding(active_context_id="invalid-work"),
        current_state="running",
    )
    allowed, results = GuardEngine().is_action_allowed(invalid_state, "finish")
    assert not allowed
    assert any(
        result.guard_name == "planning_not_enactment"
        and result.verdict == GuardVerdict.DENY
        for result in results
    )


def check_call_plan_closure():
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("tools", "Tools"))
    sm.register_transition(TransitionPrimitive(
        "run_tools", "Run tools", "tools", "start", "done",
        tool_calls=["repo.inspect", "tests.run"],
        call_plan_id="plan-1",
    ))
    engine = ThinkingMapTraversal(sm)
    state = engine.build_active_state(
        RuntimeBinding(active_context_id="tools"), current_state="start",
    )
    inspected_missing = engine.step(state, transition_id="run_tools")
    assert inspected_missing.kind == OutcomeKind.REVISE_PLAN
    missing = engine.attempt_transition(state, "run_tools")
    assert missing.kind == OutcomeKind.REVISE_PLAN
    assert state.current_state == "start"

    sm.register_call_plan(CallPlanPrimitive(
        plan_id="plan-1",
        objective="inspect, patch, and verify",
        context_id="tools",
        route_refs_in_order=["repo.inspect", "tests.run"],
        budget=BudgetEnvelope(
            time_limit=60,
            compute_limit=2,
            cost_limit=5,
            risk_ceiling="normal",
        ),
        stop_conditions=["tests pass"],
        replan_conditions=["same failure repeats twice"],
        next_planned_transition_id="run_tools",
        policy_ref="tool-policy-v1",
        choice_result_ref="choice-run-tools-v1",
    ))
    assert state.slice("run_tools")["agentic_controls"]["call_plan"]["ok"]
    fired = engine.attempt_transition(state, "run_tools")
    assert fired.kind == OutcomeKind.CONTINUE
    assert state.current_state == "done"


def check_autonomy_budget_enforcement():
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("auto", "Autonomy"))
    sm.register_role(RolePrimitive(
        "navigator", "Navigator", "auto", agency_level=AgencyLevel.AUTONOMOUS,
    ))
    sm.register_role(RolePrimitive("supervisor", "Supervisor", "auto"))
    sm.register_role_assignment(RoleAssignment(
        "nav-assignment", "robot-7", "navigator", "auto",
    ))
    sm.register_gate(GatePrimitive(
        "auto-gate", "Autonomy Gate", "auto",
        checks=[GateCheck("safe", "Safety evidence", ["safe-envelope"])],
    ))
    scope = ClaimScope(
        "warehouse-zone-a",
        [ContextSlice(
            "warehouse-v1", ("zone",), {"zone": "A"},
        )],
        interpretation_basis_ref="warehouse-scope-v1",
    )
    sm.register_autonomy_budget(AutonomyBudgetDecl(
        budget_id="nav-budget",
        version="1",
        context_id="auto",
        scope=scope,
        consumer_role_id="navigator",
        action_limit=1,
        decision_limit=2,
        risk_ceiling="normal",
        admissibility_gate_id="auto-gate",
        override_protocol_ref="nav-override-v1",
        override_role_ids=["supervisor"],
    ))
    for transition_id, source, target in (
        ("move-1", "start", "mid"),
        ("move-2", "mid", "end"),
    ):
        sm.register_transition(TransitionPrimitive(
            transition_id, transition_id, "auto", source, target,
            requires_autonomy_budget_id="nav-budget",
            action_token_cost=1,
            decision_token_cost=1,
            scope_target=scope.extension[0],
        ))
    engine = ThinkingMapTraversal(sm)
    paused_state = engine.build_active_state(RuntimeBinding(
        actor="robot-7",
        active_context_id="auto",
        current_evidence=["safe-envelope"],
        paused_autonomy_budget_ids=["nav-budget"],
    ), current_state="start")
    paused = engine.attempt_transition(paused_state, "move-1")
    assert paused.kind == OutcomeKind.ESCALATE
    assert "paused" in paused.reason
    assert paused_state.current_state == "start"

    state = engine.build_active_state(RuntimeBinding(
        actor="robot-7",
        active_context_id="auto",
        current_evidence=["safe-envelope"],
    ), current_state="start")

    first = engine.attempt_transition(state, "move-1")
    assert first.kind == OutcomeKind.CONTINUE
    assert len(state.autonomy_ledger) == 1
    assert state.autonomy_usage("nav-budget")["actions"] == 1

    inspected_depleted = engine.step(state, transition_id="move-2")
    assert inspected_depleted.kind == OutcomeKind.ESCALATE
    depleted = engine.attempt_transition(state, "move-2")
    assert depleted.kind == OutcomeKind.ESCALATE
    assert "depleted" in depleted.reason
    assert state.current_state == "mid"
    assert len(state.autonomy_ledger) == 1


def check_agentic_guards_are_opt_in():
    """F.6 and E.16 must not rewrite legality for pre-existing maps."""
    legacy = SemanticMap()
    legacy.register_context(ContextPrimitive("legacy", "Legacy"))
    legacy.register_role(RolePrimitive(
        "legacy-agent", "Legacy agent", "legacy",
        agency_level=AgencyLevel.AUTONOMOUS,
    ))
    legacy.register_work(WorkPrimitive(
        "legacy-work", "Legacy work", "legacy", performed_under=None,
    ))
    legacy.register_transition(TransitionPrimitive(
        "legacy-finish", "Finish", "legacy", "running", "task_done",
    ))
    legacy_engine = ThinkingMapTraversal(legacy)
    legacy_state = legacy_engine.build_active_state(RuntimeBinding(
        active_context_id="legacy", actor_role_ids=["legacy-agent"],
    ), current_state="running")

    allowed, results = GuardEngine().is_action_allowed(legacy_state, "legacy-finish")
    assert allowed, [result.reason for result in results]
    assert legacy_state.autonomy_budget_status("legacy-finish")[0]
    assert legacy_engine.attempt_transition(
        legacy_state, "legacy-finish",
    ).kind == OutcomeKind.CONTINUE

    # The explicit transition reference, not AgencyLevel, activates E.16.
    explicit = SemanticMap()
    explicit.register_context(ContextPrimitive("explicit", "Explicit"))
    explicit.register_transition(TransitionPrimitive(
        "budgeted", "Budgeted", "explicit", "start", "end",
        requires_autonomy_budget_id="missing-budget",
    ))
    explicit_state = ActiveState(
        explicit, RuntimeBinding(active_context_id="explicit"), "start",
    )
    allowed_explicit, explicit_results = GuardEngine().is_action_allowed(
        explicit_state, "budgeted",
    )
    assert not allowed_explicit
    assert any(
        result.guard_name == "autonomy_budget"
        and "not registered" in result.reason
        for result in explicit_results
    )


def check_gate_lattice_and_typed_cause():
    """A.21 maximum join, reachable BLOCK, and compatibility proposition."""
    positional = Outcome(OutcomeKind.ABSTAIN, "legacy", "next-state")
    assert positional.next_state == "next-state" and positional.cause is None

    block_gate = GatePrimitive(
        "hard-gate", "Hard gate", "gates",
        checks=[
            GateCheck("ordinary", "Ordinary pass", []),
            GateCheck(
                "safety", "Safety must be evidenced", ["safety-clear"],
                failure_decision=GateDecision.BLOCK,
            ),
        ],
    )
    assert block_gate.checks[1].evaluate(set()) == GateDecision.BLOCK
    assert block_gate.evaluate(set()) == GateDecision.BLOCK
    try:
        GateCheck(
            "invalid", "Missing evidence cannot mean pass", ["evidence"],
            failure_decision=GateDecision.PASS,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("failure_decision=PASS must be rejected")

    # Compatibility-visible case: the correct maximal join changes the old
    # ABSTAIN result into DEGRADE, which is actionable with a warning.
    degraded_gate = GatePrimitive(
        "degraded-gate", "Degraded gate", "gates",
        checks=[
            GateCheck("partial", "Two facts", ["a", "b"]),
            GateCheck("absent", "One absent fact", ["c"]),
        ],
    )
    assert degraded_gate.evaluate({"a"}) == GateDecision.DEGRADE
    pass_gate = GatePrimitive(
        "pass-gate", "Pass gate", "gates",
        checks=[
            GateCheck("pass", "No requirements", []),
            GateCheck("abstain", "Unavailable", ["not-present"]),
        ],
    )
    assert pass_gate.evaluate(set()) == GateDecision.PASS

    sm = SemanticMap()
    sm.register_context(ContextPrimitive("gates", "Gates"))
    sm.register_gate(block_gate)
    sm.register_gate(GatePrimitive(
        "abstain-gate", "Abstain gate", "gates",
        checks=[GateCheck("unknown", "Unknown", ["unknown-evidence"])],
    ))
    sm.register_transition(TransitionPrimitive(
        "blocked-move", "Blocked", "gates", "start", "end",
        required_gate_id="hard-gate",
    ))
    state = ActiveState(sm, RuntimeBinding(active_context_id="gates"), "start")
    assert GateBlocked("hard-gate").evaluate(state)
    assert not GateBlocked("abstain-gate").evaluate(state)
    assert not GateBlocked("missing-gate").evaluate(state)
    assert GateAbstained("abstain-gate").evaluate(state)
    assert GateAbstained("missing-gate").evaluate(state)  # exact old behavior

    engine = ThinkingMapTraversal(sm)
    inspected = engine.step(state, transition_id="blocked-move")
    assert inspected.kind == OutcomeKind.ABSTAIN
    assert inspected.cause == OutcomeCause.GATE_BLOCK
    attempted = engine.attempt_transition(state, "blocked-move")
    assert attempted.kind == OutcomeKind.ABSTAIN
    assert attempted.cause == OutcomeCause.GATE_BLOCK
    assert attempted.to_dict()["cause"] == "gate_block"
    assert state.current_state == "start"


def check_map_validation_and_unknown_transition():
    """Validation is opt-in; explicit bad transition IDs are never CONTINUE."""
    sm = SemanticMap()
    sm.register_context(ContextPrimitive("validation", "Validation"))
    sm.register_transition(TransitionPrimitive(
        "dangling", "Dangling", "validation", "start", "end",
        required_gate_id="missing-gate", guard_expression="missing-rule",
    ))
    engine = ThinkingMapTraversal(sm)
    errors = engine.validation_errors()
    assert len(errors) == 2
    assert "unknown gate" in errors[0]
    assert "no LogicLayer" in errors[1]
    try:
        engine.validate_map()
    except MapValidationError as exc:
        assert exc.errors == tuple(errors)
    else:
        raise AssertionError("validate_map must fail closed on dangling references")

    # Existing maps are not silently switched into strict validation.
    state = engine.build_active_state(
        RuntimeBinding(active_context_id="validation"), current_state="start",
    )
    assert engine.step(state, transition_id="dangling").kind == OutcomeKind.CONTINUE

    unknown_step = engine.step(state, transition_id="typo")
    assert unknown_step.kind == OutcomeKind.ABSTAIN
    assert unknown_step.cause == OutcomeCause.UNKNOWN_TRANSITION
    assert unknown_step.to_dict()["cause"] == "unknown_transition"
    unknown_attempt = engine.attempt_transition(state, "typo")
    assert unknown_attempt.kind == OutcomeKind.ABSTAIN
    assert unknown_attempt.cause == OutcomeCause.UNKNOWN_TRANSITION

    valid = SemanticMap()
    valid.register_context(ContextPrimitive("valid", "Valid"))
    valid.register_gate(GatePrimitive("gate", "Gate", "valid", checks=[]))
    valid.register_transition(TransitionPrimitive(
        "route", "Route", "valid", "start", "end",
        required_gate_id="gate", guard_expression="route-rule",
    ))
    logic = LogicLayer()
    logic.add_rule(DecisionRule(
        "route-rule", CustomProp("always", lambda _state: True), "route",
    ))
    valid_engine = ThinkingMapTraversal(valid, logic_layer=logic)
    assert valid_engine.validation_errors() == []
    assert valid_engine.validate_map() is None


def main():
    print("FPF Thinking Map — Self-verification (horizontal)")
    print("=" * 55)

    checks = [
        ("imports", check_imports),
        ("primitives", check_primitives),
        ("state (local scoping, slice, trace)", check_state),
        ("guards (scoped, transition-focused)", check_guards),
        ("logic operators (6 truth tables)", check_logic_operators),
        ("logic layer (tags, kinds, facts/actions)", check_logic_layer),
        ("traversal (focused step, demo_walk)", check_traversal),
        ("boundary enforcement (4 findings)", check_boundary_enforcement),
        ("audit fixes (R07-R21)", check_audit_fixes),
        ("end-to-end scenario", check_end_to_end),
        ("end-to-end logic scenario", check_logic_end_to_end),
        ("horizontal properties (25 items)", check_horizontal_properties),
        ("TTL evidence decay", check_ttl_decay),
        ("stagnation counter (visit countdown)", check_stagnation_counter),
        ("IDLE outcome", check_idle_outcome),
        ("BRIDGE outcome (cross-context)", check_bridge_outcome),
        ("bridge crossing (validated writeback)", check_bridge_crossing),
        ("lean slice (no full_state bolt-on)", check_lean_slice),
        ("slice blockers (HITL)", check_slice_blockers),
        ("semantic floors (FPF vertical)", check_semantic_floors),
        ("EvidenceFresh prop + integration", check_evidence_fresh_prop),
        ("response contract (output discipline)", check_response_contract),
        ("requires_human_authorization transition (no model auto-fire)", check_requires_human_authorization),
        ("authorization receipt (scoped, non-replayable, TOCTOU-safe)", check_authorization_receipt),
        ("pending input / AWAIT (distinct from IDLE)", check_pending_input_await),
        ("move intent / inspect_move (concrete move identity)", check_move_intent),
        ("reachability (discrete graph analysis, val.pdf ch.10)", check_reachability),
        (
            "route-gated transition (guard_expression -> DecisionRule, REVISE_PLAN not ESCALATE)",
            check_route_gated_transition,
        ),
        ("typed F-G-R scope and pathwise reliability", check_typed_assurance_scope),
        ("performed-work attribution (Work -> RoleAssignment)", check_work_attribution_relation),
        ("agentic call-plan closure (C.24)", check_call_plan_closure),
        ("autonomy budget hard gate and ledger (E.16)", check_autonomy_budget_enforcement),
        ("agentic structural guards are opt-in", check_agentic_guards_are_opt_in),
        ("A.21 gate lattice, BLOCK reachability, and typed cause", check_gate_lattice_and_typed_cause),
        ("map validation and unknown transition IDs", check_map_validation_and_unknown_transition),
    ]

    passed = sum(check(name, fn) for name, fn in checks)
    total = len(checks)

    print(f"\n{'=' * 55}")
    print(f"Result: {passed}/{total} checks passed")
    print("STATUS: ALL PASS" if passed == total else "STATUS: FAILURES DETECTED")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
