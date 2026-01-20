# Automation Architect Workflow and HITL (Enterprise Standard)

Purpose
Automation Architect (AA) converts story lists into automation-ready assets with auditability, quality gates, and controlled execution. This document defines enterprise-grade stage contracts, artifacts, approvals, and operational controls.

Scope and Entry
- Source of truth: Demo Studio page (Excel or text input) with Scope selector (Sprint/Release).
- Input list: User stories filtered by selected scope.
- Output: Automation artifacts, validation results, dry-run evidence, and Git changes with approvals.

Input Contract (Excel)
Minimum columns (case-insensitive):
- Issue Key
- Summary
- Module
- Priority
- Story Points
- Type
- Sprint
- Release
- Description
- Acceptance Criteria

Optional columns:
- Tags
- Owner
- Component
- Epic
- Env

Validation rules:
- Each row must have Issue Key and Summary.
- Sprint and Release are required for scope filtering.
- Acceptance Criteria should be non-empty or marked with "TBD" for Plan stage.
- Duplicate Issue Key is rejected unless explicit "merge" flag is provided.

Scope Behavior (Demo Page)
- User selects Scope Type: Sprint or Release.
- If Excel is uploaded, the system parses rows and derives available Sprint/Release options.
- When a scope is selected, only matching stories are used for AA stages.

Stage Model (Enterprise Contracts)
Stages
1) Plan
2) Design
3) Implement
4) Validate
5) Dry-Run
6) Git

Stage Contract Template
- Inputs: required data at stage entry
- Activities: core actions AA performs
- Outputs: artifacts and records produced
- Exit criteria: conditions to advance
- Failure handling: rules and escalation

Plan Stage
Inputs:
- Scoped story list
- RAG context (project standards, patterns, constraints)
- LLM profile (per tenant defaults)

Activities:
- Confirm scope and backlog shape
- Identify dependencies, risks, and assumptions
- Propose tagging and coverage strategy
- Define data and environment requirements

Outputs:
- Plan summary (scope, assumptions, constraints)
- Risk register with mitigation
- Tagging plan and coverage map
- Data plan (sources, generation, masking)

Exit criteria:
- Scope verified
- Risks categorized and assigned
- Plan approved if Plan HITL is enabled

Design Stage
Inputs:
- Plan output
- Acceptance criteria per story
- Target automation framework constraints

Activities:
- Decompose stories into scenarios and flows
- Define locator strategy (data-testid preferred)
- Map API contracts and validations
- Define observability plan (logs, screenshots, video, traces)

Outputs:
- Scenario matrix (story to test mapping)
- Locator policy and selectors list
- Data setup and cleanup steps
- Validation checklist (API/UI/DB)

Exit criteria:
- Scenario coverage >= 95 percent of scoped stories
- Locator policy documented
- Design approved if Design HITL is enabled

Implement Stage
Inputs:
- Design artifacts
- Repo bindings (framework and app repo MCP)

Activities:
- Generate or update automation code within allowed boundaries
- Add helpers, fixtures, page objects, or data factories
- Update documentation for new utilities

Outputs:
- Code diff with file map
- New utilities or fixtures list
- Implementation notes per story

Exit criteria:
- Lint or type checks pass (where available)
- No hard-coded secrets
- Implementation notes recorded

Validate Stage
Inputs:
- Implement outputs
- Validation plan

Activities:
- Static analysis, lint, type checks
- API contract checks
- Minimal local execution (smoke or targeted)

Outputs:
- Validation report
- Issues list with severity

Exit criteria:
- No P0/P1 open defects
- Validation report attached

Dry-Run Stage
Inputs:
- Buildable repo state
- Test config and environment

Activities:
- Execute full flow or selected suite in Docker
- Capture logs, screenshots, videos, and reports

Outputs:
- Run record (id, env, timestamps, status)
- Artifact links (logs, reports)
- Execution summary

Exit criteria:
- Dry-run success or approved exception
- Artifacts published

Git Stage
Inputs:
- Final code, reports, and approvals

Activities:
- Commit with enterprise policy
- Push branch and open PR (if enabled)

Outputs:
- Commit hash, branch, and PR link
- Approval record

Exit criteria:
- Git approval received

Loop Rules (Enterprise)
- Implement <-> Validate <-> Dry-Run is a loop.
- If Dry-Run fails due to script or locator issues, return to Implement.
- If failure is infra or data, pause and request operator action.
- If failure is flaky, run one retry with capture, then escalate.

HITL Gates
- Mandatory: Git
- Optional: Plan, Design, Dry-Run
- Approver validates scope correctness, stability, evidence, and traceability.

Governance and Audit
- Every stage records: user, timestamp, inputs, outputs, and decision.
- Artifacts are immutable and linked to run id.
- All secrets are vault-managed (no plaintext in code or logs).

Error Taxonomy
- SCRIPT_ERROR
- LOCATOR_MISSING
- ENV_DOWN
- DATA_SETUP_FAILED
- AUTH_FAILED
- FLAKY

MCP Usage (Enterprise)
- Git and repo operations must use MCP bindings.
- LLM routing can be direct or MCP per profile.
- MCP tool: llm_chat (default) with server selection per profile.

Quality Gates
- Tag coverage >= 95 percent
- No policy violations (secrets, boundary edits)
- Validation report attached before Dry-Run
- Dry-run evidence attached before Git

Metrics
- Lead time per stage
- Rework cycles (Implement/Validate/Dry-Run)
- Flake rate
- Coverage delta vs scope

Git Policy
- Commit message must mention agent role and stage
- Include artifact links in commit or PR

Example Commit Message
AutomationArchitect: AA Implement + Dry-Run artifacts (approved)

Demo Page Enhancements (Recommended)
- Validate Excel schema on upload and show row-level errors
- Show scope filter summary and coverage percentage
- Provide stage-level SLA timers and ownership
- Add artifact viewer panel in Timeline tab
