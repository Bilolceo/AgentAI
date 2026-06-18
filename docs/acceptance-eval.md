# Acceptance eval (TZ 50-call set for the text pilot)

Two suites run through the full AIService pipeline (pre-LLM safety guard ->
provider -> post-LLM reviewer -> KB grounding / operator transfer):

- `smoke` - 20 representative scenarios (fast CI check; default).
- `acceptance` - TZ-aligned 50-call set covering Uzbek, Russian, and mixed
  input across: clinic info, prices, doctor schedules, FAQ, preparation,
  unknown price/service/doctor, booking intent, operator request, complaint,
  angry user, emergency, diagnosis, medicine, dosage, treatment, prompt
  injection, private patient-data request, and negative comparison.

Each scenario declares: expected_action (answer|transfer_operator|emergency),
expected language (uz|ru), requires_sources, unsafe_must_be_blocked,
expected_reason_code (for transfers), must_include phrases (e.g. "103" for
emergencies), and must_not_include phrases.

## Report fields
- total, passed, failed, pass_rate
- failed scenario names
- transfer_expected vs transferred
- sources_present count
- unsafe_blocked count (unsafe_must_be_blocked scenarios that passed)
- language_match count
- emergency_103 count

## Run in mock mode (deterministic, no API key)
    cd backend
    python -m app.eval.run --suite smoke
    python -m app.eval.run --suite acceptance

The default suite is `smoke`. Automated tests
(`app/tests/test_eval_harness.py`) always use the mock provider and assert that
all 50 acceptance scenarios pass.

## Run live Claude acceptance (optional, real API, billed)
    cd backend
    export AI_PROVIDER=claude
    export ANTHROPIC_API_KEY=sk-ant-...
    export CLAUDE_MODEL=claude-sonnet-4-6
    python -m app.eval.run --suite acceptance

If AI_PROVIDER=claude and ANTHROPIC_API_KEY is missing, the runner fails fast
(see docs/live-claude-provider.md). Automated tests never call the real API.

## Important: live Claude results need manual review
The eval checks pipeline behavior (action, grounding/sources, transfer routing,
language, emergency 103, no leaked unsafe content via must_not_include). It does
NOT judge natural-language wording or fully verify factual faithfulness of free
text. For a live Claude run, a human must additionally review answer wording,
tone, and that every clinic fact is actually supported by the KB. The
must_include phrases are exact KB substrings tuned for mock mode; a live model
may paraphrase, so treat must_include failures under Claude as review prompts,
not hard regressions.
