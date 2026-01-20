# Automation Architect (AA) Enterprise Design and Implementation Plan

Purpose
Define the enterprise design and implementation plan to make the Automation Architect agent a coding-first automation expert, with accurate stage execution, robust looping, and Docker Build/Run integrated into the Dry-Run stage.

Core Identity
AA is a coding agent by nature. It must:
- Produce automation code and supporting artifacts.
- Adhere to framework boundaries.
- Provide verifiable evidence for every stage outcome.

Non-Goals
- This plan does not replace backend orchestration design for other agents.
- This plan does not prescribe a specific toolchain beyond MCP and Docker integration.

System Architecture Overview
Components
- Demo Studio (frontend) for stage execution and HITL.
- Orchestrator API (backend) for stage execution and persistence.
- MCP integrations for repo and tool access.
- LLM Profiles per stage with optional challenger model.
- Docker Build + Run to validate Dry-Run execution.

Data Model (Enterprise)
1) aa_stage_prompt
- id, stage_name, version, prompt_text, is_active, created_by, created_at

2) aa_stage_execution
- work_order_id
- stage_name
- prompt_version
- llm_profile_id
- routing_mode (direct or mcp)
- status (queued, running, completed, failed, blocked)
- started_at, ended_at
- output_summary (text)

3) aa_stage_artifact
- work_order_id
- stage_name
- type (log, report, diff, screenshot, video)
- uri, created_at

4) aa_stage_loop
- work_order_id
- from_stage, to_stage
- reason_code (SCRIPT_ERROR, LOCATOR_MISSING, ENV_DOWN, DATA_SETUP_FAILED, AUTH_FAILED, FLAKY)
- comment, created_at

5) aa_stage_llm_profile
- stage_name
- primary_profile_id
- challenger_profile_id (optional)
- is_active

Stage Design (Coding-First)
Plan
- Output: scope summary, risk list, data plan, tagging plan
- Coding expectation: none

Design
- Output: scenario matrix, locator policy, data setup plan
- Coding expectation: none

Implement
- Output: code changes, fixtures, page objects, utilities, diff map
- Coding expectation: required (primary AA coding stage)

Validate
- Output: validation report, gap list, severity
- Coding expectation: optional (fixes or adjustments)

Dry-Run
- Output: run record, artifacts, pass/fail summary
- Coding expectation: none unless a fix is required

Git
- Output: commit/PR data and approval record
- Coding expectation: none

Docker Integration (Dry-Run Stage)
Current Status
- Docker Build and Docker Run wired as temporary controls.

Target Behavior
- Dry-Run stage invokes Docker Build and Docker Run in sequence.
- Build and Run results are stored as stage artifacts.
- Dry-Run exit criteria requires successful Docker Run or approved exception.

Dry-Run Flow (Target)
1) Validate stage passes.
2) Dry-Run triggers Docker Build with stage-specific context.
3) If Build fails: loop to Implement with reason_code=SCRIPT_ERROR.
4) If Build succeeds: trigger Docker Run.
5) If Run fails: classify failure (SCRIPT_ERROR, LOCATOR_MISSING, ENV_DOWN, DATA_SETUP_FAILED).
6) If Run succeeds: proceed to Git.

Looping Strategy (Enterprise)
Looping is output-driven.
- Plan -> Design if scope and acceptance criteria are stable.
- Design -> Plan if situation changes or scope mismatches.
- Implement <-> Validate for coverage and correctness.
- Validate -> Implement when gaps exist.
- Dry-Run -> Implement or Design based on root cause.

LLM Profile Strategy per Stage
Default: Use tenant default profile unless stage override is set.

Recommended Overrides
- Implement: code-specialized profile if available.
- Validate: challenger profile for critique.
- Dry-Run: default profile for triage only.

Prompt Management
- Each stage prompt stored in DB with version.
- Stage execution must record prompt version.
- UI must expose stage prompt edit for admin only.

MCP and Repo Binding
- Implement and Git stages require MCP bindings for repo access.
- Dry-Run uses repo bindings for Docker context and artifacts.
- MCP failures must halt and require operator action.

Stage Accuracy Controls
- Validate must cross-check requirements to code coverage.
- Dry-Run must include artifact evidence.
- Git must block without approval and Dry-Run success.

Operational Metrics
- Stage lead time and loop counts
- Dry-Run pass rate
- Coverage completeness vs scope
- Defect leakage per stage

Implementation Plan (Phased)
Phase 1: Stage Prompt and Profile Infrastructure
- Add aa_stage_prompt table and API.
- Add aa_stage_llm_profile mapping.
- Update AA runner to load per-stage profile and prompt version.

Phase 2: Docker Dry-Run Integration
- Wire Docker Build/Run to Dry-Run stage.
- Store build/run logs as artifacts.
- Map failure taxonomy to loop targets.

Phase 3: Looping Engine
- Implement stage loop routing based on output metadata.
- Persist aa_stage_loop records.
- Expose loop history in UI.

Phase 4: Validation Hardening
- Add challenger LLM for Validate stage.
- Enforce coverage thresholds and requirement alignment.

Phase 5: Governance and Audit
- Enforce approvals and audit logging across stages.
- Add artifact viewer and stage status SLA.

UI Changes (Demo Page)
- Stage LLM Profile dropdown per stage.
- Stage prompt version selector (admin only).
- Loop reason selection and history log.
- Dry-Run status view linked to Docker tabs.

Acceptance Criteria
- Each stage uses a persisted prompt with a recorded version.
- Stage-specific LLM profile selection works and falls back safely.
- Docker Build and Run are part of Dry-Run stage.
- Looping is driven by output and logged with reason codes.
- AA produces code changes for Implement stage with traceability.
