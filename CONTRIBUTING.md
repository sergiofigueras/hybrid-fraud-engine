# Contributing

Contributions that improve correctness, test coverage, documentation, observability, and safety are welcome.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/verify_project.py
```

## Pull-request expectations

A change should:

- preserve the rule/model decision hierarchy unless the policy change is explicit;
- include tests for new behavior;
- avoid real customer or payment data;
- update documentation when contracts or workflows change;
- keep training and inference feature transformations consistent;
- avoid silently converting a ranking score into a claimed calibrated probability;
- document security, privacy, and operational implications.

## Commit style

Clear conventional-style messages are preferred, for example:

```text
feat: add beneficiary-age review rule
fix: reject timezone-naive transaction events
test: cover model artifact readiness failure
docs: expand threshold selection guidance
```
