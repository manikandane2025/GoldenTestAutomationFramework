# Framework Overview

Purpose
GoldenAutomationFramework is a unified automation framework for UI, API, integration, performance, and security tests. It enforces strict separation of concerns so that feature intent, UI mechanics, and API transport are independent and reusable.

Primary Language and Libraries
- Language: Python 3.x (confirm in GoldenAutomationFramework/requirements.txt)
- BDD: behave (features and step orchestration)
- UI: Playwright (browser automation and tracing)
- API: requests (HTTP client layer)
- Data/DB: SQLAlchemy (optional data utilities, not for assertions)
- Validation: jsonschema (contract checks)
- Templates: Jinja2 (payload and data templates)
- Config: PyYAML (runtime config) and JSON (test_runner_instance.json)

Do not add new libraries without approval. If a library is missing from requirements.txt, treat it as unavailable.

Audience
- Automation Architects who design the system
- Test Case Developers who implement tests
- DevOps teams who run CI/CD pipelines
- Auditors who review traceability and evidence

Execution Flow (High Level)
1. Load test_runner_instance.json (runtime selection, tags, env)
2. Initialize environment and config (config/ + constants.py)
3. Load utilities (Utility/) and logging
4. Initialize security and clients (security/ + clients/)
5. Load test data (input/ + FrameworkTestDataDatabase/ + templates/)
6. Execute tests (features/ + pages/ + clients/ + performance/ + security/)
7. Capture logs and raw artifacts (logs/ and output/)
8. Generate reports (reports/ + CustomJsonReportFormatter/)

Root Responsibilities
- features: intent and flow only; no low level mechanics
- pages: UI mechanics and locators only
- clients: API transport, auth, endpoint rules
- Utility: waits, retries, assertion helpers, logging
- FrameworkTestDataDatabase: data setup and cleanup utilities
- templates/input: reusable payloads and datasets
- reports: human readable outputs and summaries
- CustomJsonReportFormatter: machine readable outputs
- logs/output: execution artifacts and evidence

Separation Rules (Non Negotiable)
- No assertions in clients or pages
- No hardcoded secrets; use security/ or vault paths
- No static sleeps unless documented and justified
- Tests must be deterministic and parallel safe
- Avoid environment specific logic in tests (use config/test_runner_instance.json)

Locator Strategy (UI)
- Prefer stable hooks: data-testid, data-qa, aria-label, role + name
- Avoid brittle selectors (index based, dynamic IDs, layout XPaths)
- Centralize locators in pages/
- Use event driven waits from Utility/, not sleeps
- Document special cases (iframe, shadow DOM, virtualized lists)

API Strategy
- Keep endpoint construction and auth inside clients/
- Log request and response with secret masking
- Validate contracts with jsonschema when available
- Prefer API validations for stability where possible

Data Strategy
- input/: baseline static datasets
- templates/: parameterized payloads (Jinja2)
- FrameworkTestDataDatabase/: factories and cleanup
- Data isolation: unique run IDs and tenant or namespace
- Never share mutable data across parallel runs

Observability and Evidence
- logs/: structured step logs with correlation IDs
- output/: screenshots, network traces, raw artifacts
- reports/: human readable summary
- CustomJsonReportFormatter/: machine readable results for analytics

Quality Gates (Before Git)
- Lint and format pass (if configured)
- No secrets committed
- Deterministic and independent tests
- Clean setup and teardown or isolated data plan
- Reports generated in reports/ and JSON validated

Extension Points
- Add new API clients in clients/
- Add new UI pages and locators in pages/
- Add data factories in FrameworkTestDataDatabase/
- Add shared utilities in Utility/ (avoid business logic)
- Add report fields in CustomJsonReportFormatter/ only with architect approval and impact analysis
  - Treat the JSON schema as a stable contract for downstream tools
  - Changes may break report consumers and dashboards
  - Update documentation and any parsers in the same change set

Framework Stack (Code Map)
- runner.py: execution entry point and orchestration
- test_runner_instance.json: runtime selection, tags, environment
- constants.py: global constants and defaults
- config/: environment settings and runtime config loaders
- Utility/: logging, waits, retries, assertion helpers
- security/: secrets handling and security utilities
- clients/: API and service adapters (requests)
- pages/: UI page objects and locators (Playwright)
- features/: Behave scenarios and step orchestration
- FrameworkTestDataDatabase/: data factories and cleanup
- templates/: Jinja2 payload templates
- input/: static datasets
- reports/: human readable reports
- CustomJsonReportFormatter/: machine readable JSON reports
- logs/: structured execution logs
- output/: screenshots, traces, and artifacts

Anti Patterns (Avoid)
- Business logic inside features or pages
- Assertions inside clients or page objects
- Duplicated locators in tests
- Direct DB calls from UI tests
- Environment specific assumptions in code

Expected Run Outputs
- logs/: structured logs with timestamps
- output/: screenshots and network traces
- reports/: HTML or summary reports
- CustomJsonReportFormatter/: JSON results for agent consumption
