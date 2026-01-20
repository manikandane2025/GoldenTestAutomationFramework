# Docker File Ops Scope for Automation Architect

Purpose
Define the complete, detailed scope for file operations performed by the Automation Architect inside a Docker container after pulling code from Git. This is the operational contract for safe, auditable, and repeatable automation changes.

Assumptions
- All file operations occur inside a containerized workspace.
- Source code is obtained via MCP Git, not manual local file access.
- The framework boundary rules are enforced before any write.
- Human approval is required before Git push.

Repository and Workspace Tasks
- Clone repository into a container workspace path (isolated per run).
- Checkout or create a branch using naming conventions.
- Verify clean working tree before modifications.
- Pull latest updates from remote.
- Detect and surface merge conflicts early.
- Read repository metadata (README, context.json, runbooks).
- Build a scoped tree view to restrict operations to allowed paths.

Allowed File Operations (Core)
- Create new files under approved directories only.
- Read any file needed for analysis and locator extraction.
- Update existing files via minimal diffs.
- Delete files only when explicitly approved.
- Rename or move files with dependency awareness.
- Normalize line endings and encoding to repository standards.
- Add or update context.json in root folders when required.

Restricted File Operations (Guardrails)
- runner.py and constants.py are protected by default.
- CustomJsonReportFormatter schema is a stable contract (changes require approval).
- Secrets, tokens, or credentials must never be written to repo.
- No writes to system paths outside the workspace mount.

File Targeting and Boundary Enforcement
- features/: high-level test intent, no low-level actions.
- pages/: UI mechanics only, no assertions.
- clients/: API transport only, no assertions.
- Utility/: shared helpers (logging, waits, retry, assertions).
- FrameworkTestDataDatabase/: data setup/cleanup only.
- templates/ and input/: payloads and datasets.
- reports/ and logs/ and output/: generated artifacts only (no hand edits).

Scaffolding and Templates
- Use templates for new feature files, page objects, client stubs.
- Use consistent naming and folder placement.
- Generate minimal placeholder code only when context.json permits.
- Auto-add runbook notes when new flows are introduced.

Dependency Management
- Read requirements.txt or equivalent manifest.
- Add dependencies only with approval and documented rationale.
- Update lock files if present.
- Verify compatibility with current Python/runtime version.

Validation and Static Checks
- Run lint/format if configured for the repo.
- Run lightweight syntax checks for changed files.
- Validate JSON/YAML schema for config changes.
- Fail early if validations fail; return to Implement stage.

Artifact and Audit Capture
- Record a file change manifest (path, action, reason).
- Generate a diff summary for review.
- Store console output and errors under logs/.
- Store run artifacts under output/ or configured artifacts path.

HITL Hooks
- Before writing: present plan and target file list if changes are large.
- Before Git: present diff, validation output, and risk summary.
- Require approval with name, timestamp, and comment.

Git Operations (Post-Approval Only)
- Commit with enforced message format including agent role and stage.
- Push to new branch, never force push.
- Provide repo link, branch, and commit hash.

Error Handling and Recovery
- If conflict: pause and request manual resolution.
- If validation fails: do not commit; fix in correct layer.
- If file write fails: log error and abort run.
- If wrong directory detected: stop and escalate.

Security and Compliance
- No secrets in code; use vault references.
- Mask secrets in logs and artifacts.
- Enforce least privilege on repo access tokens.

Example Workflow (High Level)
1) Clone repo in container and checkout branch.
2) Read context.json and runbooks.
3) Apply changes in allowed directories.
4) Run lint/syntax checks.
5) Generate diff and summary for HITL.
6) Commit and push after approval.

Acceptance Criteria
- No boundary violations.
- No secrets in code or logs.
- Full audit trail for file changes.
- Changes pass configured validations.
