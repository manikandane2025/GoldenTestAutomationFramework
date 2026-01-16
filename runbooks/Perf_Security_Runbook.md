# Performance and Security Runbook

## Performance (k6)
### Run
```
pwsh GoldenAutomationFramework/performance/run_k6.ps1 -BaseUrl http://localhost:3000
```

### Output
- JSON summary: `GoldenAutomationFramework/reports/perf/k6_summary_*.json`
- HTML report: `GoldenAutomationFramework/reports/perf/k6_report_*.html`

## Security (OWASP ZAP baseline)
### Run
```
pwsh GoldenAutomationFramework/security/zap_baseline.ps1 -TargetUrl http://localhost:3000
```

### Output
- HTML report: `GoldenAutomationFramework/reports/security/zap_baseline_*.html`

## Notes
- Ensure backend and frontend are running.
- Use sprint-specific URLs if needed.
