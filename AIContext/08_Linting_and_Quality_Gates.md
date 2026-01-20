# Linting and Quality Gates

Linting
- Run configured linters and formatters before commit.
- Use the repo configuration if present.
- If configured, common tools may include ruff, flake8, black, isort, or mypy.
- Do not add new tooling without approval.

Quality Gates
- No secrets committed.
- No duplicated utilities.
- Tests are independent and deterministic.
- Reports generated on failure.
- Tags applied correctly.
- Boundaries respected: features, pages, clients, Utility.

Recommended Checks
- Static lint and format
- Contract validation (jsonschema) if available
- Minimal UI coverage for high value flows
- API smoke validation where possible

Pre-Commit Checklist
- runner.py not modified unless approved
- test_runner_instance.json updated only for runtime selection
- new pages and clients documented in context.json (if required)
