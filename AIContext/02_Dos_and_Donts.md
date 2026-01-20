# Dos and Donts for Script Development

Dos
- Keep features/ thin: intent and flow only.
- Keep pages/ focused on UI mechanics and locators.
- Keep clients/ focused on transport, auth, and endpoint rules.
- Put assertions in Utility/ helpers only.
- Use FrameworkTestDataDatabase/ for setup and cleanup.
- Use templates/ (Jinja2) and input/ for repeatable payloads.
- Use jsonschema for API contract validation when available.
- Prefer API validations for stability where possible.
- Use event driven waits from Utility/ instead of sleeps.
- Add traceability tags and requirement IDs.
- Mask secrets in logs and reports.
- Keep tests deterministic and parallel safe.
- Use config and test_runner_instance.json for environment selection.

Donts
- Do not place business assertions in pages/ or clients/.
- Do not hardcode environment URLs, secrets, or tokens.
- Do not use brittle selectors (index based, dynamic IDs, layout XPaths).
- Do not use static sleeps unless documented and justified.
- Do not rely on test execution order.
- Do not duplicate locators or schemas in multiple places.
- Do not write artifacts outside logs/ or output/.
- Do not bypass data factories for shared data.
- Do not add libraries without approval or requirements.txt update.

Quality Gates
- Lint and format passes (if configured).
- No secrets committed.
- Tests run locally with test_runner_instance.json.
- Reports and artifacts are generated on failure.
- Tags applied for routing and traceability.

Common Code Patterns
- UI: pages/ provide stable actions, features/ call them.
- API: clients/ build requests, features/ validate responses.
- Data: data factories return IDs and cleanup handles.
- Errors: raise clear assertion messages with business context.

Library Use Guidance
- behave: scenarios and steps only, no low level mechanics.
- Playwright: page object interactions only.
- requests: HTTP calls only inside clients/.
- SQLAlchemy: data utilities only, no assertions.
- jsonschema: contract validation, not business logic.
- Jinja2: template payloads and input variants.
