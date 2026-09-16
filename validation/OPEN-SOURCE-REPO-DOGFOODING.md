# Open-Source Repository Dogfooding

Before public release, this framework repository should itself be assessed against the current OpenSSF OSPS Baseline (current at research time: v2026.08.28) in addition to its own controls.

Local files can satisfy only part of that posture. GitHub-host settings must be configured after repository creation.

## File-level items already present

- MIT `LICENSE`;
- contribution guide;
- security policy;
- code of conduct;
- architecture/framework documentation;
- automated tests/validation workflow;
- unique version/changelog structure.

## GitHub settings that require the human repository owner

- [ ] Require MFA consistent with organization/repository policy.
- [ ] Protect the primary branch against direct push/deletion.
- [ ] Require pull-request/status checks.
- [ ] Keep default workflow permissions at minimum necessary.
- [ ] Prevent untrusted PR code from obtaining privileged secrets.
- [ ] Enable private vulnerability reporting.
- [ ] Define maintainers/roles.
- [ ] Configure signed/attested release process.
- [ ] Add dependency update/security monitoring.
- [ ] Verify official project/distribution links use authenticated encrypted channels.

Do not claim OSPS Baseline conformance until those host-level controls are assessed against the exact current baseline version.
