# Contributing

Contributions are welcome.

A proposed normative control should include:
1. concrete risk/failure mode;
2. applicability;
3. normative requirement;
4. required evidence;
5. verification method;
6. blocking condition;
7. authoritative or empirical references;
8. assurance-level rationale.

Do not add controls merely because a practice is fashionable.

## Changes to controls

Open a pull request and identify:
- existing controls affected;
- backward-compatibility impact;
- evidence burden;
- whether the change is normative or editorial.

## Research references

Prefer:
1. standards/public-sector/recognized security organizations;
2. peer-reviewed research;
3. transparent empirical preprints;
4. vendor research with methodology disclosed;
5. practitioner evidence.

Label evidence status honestly.

## Security

Follow `SECURITY.md`. Do not publish an exploit for an unpatched framework tooling vulnerability in a public issue.

## Style

Normative prose should be concise and testable. Avoid "be secure", "follow best practices", or persona-only instructions without an observable evidence requirement.

## Developer Setup & Testing Workflow

1. **Clone and install dependencies for testing**:
   ```bash
   git clone https://github.com/Maferreira25/Aura-Code.git
   cd Aura-Code
   pip install -e .[test]
   ```

2. **Run the test suite**:
   ```bash
   pytest
   # or with Python's built-in runner:
   python -m unittest discover -s tests -v
   ```

3. **Verify framework integrity and empirical test benchmarks**:
   Always run the validators before creating a pull request:
   ```bash
   python tools/validate_framework.py
   python validation/tools/validate_suite.py
   ```

4. **Update cryptographic manifest**:
   If adding, deleting, or modifying framework files, regenerate `MANIFEST.json`:
   ```bash
   python tools/update_manifest.py
   ```
