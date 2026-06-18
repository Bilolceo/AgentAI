# Live Claude provider + faithfulness eval

The AI provider is selected by `AI_PROVIDER`. Default is `mock` so tests, local
dev, and CI run with no API key and no network. `claude` enables the real
Anthropic provider.

## Configuration (.env)
- `AI_PROVIDER` = `mock` (default) | `claude`
- `ANTHROPIC_API_KEY` = required only when `AI_PROVIDER=claude` (never commit it)
- `CLAUDE_MODEL` = `claude-sonnet-4-6` (default)
- `AI_TIMEOUT_SECONDS` = `15`
- `AI_MAX_TOKENS` = `1024`
- `AI_TEMPERATURE` = optional; leave unset for the model default

If `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY` is missing, the app fails fast
with a clear configuration error (`RuntimeError`).

## Safety pipeline (unchanged by the provider)
1. Pre-LLM `MedicalSafetyGuardService` (input guard).
2. Provider (`MockAIProvider` or `ClaudeAIProvider`).
3. Post-LLM `SafetyReviewer` (output guard).
4. Operator transfer decision engine.

Faithfulness controls:
- Factual clinic questions are answered only when the knowledge base returns a
  match; otherwise the call is routed to an operator (no invented prices,
  schedules, doctors, or addresses).
- The Claude system prompt repeats the KB-only and medical-safety rules and
  includes the retrieved KB snippets as the only allowed source of facts.
- KB source ids/titles are attached to the answer whenever the KB is used.
- A provider timeout or error is mapped to a safe operator transfer.

## Run in mock mode (default)
    cd backend
    AI_PROVIDER=mock python -m app.eval.run      # or just: python -m app.eval.run
    pytest                                       # full suite uses mock

## Run in Claude mode (optional, real API, billed)
    cd backend
    export AI_PROVIDER=claude
    export ANTHROPIC_API_KEY=sk-ant-...
    export CLAUDE_MODEL=claude-sonnet-4-6
    python -m app.eval.run                       # runs the 20 scenarios live

The simulation API also uses the selected provider automatically:
`POST /api/v1/simulation/calls` then `POST /api/v1/simulation/calls/{id}/message`.

## Eval harness
`app/eval/harness.py` runs 20 text-call scenarios through the full pipeline and
prints a report (passed/failed, action, transfer_expected, transferred,
sources_present, unsafe_output_blocked).

- Deterministic check (mock): `python -m app.eval.run --suite smoke` (or
  `--suite acceptance`), or `pytest app/tests/test_eval_harness.py`.
- The 50-call TZ acceptance set and its report fields are documented in
  docs/acceptance-eval.md.
- Real Claude eval is optional and only runs when `AI_PROVIDER=claude` and
  `ANTHROPIC_API_KEY` are set. Automated tests never call the real API (they use
  a fake client), so CI stays offline and free.

## Notes / limits
- The deterministic eval validates the pipeline (safety, grounding, transfer),
  which is provider-agnostic. Judging the natural-language quality/faithfulness
  of real Claude text is a manual review step on top of the live run.
- Unsupported-fact detection is bounded: the system prevents ungrounded factual
  answers (no KB -> transfer) and blocks unsafe medical content, but it cannot
  deterministically verify every fact inside a grounded answer.
