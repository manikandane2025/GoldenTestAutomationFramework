# Automation Architect Stage Contracts, LLM Profiles, and Looping (Enterprise Standard)

Purpose
Define how each Automation Architect (AA) stage is executed with explicit prompts, per-stage LLM profile selection, and real-world looping rules. This document is the enterprise-grade counterpart to the early workflow notes and the Situation Identification Plan.

Scope
- Applies to the Demo Studio AA runner (Excel input with Sprint/Release scope).
- Covers stage contracts, prompt persistence, LLM profile selection, and loop policies.
- Incorporates real-world scenario handling (from 10_AA_Situation_Identification_Plan.md).

Core Principles
- Every stage has a contract: Inputs, Activities, Outputs, Exit Criteria.
- Each stage has a stored prompt, versioned and auditable.
- LLM selection is explicit per stage, with optional challenger model for validation.
- Loops are driven by output quality and dependency readiness, not a fixed stage pair.

Stage Catalog
1) Plan
2) Design
3) Implement
4) Validate
5) Dry-Run
6) Git

Stage Dependencies (High Level)
- Plan depends on: scoped story list + situation confirmation.
- Design depends on: Plan outputs.
- Implement depends on: Design outputs + repo bindings.
- Validate depends on: Implement outputs.
- Dry-Run depends on: Validate outputs + environment readiness.
- Git depends on: Dry-Run success + approvals.

LLM Profile Selection (Enterprise Policy)
- Default LLM profile applies to all stages unless a stage override is configured.
- Each stage may specify a primary LLM profile and an optional challenger profile.
- Challenger profile is used for critique or cross-check (e.g., Validate stage).
- If a stage override profile is missing or fails, fallback to default and record the fallback.
- LLM profile usage is persisted per stage execution (profile id, model, routing mode, timestamp).

Prompt Storage and Versioning
- Each stage has its own prompt stored in DB with:
  - stage_name
  - prompt_version
  - prompt_text
  - created_by
  - created_at
  - active_flag
- Stage prompt updates create new versions; historical versions remain immutable.
- Stage execution records the prompt version used.

Prompt Template (Baseline)
- SYSTEM ROLE: stage-specific responsibilities
- INPUTS: required artifacts and context
- TASKS: enumerated stage actions
- OUTPUT FORMAT: strict JSON or structured markdown
- QUALITY RULES: measurable checks

Stage Contracts (Enterprise Detail)

Plan Stage
Inputs:
- Scoped story list
- Situation classification + confidence
- RAG context

Activities:
- Confirm scope and execution situation
- Identify dependencies and risk
- Define tagging and coverage strategy
- Define data and environment requirements

Outputs:
- Plan summary
- Risk register
- Tagging plan
- Data plan

Exit Criteria:
- Situation confirmed or overridden with reason
- Risks categorized with mitigation
- Plan approval if HITL enabled

Design Stage
Inputs:
- Plan outputs
- Story acceptance criteria
- Framework constraints

Activities:
- Decompose stories into scenarios
- Define locator strategy and UI/API coverage
- Define data setup and cleanup steps
- Define observability plan

Outputs:
- Scenario matrix
- Locator policy
- Data and validation checklist

Exit Criteria:
- Scenario coverage >= 95 percent
- Locator policy documented
- Design approval if HITL enabled

Implement Stage
Inputs:
- Design artifacts
- Repo bindings (framework/app MCP)

Activities:
- Generate or update automation code
- Update helpers, fixtures, page objects
- Document changes and intent per story

Outputs:
- Code diff map
- Implementation notes
- Utility or fixture list

Exit Criteria:
- Lint or type checks pass (if available)
- No secrets in code
- Implementation notes recorded

Validate Stage
Inputs:
- Implement outputs
- Validation plan
- Optional challenger LLM profile

Activities:
- Static checks and contract validation
- LLM critique (challenger model) on implementation vs requirements
- Identify gaps and missing coverage

