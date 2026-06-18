"""Multi-turn conversation eval runs deterministically on the mock provider."""
from __future__ import annotations

import pytest

from app.eval.multiturn import (
    EMERGENCY,
    MULTITURN,
    MultiTurnScenario,
    Turn,
    format_multiturn_report,
    run_multiturn_eval,
)
from app.services.ai.provider import MockAIProvider


@pytest.mark.asyncio
async def test_suite_loads_at_least_15_scenarios() -> None:
    assert len(MULTITURN) >= 15


@pytest.mark.asyncio
async def test_multiturn_all_pass_on_mock() -> None:
    results = await run_multiturn_eval(MockAIProvider())
    assert len(results) == len(MULTITURN)
    failed = [r.name for r in results if not r.passed]
    assert not failed, f"failing: {failed}\n{format_multiturn_report(results)}"


@pytest.mark.asyncio
async def test_report_has_required_fields() -> None:
    results = await run_multiturn_eval(MockAIProvider())
    report = format_multiturn_report(results)
    assert "SUMMARY: total=15 passed=15 failed=0 pass_rate=100.0% total_turns=" in report
    assert "transfers=" in report and "emergency_103=" in report
    assert "sources_present=" in report and "unsafe_blocked=" in report
    assert "language_matches=" in report
    assert "failed: none" in report
    # the operator-busy scenario must have created a callback task
    cb = next(r for r in results if r.name == "callback_creation_operator_busy")
    assert cb.callback_tasks >= 1


@pytest.mark.asyncio
async def test_forced_failure_is_reported() -> None:
    bad = MultiTurnScenario("forced_fail", "clinic_info", [
        Turn("Klinika manzili qayerda?", EMERGENCY, must_include=("103",)),
    ], expected_final_action=EMERGENCY)
    results = await run_multiturn_eval(MockAIProvider(), scenarios=[bad])
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].first_failed_turn == 0
    assert "failed: forced_fail" in format_multiturn_report(results)
