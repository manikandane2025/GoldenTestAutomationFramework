# Automation Architect Situation Identification Plan

## Purpose
Define how the Automation Architect identifies the project situation (Sprint Development, Release Hardening, Backlog Automation, Maintenance) from user inputs and confirms with the user before proceeding.

## Goals
- Classify execution context early and reliably.
- Require explicit user confirmation for ambiguous or mixed scopes.
- Align behavior with SDLC cycles (sprint, release, backlog, refactor).
- Support overrides with an audit trail when needed.

## Inputs
- User scope: Sprint or Release selection plus story list.
- Story metadata: sprint, release, status, labels, tags, priority.
- Environment readiness signals: feature flags, build version, deployment date.
- History: prior automation runs for same story IDs (optional).

## Situation Taxonomy (Analytics Driven)
The agent derives the situation using weighted signals, not fixed if/else chains. It computes a confidence score per category and only asks for confirmation when confidence is below a threshold or mixed.

### Primary Situations
1) Sprint Development
   - High share of stories in active sprint.
   - Status in Active, QA, Ready for Test.
   - Recent updates in the last N days.
2) Release Hardening
   - Stories span multiple sprints but share a release.
   - High ratio of QA or UAT statuses.
3) Backlog Automation
   - Stories closed long ago or missing sprint.
   - Little recent activity; stable requirements.
4) Maintenance or Refactor
   - Request focuses on updating existing scripts, no new features.
   - High overlap with existing automation assets.
5) Mixed Scope
   - Multiple categories above threshold at the same time.

### Scenario Catalog (Examples)
- New feature in active sprint
- Spillover story from previous sprint
- Feature flag on but deployment pending
- Release stabilization with defects
- Hotfix release with urgent priority
- Backlog automation for closed stories
- Legacy system script refresh
- API contract change without UI change
- UI redesign with high locator volatility
- Localization only changes
- Environment not ready
- Test data unavailable
- Auth or SSO change in progress
- Parallel streams in same release

## Scenario Dimensions (Reduce If/Else)
Classify along orthogonal dimensions, then map to the closest situation:
1) Timeline: sprint active, release window, backlog, maintenance
2) Readiness: deployed, flagged, blocked
3) Risk: high, medium, low
4) Change type: UI, API, data, infra, mixed
5) Stability: volatile vs stable
6) Intent: new automation vs refactor vs regression expansion

## Confidence Model (Explainable)
Each situation gets a score using weighted signals:
- SprintMatchRatio
- ReleaseMatchRatio
- StatusDistribution
- RecencyScore
- StoryAgeScore
- BacklogTagPresence
- VolatilityScore
- ExistingAutomationOverlap

If the top score is below threshold or close to the runner up, mark as Mixed or Uncertain and ask for confirmation.

## Resolution Strategy for Mixed or Uncertain
- Offer split recommendations with minimal clicks:
  - Split by sprint vs backlog
  - Split by release vs non release
  - Proceed as combined with override
- Default to the least risky split.

## Blocked or Defer Scenarios
If blocked, do not proceed to implement without explicit override:
- Feature not deployed (flag off or missing build)
- Environment down or unstable
- Test data unavailable
- Auth or SSO changes in progress
- Third party dependency unavailable

## Jira and ADO Signal Map
### Jira fields
- sprint, fixVersion, status, updated, created, labels, components
- issuetype, priority, resolutiondate
- custom: feature flag, deployment status, environment readiness

### Azure DevOps fields
- Iteration Path, Release or Tags, State, Changed Date, Created Date
- Area Path, Work Item Type, Tags
- custom: environment readiness, feature toggle, build version

## Excel or Demo Fields (Recommended)
To emulate Jira and ADO analytics in demo input:
- sprint, release, status, created_date, updated_date, closed_date
- labels or tags, component or module, priority, story_points
- deployment_status, feature_flag, env_ready
- automation_exists, script_owner, last_automation_update
- change_frequency (High, Med, Low)

## Mapping Guidance
- EPIC to Feature to Story to Test Cases (manual) to Automation.
- If manual test cases are missing, prompt to generate them or call Test Case Developer.
- If multiple scopes exist, split runs or require override.

## Example Decision Summary (User Facing)
- Situation: Sprint Development (0.78 confidence)
- Top signals: sprint match 85 percent, recent updates 7 days, status active and QA
- Action: proceed to plan and enforce readiness gate

## Confirmation Flow (Low Friction)
1) Agent proposes detected situation with top signals.
2) User confirms or changes with one click.
3) If Mixed or Uncertain: offer 2 to 3 suggested splits.
4) Store confirmation in run metadata.

## Overrides
Allow user override with:
- Reason code (enum)
- Short justification
- Approval required (HITL)
- Optional expiry per work order

## Behavior by Situation
- Sprint Development:
  - Enforce feature readiness gate.
  - Dry-Run required before Git.
- Release Hardening:
  - Gate required; allow limited override.
  - Higher validation emphasis.
- Backlog Automation:
  - Gate may be overridden.
  - Dry-Run required if execution requested.
- Maintenance or Refactor:
  - Gate optional if no execution planned.
- Mixed Scope:
  - Prefer split into separate runs.

## Data Model (Proposed)
- situation_detected: string
- situation_confirmed: string
- situation_override: { reason, comment, by, at, expires_at }

## Acceptance Criteria
- Agent asks for confirmation when confidence is low or mixed.
- Mixed scope is explicitly flagged.
- User choice is persisted and visible in timeline details.
