---
name: bug-assurance
description: Correct a bug by reproducing root cause, protecting the expected behavior with regression evidence, checking sibling impact and preserving evaluator integrity.
---

Reproduce/characterize → root cause → sibling search → regression oracle → minimal fix → related tests/security checks → independent review if significant.

Do not silence symptoms with generic catch/fallback unless that is the correct designed behavior.

If expected behavior is materially ambiguous, ask the user before encoding it in the regression test.
