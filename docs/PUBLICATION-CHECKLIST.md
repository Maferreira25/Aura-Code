# GitHub Publication Checklist

Before making the repository public:

- [ ] Human project owner chooses the final public name after GitHub/package/trademark collision search; the current name is explicitly a working title.
- [ ] Replace generic contributor attribution if desired.
- [ ] Enable branch protection and required reviews.
- [ ] Enable GitHub Private Vulnerability Reporting.
- [x] GitHub Actions in the included workflow are pinned to a verified immutable full commit SHA.
- [ ] Enable Dependabot/renovation policy appropriate to repository.
- [ ] Run framework validator, validation-suite validator and tests from a clean clone (`tools/validate_framework.py`, `validation/tools/validate_suite.py`, unit tests).
- [ ] Review all external references/status dates.
- [ ] Tag `v0.1.1-draft`; do not label as stable/certified.
- [ ] Create Discussions or equivalent venue for control proposals.
- [ ] Add named maintainers to GOVERNANCE.md.
