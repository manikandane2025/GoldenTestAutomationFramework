# Tagging Conventions

Purpose
Tags control execution scope, CI routing, and traceability. They must be consistent across features and scenarios.

Where to Tag
- features/ files for scenario level tags.
- Use a consistent prefix for pipeline routing.
- Keep tags in lowercase with hyphens, no spaces.

Core Tag Groups
- @smoke, @regression, @e2e
- @ui, @api, @integration, @performance, @security
- @feature:<feature_name>
- @req:<requirement_id>
- @story:<story_id> (optional)
- @owner:<team_or_role>
- @risk:<low|medium|high>

Recommended Tag Set (Minimum)
- Every scenario must include one of: @smoke, @regression, @e2e
- Include one of: @ui, @api, @integration
- Include @feature:<name> and @req:<id> when available

Examples
- Scenario: Login happy path
  Tags: @smoke @ui @feature:auth @req:HNE-001 @risk:high

- Scenario: Eligibility API validation
  Tags: @api @regression @feature:eligibility @req:HNE-014 @risk:medium

Operational Rules
- Do not create freeform tags outside the approved set.
- Avoid tags that encode environment names.
- Use test_runner_instance.json to select tags for runs.

Traceability Tips
- Map @req to Jira or ADO IDs.
- Add @story when the user provides a story list.
- Keep tags consistent so reports can aggregate by tag.
