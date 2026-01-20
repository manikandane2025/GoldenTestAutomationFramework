# Execution Logs and Reports

Where to Look
- logs/: structured logs, request and response traces, correlation IDs
- output/: screenshots, videos, HAR, raw artifacts
- reports/: human readable reports and summaries
- CustomJsonReportFormatter/: machine readable JSON reports

Recommended Workflow
1. Open reports/ for the high level summary.
2. Use CustomJsonReportFormatter output to find failed tests and artifacts.
3. Drill into logs/ for trace IDs and step level messages.
4. Inspect output/ for screenshots and network traces.

Key Indicators
- Failures include a clear assertion message with business context.
- Each test logs start, step transitions, and end status.
- API errors include request and response with secrets masked.
- UI failures include screenshots and locator details.

Common JSON Fields (Typical)
- run_id, scenario_id, status, start_time, end_time
- tags, requirement_id, feature_name
- artifacts: screenshots, logs, traces
- error: message, stack, component

If Reports Are Missing
- Verify runner.py executed the configured report writers.
- Check test_runner_instance.json for reporting flags.
- Confirm output directories exist and are writable.

Console Output Tips
- Use the earliest error line in logs/ for root cause.
- Do not trust the last error line alone.
- Link log timestamps to report timestamps for traceability.

Artifact Hygiene
- Keep artifacts per run_id for isolation.
- Avoid overwriting artifacts between runs.
- Clean old artifacts by retention policy only.