Outputs:
- Validation report
- Gap list and severity

Exit Criteria:
- No P0/P1 open defects
- Validation report attached

Dry-Run Stage
Inputs:
- Buildable repo state
- Test environment readiness

Activities:
- Execute targeted or full suites in Docker
- Capture logs and artifacts

Outputs:
- Run record (id, env, status)
- Artifact links
- Execution summary

Exit Criteria:
- Dry-run success or approved exception
- Artifacts published

Git Stage
Inputs:
- Approved Dry-Run
- Final code and artifacts

Activities:
- Commit with enterprise policy
- Push branch and open PR (if enabled)

Outputs:
- Commit hash, branch, PR link
- Approval record

Exit Criteria:
- Git approval received

Looping Strategy (Enterprise)
Loops are dependency-driven. The system uses stage outputs to determine the next stage or loop-back target.

Loop Triggers
- Plan -> Design: Missing acceptance criteria or unclear scope
- Design -> Plan: Scope mismatch or situation reclassification
- Implement -> Design: Missing scenarios or locator policy gaps
- Validate -> Implement: Coverage gaps or contract violations
- Dry-Run -> Implement: Script errors or locator failures
- Dry-Run -> Validate: Evidence missing or validation checks incomplete

Failure Taxonomy to Loop Mapping
- SCRIPT_ERROR -> Implement
- LOCATOR_MISSING -> Design or Implement (based on root cause)
- ENV_DOWN -> Pause (request operator action)
- DATA_SETUP_FAILED -> Plan or Design (data plan update)
- AUTH_FAILED -> Plan (credential readiness)
- FLAKY -> Dry-Run retry then Validate

Situation-Aware Loop Rules
- Sprint Development: prioritize speed, allow limited rework loops before Git gate.
- Release Hardening: stricter Validate and Dry-Run loops, no Git without evidence.
- Backlog Automation: more Design -> Implement iterations, Dry-Run optional unless execution requested.
- Maintenance/Refactor: focus on Implement -> Validate; skip Plan if scope unchanged.
- Mixed Scope: split runs by situation; loop rules per split.

LLM Usage Patterns by Stage
- Plan: default profile
- Design: default profile, optional second-pass critique for coverage completeness
- Implement: default profile or code-specialized model (if configured)
- Validate: primary + challenger profile for cross-check
- Dry-Run: no LLM unless summary/triage needed
- Git: default profile for commit message compliance

Data Model (Recommended)
- aa_stage_prompt:
  - id, stage_name, version, prompt_text, is_active, created_by, created_at
- aa_stage_execution:
  - work_order_id, stage_name, prompt_version, llm_profile_id, routing_mode, started_at, ended_at, status
- aa_stage_feedback:
  - work_order_id, stage_name, author, feedback, at
- aa_stage_loop:
  - work_order_id, from_stage, to_stage, reason_code, at

Demo Page Integration
- Scope selection filters story list before Plan stage.
- Stage prompt editor loads from prompt registry and saves with versioning.
- LLM profile picker per stage (with default fallback).
- Timeline shows stage outputs, status, and loop history.

Acceptance Criteria
- Each stage uses a saved prompt with version recorded.
- Each stage can use a different LLM profile.
- Loop decisions are traceable and reason-coded.
- Stage outputs persist and are visible in Timeline.

Appendix: Stage Prompt Skeleton (Example)
SYSTEM ROLE:
You are the Automation Architect responsible for {{stage}}.

INPUTS:
- stories: {{stories}}
- scope: {{scope}}
- prior_stage_output: {{prior_stage_output}}

TASKS:
1) Perform {{stage}} activities.
2) Identify gaps and risks.
3) Produce outputs in the required format.

OUTPUT FORMAT (STRICT JSON):
{
  "stage": "{{stage}}",
  "summary": "...",
  "artifacts": [],
  "risks": [],
  "next_actions": []
}
