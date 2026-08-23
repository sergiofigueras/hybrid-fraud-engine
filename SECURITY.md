# Security Policy

## Educational-use boundary

This repository is an educational and portfolio project based on synthetic data. It is not approved for real payment authorization, fraud blocking, credit decisions, or other high-impact financial actions.

## Reporting vulnerabilities

Do not disclose a suspected vulnerability in a public issue. Report it privately to the repository owner through an appropriate private GitHub contact or security-advisory channel.

A useful report includes:

- the affected file, endpoint, or component;
- reproduction steps;
- expected and observed behavior;
- potential impact;
- suggested remediation, when available.

## Known security considerations

### Serialized model artifact

The bundled model uses `joblib`, which relies on Python object serialization. Loading an untrusted model artifact can execute malicious code. Only load artifacts from controlled and verified sources.

### Trusted feature sources

Fields such as account lock state, stolen-card status, transaction velocity, merchant risk, and daily limits must come from authoritative internal services in a real system. Do not trust an external caller to assert these values.

### Authentication and authorization

The tutorial API intentionally omits user authentication. A deployed service must implement authentication, service authorization, least privilege, network controls, request limits, and audit logging.

### Sensitive data

Transaction payloads may contain personal and financial information. Minimize collection, tokenize identifiers, encrypt data in transit and at rest, limit access, and define retention and deletion policies.

### Model and policy integrity

Production deployment should use signed artifacts, checksums, controlled registries, rule approval workflows, versioned configuration, immutable audit records, and tested rollback procedures.

### Decision safety

The model cannot auto-decline a transaction in this tutorial. High model scores route transactions to review. Do not remove that constraint without a formal risk assessment, calibrated decision policy, legal and compliance review, and tested customer-remediation procedures.

## Supported versions

Security fixes should be applied to the latest version on the `main` branch.
