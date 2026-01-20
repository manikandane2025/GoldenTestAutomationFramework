# GoldenAutomationFramework AI Context

Purpose
This folder contains the official knowledge base for the Test Automation Architect agent and human contributors. It is designed to be uploaded into the STLC Knowledge Base so the agent can follow framework boundaries, conventions, and quality gates.

Audience
- Automation Architect and reviewers
- Test Case Developers and automation engineers
- DevOps and release teams
- Audit and compliance reviewers

Files and Intent
- 01_Framework_Overview.md: architecture, boundaries, and core rules
- 02_Dos_and_Donts.md: non negotiable coding rules and anti patterns
- 03_Tagging_Conventions.md: tags, routing, and traceability
- 04_Execution_Logs_and_Reports.md: where to find evidence and how to read it
- 05_Runtime_Troubleshooting.md: common failures and fixes
- 06_AA_Workflow_and_HITL.md: stage flow, approvals, and loop rules
- 07_CICD_and_Runners.md: pipeline guidance and runner usage
- 08_Linting_and_Quality_Gates.md: quality gates before commit
- 09_Data_Factory_Patterns.md: test data strategy and patterns
- 10_AA_Situation_Identification_Plan.md: scope detection and user confirmation
- 11_AA_Stage_Lifecycle.md: consolidated stage lifecycle and HITL behavior
- 12_Docker_FileOps_Scope.md: Docker-based file operations scope and guardrails

Usage Rules
- Keep guidance actionable and framework specific.
- Use ASCII only.
- Do not invent architecture beyond the framework boundaries.
- If behavior changes, update this folder first and then update code.
- Keep examples minimal and realistic.

Update Process
- Add new sections when new tooling or conventions are introduced.
- Review for clarity after each framework change.
- Align terminology with runner.py and test_runner_instance.json.
