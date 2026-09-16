# Safety and Ethics

The suite is designed to test software assurance, not real-world intrusion.

Security scenarios SHOULD:
- run in isolated local containers/temp directories;
- use synthetic data and credentials;
- avoid scanning or attacking external systems;
- avoid real malware/persistence;
- demonstrate vulnerability resistance with benign proofs.

When using real vulnerability repositories/benchmarks:
- follow upstream license and safety guidance;
- keep exploit execution isolated;
- do not expose vulnerable services publicly;
- do not publish a zero-day discovered during evaluation before coordinated disclosure.

Human-study claims require appropriate research ethics review where applicable.

Do not use the framework benchmark to rank individual employees without a separately justified personnel-evaluation policy.
