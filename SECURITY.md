# Security policy

The Spec-Drift Chronometer is an oversight component, so weaknesses in it can weaken the oversight of the systems it protects. Reports are taken seriously.

## Reporting a vulnerability

Please **do not open a public issue**. Instead, report privately:

- through GitHub: **Security → Report a vulnerability** on this repository, or
- by email to **info@aevoxis.de** with the subject "Security: Spec-Drift Chronometer".

Please include what you found, how to reproduce it, and what an attacker could achieve. You will receive an acknowledgement within 7 days. Once a fix is available, the report is credited in the release notes unless you prefer otherwise.

## Scope

In scope: the backend (`backend/`), the dashboard (`frontend/`), the integrations (`integrations/`) and the test suite.

Already known and documented, so no report is needed (see "Known limitations" in the README): approvals carry no identity check, intent files are not yet signed, near misses are not logged, and an unreachable scoring model produces a normal-looking rejection. New ways to exploit these are still welcome.

## Supported versions

This is a prototype. Fixes are made on the `main` branch only.
