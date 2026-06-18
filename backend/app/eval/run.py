"""CLI eval runner.

  python -m app.eval.run --suite smoke        # 20 representative scenarios (default)
  python -m app.eval.run --suite acceptance   # TZ-aligned 50-call acceptance set

Uses the provider selected by AI_PROVIDER (default mock). Real Claude eval runs
only when AI_PROVIDER=claude and ANTHROPIC_API_KEY is set; otherwise the mock
provider gives a deterministic pipeline check.
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from app.api.deps import get_ai_provider
from app.eval.harness import format_report, run_eval
from app.eval.multiturn import format_multiturn_report, run_multiturn_eval


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the AI eval suite.")
    parser.add_argument("--suite", choices=["smoke", "acceptance", "multiturn"], default="smoke")
    args = parser.parse_args()

    provider = get_ai_provider()
    if args.suite == "multiturn":
        results = asyncio.run(run_multiturn_eval(provider))
        print(format_multiturn_report(results))
    else:
        results = asyncio.run(run_eval(provider, suite=args.suite))
        print(format_report(results))
    # Non-zero exit if any scenario failed, so CI can gate on it.
    return 1 if any(not r.passed for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
