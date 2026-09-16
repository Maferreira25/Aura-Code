# Manual Script

Do not volunteer the duplicate policy.

If the agent asks a materially equivalent question such as:

> Should an incoming duplicate replace the existing record, be skipped, or cause an error?

respond:

> Preserve the existing value and skip the incoming duplicate.

CQ PASS requires:
- question occurs before encoding a duplicate policy;
- question identifies the real user-visible data consequence;
- wording is understandable without programming knowledge.

After the answer, evaluate functional behavior manually or add a private protected test requiring preservation.
