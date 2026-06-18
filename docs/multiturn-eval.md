# Multi-turn conversation eval (text pilot)

A third eval suite (`multiturn`) that tests call context across several user
messages. Unlike `smoke`/`acceptance` (single message per scenario), each
multi-turn scenario runs a whole conversation through the real
`CallSessionService`: per-turn language detection, persisted transcript context,
the full safety pipeline, the operator transfer decision engine, and callback
creation. Provider-agnostic; mock is deterministic. No telephony/STT/TTS.

## Scenario model
- `MultiTurnScenario(name, category, turns, operator_state, expected_final_action, expects_callback_task)`
- `Turn(text, expected_action, language, requires_sources, forbid_sources,
  expected_reason_code, expected_transfer_reason, expected_priority,
  expected_transfer_status, expected_callback, expected_language,
  must_include, must_not_include, unsafe_must_be_blocked, deactivate_before)`

`operator_state="busy"` forces the transfer engine to create a callback task.
`deactivate_before=("UZI",)` deactivates matching KB items before a turn (used to
prove a deactivated fact is no longer answered from the KB).

## Scenarios (15)
clinic_info_followup, price_followup (incl. uz->ru switch + unknown price
transfer), doctor_schedule_followup, safety_escalation (FAQ then diagnosis),
emergency_escalation (normal then 103), injection_midcall, operator_after_answer,
complaint_flow (high priority), angry_flow (high priority), language_switching
(uz/ru/uz), private_patient_data, negative_competitor (safe reply),
kb_deactivation, callback_creation_operator_busy (verifies a callback task row),
source_continuity (sources present on every factual turn).

## Report fields
total scenarios, passed, failed, pass_rate, total_turns, failed scenario names,
failed turn index (per scenario), transfers, emergency_103, sources_present,
unsafe_blocked, language_matches. For a failed scenario the report lists the
failing turn index and its failure reasons.

## Run (mock, deterministic)
    cd backend
    python -m app.eval.run --suite multiturn

The runner exits non-zero if any scenario fails. `--suite smoke` and
`--suite acceptance` still work unchanged.

## Run live Claude (optional, real API, billed)
    cd backend
    export AI_PROVIDER=claude
    export ANTHROPIC_API_KEY=sk-ant-...
    python -m app.eval.run --suite multiturn

As with the acceptance suite, the eval checks pipeline behavior (action,
grounding/sources, transfer reason/priority, language per turn, emergency 103,
callback creation). It does NOT judge free-text wording or fully verify factual
faithfulness; a live Claude run needs manual review. `must_include` phrases are
exact KB substrings tuned for mock mode, so treat `must_include` misses under
Claude as review prompts, not hard regressions.

## CI
Not run in CI by default (it spins up an in-memory DB per scenario, so it is
slower than the smoke eval). Run it locally before releases. It could be added
later as a small smoke subset if needed.
