# CI/CD and Runner Mapping

Goals
- Ensure tests run deterministically across pipelines.
- Align tags to execution stages.
- Preserve evidence for audit and debugging.

Pipeline Guidance
- @smoke: PR gate or pre-merge checks
- @regression: nightly or scheduled runs
- @e2e: release candidate or staging gate
- @performance and @security: separate pipeline stages

Runner Configuration
- Use test_runner_instance.json to select envs and browser matrix.
- Keep parallelism settings inside config.
- Avoid environment branching in tests.

Execution Entry
- runner.py is the only entry point.
- Do not bypass runner.py for pipeline runs.

Artifacts and Retention
- Persist reports/ and CustomJsonReportFormatter output.
- Upload logs/ and output/ as pipeline artifacts.
- Retain artifacts by run_id for traceability.

Failure Handling
- Fail fast on critical tests (@smoke).
- Allow soft-fail with alerting for non blocking suites.
- Capture failure evidence before teardown.

Environment Matrix
- UI: browsers and devices from config.
- API: base URLs from config.
- Performance: isolated stage with longer timeouts.
