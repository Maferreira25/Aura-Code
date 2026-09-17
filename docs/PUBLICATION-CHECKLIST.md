# GitHub Publication Checklist

Before making the repository public:

- [ ] Human project owner chooses the final public name after GitHub/package/trademark collision search; the current name is explicitly a working title.
- [x] Replace generic contributor attribution if desired (Confirmed: maintaining "AuraCode Contributors").
- [ ] Enable branch protection and required reviews (Configure in GitHub Settings -> Branches).
- [ ] Enable GitHub Private Vulnerability Reporting (Configure in GitHub Settings -> Code security).
- [x] GitHub Actions in the included workflow are pinned to a verified immutable full commit SHA.
- [x] Enable Dependabot/renovation policy appropriate to repository (Configured in .github/dependabot.yml).
- [x] Run framework validator, validation-suite validator and tests from a clean clone (`tools/validate_framework.py`, `validation/tools/validate_suite.py`, unit tests).
- [ ] Review all external references/status dates.
- [ ] Tag `v0.1.1-draft`; do not label as stable/certified.
- [ ] Create Discussions or equivalent venue for control proposals (Configure in GitHub Settings -> Features).
- [x] Add named maintainers to GOVERNANCE.md (Added @Maferreira25 as Lead Maintainer).
