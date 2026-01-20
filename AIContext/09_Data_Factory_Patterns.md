# Data Factory Patterns

Purpose
Use FrameworkTestDataDatabase to create, seed, and clean test data safely. Keep data generation deterministic and isolated per run.

Patterns
- Factory methods for common entities (user, policy, claim, enrollment).
- Unique IDs per run to avoid collisions.
- Cleanup hooks for created data.
- Templates with Jinja2 for parameterized payloads.

Sources
- templates/ for payload templates.
- input/ for static datasets.
- clients/ for API based setup.

Best Practices
- Keep data generation deterministic.
- Separate setup and validation.
- Avoid shared mutable datasets in parallel runs.
- Track data dependencies in logs for traceability.

Data Contracts
- Prefer jsonschema for payload validation.
- Store schema references with test data when possible.

Cleanup Strategy
- Always return cleanup handles from factories.
- Use teardown hooks to delete created data.
- If cleanup is blocked, log the data identifiers for manual cleanup.
