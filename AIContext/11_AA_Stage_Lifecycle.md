# Automation Architect Stage Lifecycle (Consolidated)

Purpose
Provide a single, end-to-end description of the Automation Architect lifecycle, including stage responsibilities, loop and retry behavior, HITL decision points, artifacts, and dynamic runtime behavior.

Audience
- Automation Architect agent
- Human reviewer and approver
- DevOps or release teams

Stage Overview
1) Plan
2) Design
3) Implement
4) Validate
5) Dry-Run
6) Git

Stage Details

Plan
- Goal: confirm scope and derive an automation plan that is safe and realistic.
- Inputs: scope (sprint, release, backlog), requirements, known risks, readiness signals.
- Outputs: plan summary, assumptions, dependencies, tagging plan, risk list.
- HITL: approval required if scope is ambiguous or high risk.
- Artifacts: plan JSON, assumptions list, decision log entry.

Design
- Goal: translate plan into a testable design with clear boundaries.
- Inputs: confirmed plan, system and API details, test data needs.
- Outputs: scenario list, locator strategy, data setup and cleanup plan, validation plan.
- HITL: optional approval if plan is complex or scope changed.
- Artifacts: design summary, locator policy notes, data strategy.

Implement
- Goal: produce framework-aligned code changes without boundary violations.
- Inputs: design artifacts, framework rules, data templates.
- Outputs: code changes in features/, pages/, clients/, Utility/, data factories.
- HITL: not required, but change review may be requested for critical scope.
- Artifacts: file change list, code diff summary, updated context references.

Validate
- Goal: verify static correctness and minimum expected quality.
- Inputs: code changes and prior stage outputs.
- Outputs: lint results, schema checks, static validations.
- HITL: optional if validation fails with ambiguity.
- Artifacts: validation summary with pass or fail notes.

Dry-Run
- Goal: execute a controlled run and capture evidence.
- Inputs: validated code, runtime config, test data.
- Outputs: execution status, logs, output artifacts, report entries.
- HITL: required if Dry-Run fails and next action is unclear.
- Artifacts: logs/, output/, reports/, CustomJsonReportFormatter output.

Git
- Goal: commit and push approved changes.
- Inputs: approved run and HITL decision.
- Outputs: commit, push, repo link, change summary.
- HITL: approval required before push.
- Artifacts: commit hash, branch name, artifact links.

Loop and Retry Rules
- Implement <-> Validate <-> Dry-Run is a loop.
- If Dry-Run fails with SCRIPT_ERROR or LOCATOR_MISSING: return to Implement.
- If Validate fails: return to Implement.
- If Dry-Run fails with ENV_DOWN or DATA_SETUP_FAILED: pause and request user action.
- Retries should be limited to a safe number (default 2) unless user approves.
- Each loop iteration must record what changed and why.

Error Categories and Handling
- LOCATOR_MISSING: update pages/ locators; re-run Dry-Run.
- ENV_DOWN: pause and request environment confirmation.
- DATA_SETUP_FAILED: fix data factory or template; re-run Validate then Dry-Run.
- AUTH_FAILED: request credentials from vault; re-run Dry-Run.
- TIMEOUT: tune waits or readiness checks; re-run Dry-Run.
- SCRIPT_ERROR: fix code in correct layer; re-run Validate then Dry-Run.

HITL Decision Analysis
- Required before Git stage.
- Required if scope changes in Plan or Design.
- Required if Dry-Run fails with ambiguous root cause.
- Optional for routine changes with low risk.

HITL Inputs
- Stage summary and outputs.
- Risk assessment and mitigation notes.
- Artifacts and logs.
- Proposed next action.

HITL Outcomes
- Approve: proceed to next stage.
- Reject: return to previous stage with explicit change request.
- Defer: wait for user or environment readiness.

Reviewer Sub-Agent (Automated Review)
- Runs after Implement, Validate, and Dry-Run.
- Read-only: no code changes, no file writes.
- Produces a structured verdict and recommendations for the next stage.

Reviewer Output Schema (Draft)
- status: approve | reject | needs_changes
- severity: blocker | major | minor
- findings[]:
  - rule_id
  - description
  - file_path
  - location_hint
  - fix_hint
  - confidence
- recommended_next_stage: Implement | Validate | Dry-Run | Plan
- summary: short explanation for human review

AA Correction Loop (Using Reviewer Output)
1) Build a fix plan ordered by severity (blocker -> major -> minor).
2) Apply changes only in the correct layer (features, pages, clients, Utility).
3) Update stage notes with what changed and why.
4) Re-run the minimal stage recommended by the reviewer.
5) Re-run reviewer; stop only on approve or explicit human override.

Dynamic Behavior
- The agent must adapt stage requirements based on detected situation:
  - Sprint Development: readiness gate enforced, Dry-Run required.
  - Backlog Automation: readiness gate optional, Dry-Run recommended.
  - Release Hardening: validation depth increased, approvals stricter.
  - Maintenance or Refactor: lower scope, but still enforce quality gates.
- The agent must reuse prior credentials and data if still valid.
- The agent must ask for missing inputs only when needed.

Artifacts (By Stage)
- Plan: plan JSON, assumptions list, decision log.
- Design: scenario matrix, locator policy, data plan.
- Implement: diff summary, file list, updated context references.
- Validate: lint results, static checks report.
- Dry-Run: logs/, output/, reports/, JSON report.
- Git: commit hash, branch, repo link.

Status Tracking
- Status values: queued, running, completed, failed, errored.
- Each stage must record start time, end time, and final status.
- Failure reasons must be mapped to one of the error categories.

Approval Notes
- Approvals must include approver name, timestamp, and comment.
- Rejections must include a reason and required changes.

Non Negotiable Rules
- Do not violate framework boundaries.
- Do not push to Git without approval.
- Do not proceed when environment is down unless override is granted.
