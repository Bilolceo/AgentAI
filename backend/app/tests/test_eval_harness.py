"""Eval harness: smoke + TZ acceptance suites run deterministically on mock."""
from __future__ import annotations

import pytest

from app.eval.harness import ACCEPTANCE, EMERGENCY, SMOKE, Scenario, format_report, run_eval
from app.services.ai.provider import MockAIProvider


@pytest.mark.asyncio
async def test_smoke_suite_all_pass() -> None:
    results = await run_eval(MockAIProvider(), suite="smoke")
    assert len(results) == len(SMOKE) == 20
    failed = [r.name for r in results if not r.passed]
    assert not failed, f"failing: {failed}\n{format_report(results)}"


@pytest.mark.asyncio
async def test_acceptance_suite_loads_50_and_all_pass() -> None:
    assert len(ACCEPTANCE) == 50
    results = await run_eval(MockAIProvider(), suite="acceptance")
    assert len(results) == 50
    failed = [r.name for r in results if not r.passed]
    assert not failed, f"failing: {failed}\n{format_report(results)}"


@pytest.mark.asyncio
async def test_report_summary_correct() -> None:
    results = await run_eval(MockAIProvider(), suite="acceptance")
    report = format_report(results)
    assert "SUMMARY: total=50 passed=50 failed=0 pass_rate=100.0%" in report
    assert "failed: none" in report
    assert "emergency_103=3" in report


@pytest.mark.asyncio
async def test_forced_failure_appears_in_failed_list() -> None:
    # A clinic-address question deliberately mislabeled as an emergency must fail.
    bad = Scenario(
        "forced_fail", "Klinika manzili qayerda?", "uz-UZ", "clinic_info", EMERGENCY,
        must_include=("103",),
    )
    results = await run_eval(MockAIProvider(), scenarios=[bad])
    assert len(results) == 1
    assert results[0].passed is False
    assert "failed: forced_fail" in format_report(results)
