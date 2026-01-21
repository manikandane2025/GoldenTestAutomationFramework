# Automation Architect Lift Journey (Unified Run + Looping)

Purpose
Define the end-to-end "lift journey" for the Automation Architect (AA) agent using a single unified run id, per-stage execution, and loop path control. This document clarifies how stages, outputs, and artifacts are combined, and how loop paths are executed safely.

Audience
- Automation Architect agent
- Human reviewer and approver
- Platform and DevOps teams

Guiding Principles
- One AA run id per workflow execution.
- Stage runs append to a unified AA run summary.
- Implement stage produces file_changes and triggers repo workflow actions (apply, dry_run, push).
- Loop path is explicit, observable, and auditable.
- HITL gates are enforced at policy-defined points (Git mandatory, others configurable).

Core Concepts
- AA Run Id: Stable id for a workflow execution across all stages.
- Stage Task Run: A single-stage action (Plan, Design, Implement, Validate, Dry-Run, Git).
- Run Summary: Aggregated output across stages under the same AA run id.
- Repo Workflow: Container actions that apply diffs and capture artifacts.
- Loop Path: Implement <-> Validate <-> Dry-Run cycle driven by evidence and failure codes.

Unified Run Model (Best Option)
1) Start AA Run
   - Create AA run id.
   - Initialize stage states and empty stage outputs.
   - Store scope metadata (sprint/release), inputs, and selected LLM profile.

2) Run Stage Task (Plan/Design/Implement/Validate/Dry-Run/Git)
   - Each stage appends its output to the AA Run Summary.
   - Stage output is persisted with stage_name, status, timestamps, and evidence links.

3) View Full Output
   - Shows the AA Run Summary with per-stage outputs, artifacts, and decisions.
   - Includes loop history and HITL decisions.

UI Journey (Target)
- Agent-level button: Run AA Workflow
  - Starts or resumes the unified AA run id.
- Stage-level button: Run Stage Task
  - Executes only the current stage and appends output to the run.
- View Full Output
  - Displays combined output for the run id.

Stage Outputs (Aggregated)
- Plan: risks, dependencies, approvals, scope metadata, decision log.
- Design: scenario matrix, locator policy, data plan, validation checklist.
- Implement: file_changes, diff summary, repo artifacts, framework extensions.
- Validate: validation report, gaps, recommended loop stage.
- Dry-Run: run record, logs, evidence, recommended loop stage.
- Git: commit hash, PR link, approval record.

Repo Workflow (Container)
1) Clone framework repo and app repo into container workspace.
2) Apply file_changes (apply).
3) Capture artifacts: console stdout/stderr, framework.diff, app.diff.
4) Dry-run optionally executes runner.py --dry-run.
5) Push to Git only after approvals and Dry-Run success.

Loop Path Mechanics
- Loop path is Implement <-> Validate <-> Dry-Run.
- Loop is triggered by outcome codes:
  - SCRIPT_ERROR, LOCATOR_MISSING -> Implement
  - VALIDATION_GAP -> Implement
  - FLAKY -> Dry-Run retry (max 1) then Validate
  - ENV_DOWN, DATA_SETUP_FAILED, AUTH_FAILED -> Pause and HITL
- Loop iteration rules:
  - Each loop iteration must record the reason_code and change summary.
  - Output append is idempotent and tagged with iteration number.
  - Run Summary includes loop count and final resolution.

HITL Gates
- Required for Git stage.
- Optional for Plan/Design/Implement unless policy marks as required.
- Required for ambiguous failures in Dry-Run or Validate.
- Approval record includes approver, timestamp, and comment.

State Model (Minimal)
- run_id
- current_stage
- stage_statuses (queued, running, completed, failed, blocked)
- stage_outputs (per stage, per iteration)
- loop_history (from_stage, to_stage, reason_code, at)
- approvals (stage_name, status, by, at, comment)
- artifacts (links per stage and repo workflow)

Failure Handling
- If a stage fails, mark stage status = failed and attach error metadata.
- If repo workflow fails, stage status = blocked and loop decision required.
- If dry-run fails, record failure category and recommended loop stage.

Visibility
- Timeline shows stage status and loop transitions.
- Agent Execution shows repo workflow logs and diffs.
- View Full Output shows combined per-stage outputs for the run id.

Actionable Next Steps
- Implement unified AA run id and aggregated run summary in backend.
- Update UI to use Run AA Workflow (agent-level) and Run Stage Task (stage-level).
- Update View Full Output to render the aggregated run summary.
- Enforce loop history and stage iteration metadata.

Non-Negotiable Rules
- One AA run id per workflow execution.
- Do not push to Git without approval and Dry-Run evidence.
- Each loop iteration must be logged with reason_code and artifacts.
