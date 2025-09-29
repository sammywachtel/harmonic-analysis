# tests/integration/test_arbitration_policy_thresholds.py
# TODO-DELETE: This test file is incompatible with the unified pattern engine redesign.
# The arbitration logic has changed and these specific threshold tests need to be updated
# to work with the new AnalysisEnvelope and pattern-based analysis system.
# Mark for deletion after Iteration 2 when new arbitration tests are written.
import pytest
from harmonic_analysis.dto import AnalysisSummary, AnalysisType
from harmonic_analysis.services.analysis_arbitration_service import (
    AnalysisArbitrationService,
    ArbitrationPolicy,
)


def _sum(kind: str, conf: float) -> AnalysisSummary:
    return AnalysisSummary(type=AnalysisType(kind), roman_numerals=[], confidence=conf)


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_min_functional_gate_bracket():
    arb = AnalysisArbitrationService(policy=ArbitrationPolicy())
    # functional below gate => modal must win (if present)
    functional_low = _sum("functional", 0.49)
    modal_high = _sum("modal", 0.80)
    env_low = arb.arbitrate(functional_low, modal_high)
    assert env_low.primary.type == AnalysisType.MODAL

    # at the gate: decision depends on margins (no forced rejection)
    functional_at = _sum("functional", 0.50)
    env_at = arb.arbitrate(functional_at, modal_high)
    assert env_at.primary.type in (AnalysisType.FUNCTIONAL, AnalysisType.MODAL)


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_min_modal_gate_bracket():
    arb = AnalysisArbitrationService(policy=ArbitrationPolicy())
    # modal below gate => functional must win
    modal_low = _sum("modal", 0.39)
    functional_high = _sum("functional", 0.80)
    env_low = arb.arbitrate(functional_high, modal_low)
    assert env_low.primary.type == AnalysisType.FUNCTIONAL

    # at the gate: decision depends on margins (no forced rejection)
    modal_at = _sum("modal", 0.40)
    env_at = arb.arbitrate(functional_high, modal_at)
    assert env_at.primary.type in (AnalysisType.FUNCTIONAL, AnalysisType.MODAL)


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_functional_dominance_margin():
    arb = AnalysisArbitrationService(policy=ArbitrationPolicy())
    f = _sum("functional", 0.60)

    # +0.09 margin => not enough to force functional
    m_close = _sum("modal", 0.51)  # 0.60 - 0.51 = +0.09
    env_close = arb.arbitrate(f, m_close)
    assert env_close.primary.type in (AnalysisType.FUNCTIONAL, AnalysisType.MODAL)

    # +0.10 margin => functional must be primary
    m_margin = _sum("modal", 0.50)  # 0.60 - 0.50 = +0.10
    env_margin = arb.arbitrate(f, m_margin)
    assert env_margin.primary.type == AnalysisType.FUNCTIONAL


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_modal_dominance_margin():
    arb = AnalysisArbitrationService(policy=ArbitrationPolicy())
    m = _sum("modal", 0.60)

    # +0.14 margin => not enough to force modal
    f_close = _sum("functional", 0.46)  # 0.60 - 0.46 = +0.14
    env_close = arb.arbitrate(f_close, m)
    assert env_close.primary.type in (AnalysisType.FUNCTIONAL, AnalysisType.MODAL)

    # +0.15 margin => modal must be primary
    f_margin = _sum("functional", 0.45)  # 0.60 - 0.45 = +0.15
    env_margin = arb.arbitrate(f_margin, m)
    assert env_margin.primary.type == AnalysisType.MODAL


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_override_flag_default_off():
    # default policy should not apply evidence-weighted override
    arb = AnalysisArbitrationService(policy=ArbitrationPolicy())
    f = _sum("functional", 0.55)
    m = _sum("modal", 0.56)
    env = arb.arbitrate(f, m)
    assert env.primary.type in (AnalysisType.FUNCTIONAL, AnalysisType.MODAL)


@pytest.mark.skip(
    reason="TODO-DELETE: Incompatible with unified pattern engine - needs rewrite"
)
def test_override_flag_on_changes_behavior():
    # Adjust the expectation below if your policy logic differs
    policy = ArbitrationPolicy(enable_evidence_based_modal_arbitration=True)
    arb = AnalysisArbitrationService(policy=policy)
    f = _sum("functional", 0.55)
    m = _sum("modal", 0.56)
    env = arb.arbitrate(f, m)
    # With evidence-based override on, a slight modal edge is expected to select modal
    assert env.primary.type == AnalysisType.MODAL
