# Runtime Troubleshooting

Common Issues and Checks

1) LOCATOR_MISSING
- Verify locator in pages/ only.
- Prefer data-testid or aria-label selectors.
- Check iframe or shadow DOM.
- Ensure waits are event driven and in Utility/.

2) TIMEOUT
- Confirm environment readiness and page load signals.
- Increase explicit wait timeout in Utility/ only.
- Avoid static sleeps unless justified.

3) AUTH_FAILED
- Validate credentials from security/ or vault.
- Confirm token refresh logic in clients/.
- Check required headers and tenant IDs.

4) DATA_SETUP_FAILED
- Validate templates/ and input/ data integrity.
- Ensure FrameworkTestDataDatabase creates unique records.
- Add cleanup to teardown hooks.

5) ENV_DOWN
- Check base URL health endpoints.
- Confirm environment readiness checks ran.
- Verify DNS, proxy, or VPN constraints.

6) SCRIPT_ERROR
- Locate the failing layer (feature vs page vs client).
- Fix the issue in the correct layer only.
- Add or refine assertions in Utility/.

Runtime Console Errors
- Read the first error line and locate the module path.
- Trace to the boundary: feature vs page vs client.
- Fix the issue in the correct layer only.

Escalation
- If the fix changes execution flow or boundaries, escalate to the Automation Architect agent.
