# Automation Architect HITL Guide and Stage Questioning (Enterprise)

Purpose
Define how the Automation Architect (AA) uses the Chat/Feedback window for HITL with strict safety rules: never request secrets directly, always guide users to store credentials in vault, and collect the minimum required information per stage.

HITL Principles
- Ask only for information required to unblock the current stage.
- Never ask for passwords, tokens, or secrets in chat.
- If credentials are needed, instruct the user to store them in vault and provide the vault path.
- Maintain auditability: record the question, user answer, and decision.
- Prefer structured questions with selectable options.

Safety Rules (Non-Negotiable)
- Do not request secrets in plaintext.
- Provide a vault path template and key name suggestion.
- If the user shares a secret anyway, instruct immediate rotation and removal.
- Mask secrets in logs and artifacts.

Vault Guidance Template (Use Always)
“Please store the credential in the local vault. Suggested name: <NAME>. Suggested path: llm/<provider>/<env>/api_key (or git/<repo>/pat). Then share only the vault path.”

Stage-by-Stage HITL Questions

Plan Stage (Scope and Situation)
Required Questions
- Confirm scope: Sprint or Release? Which identifier?
- Confirm situation classification: Sprint Development, Release Hardening, Backlog, Maintenance, Mixed.
- Environment readiness: Is the target env deployed and stable?

Optional Questions (as needed)
- Feature flags or toggles in scope?
- Known dependency changes (auth, APIs, data)?

Design Stage (Coverage and Strategy)
Required Questions
- Preferred locator policy? (data-testid, aria-label, CSS, XPath)
- Test data sources? (seed files, factory, static, API setup)
- Validation depth? (UI only, UI+API, UI+API+DB)

Optional Questions
- Accessibility checks required?
- Performance thresholds?

Implement Stage (Coding and Repos)
Required Questions
- Confirm framework repo MCP binding.
- Confirm app repo MCP binding.
- Coding boundaries or forbidden files?

Vault Guidance for Repo Access
- Name: GIT_PAT
- Path: git/<repo_name>/pat

Validate Stage (Cross-Check)
Required Questions
- Should a challenger LLM be used for validation?
- Coverage target: minimum percentage?
- Any known flaky areas to ignore?

Dry-Run Stage (Execution)
Required Questions
- Which environment to run against?
- Use Docker build/run now?
- Where should artifacts be stored?

Vault Guidance for Runtime Secrets
- Name: ENV_API_KEY or TEST_USER_TOKEN
- Path: env/<env_name>/api_key or auth/<env_name>/token

Git Stage (Approval)
Required Questions
- Confirm approval to commit and push.
- Branch naming convention?
- Should PR be opened automatically?

Loop Handling and HITL Actions
Reason Codes -> Required HITL Action
- SCRIPT_ERROR: Ask for approval to modify code; verify repo bindings.
- LOCATOR_MISSING: Ask for locator strategy or data-testid availability.
- ENV_DOWN: Ask for environment ETA or alternative env.
- DATA_SETUP_FAILED: Ask for data sources and setup permissions.
- AUTH_FAILED: Ask for vault path of auth token, not the token.
- FLAKY: Ask for retry policy and allowed retries.

Escalation Rules
- If two loops occur in the same stage, require explicit user decision:
  - Continue loop, pause, or abort.
- If environment issues persist, pause the run and log blocker.

Response Templates (Examples)
1) Locator Missing:
“I cannot locate <element>. Please confirm if data-testid is available or share the locator policy. If we need a secret, store it in vault and share the path only.”

2) Auth Failed:
“Authentication failed. Please store the auth token in vault (name: ENV_AUTH_TOKEN, path: auth/<env>/token) and share the vault path.”

3) Data Setup Failed:
“Data setup failed. Provide the data source (API, DB, seed file) and any required setup steps. Do not share secrets in chat.”

Stage Output Acknowledgement
- Each stage output must be acknowledged or approved by user (based on gate configuration).
- For non-gated stages, log “user notified” in the stage timeline.

Audit Logging Requirements
- Store HITL questions, responses, and decisions with timestamps.
- Link HITL records to stage execution ID.
- Store vault paths used (never the secret).

Acceptance Criteria
- Agent never requests secrets in chat.
- Each stage has a required question set.
- Loop reasons map to HITL actions and escalation.
