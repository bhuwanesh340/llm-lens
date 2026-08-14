# Feature Specification: Project-Scoped Tracing & Professional UI Theme

**Feature Branch**: `002-project-tracing-and-theme`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "(f1) since this is an observability project, the LLM calls can be measured for any project not just our project — make it identical to how LangSmith is used to measure and trace LLM calls. (f2) user should have option to create a project on UI and use that project name to tag the LLM traces (as done in LangSmith), otherwise we won't know for which project how much cost is incurred. (f3) the UI is currently a plain white screen — it should show professionalism; add teal green / lime professional background and screens."

## Context & Relationship to Feature 001

Feature 001 delivered the observability foundation: a unified gateway, telemetry capture, cost/usage/error analytics, and a request explorer. It included an `applications` entity that attributes cost per application.

This feature closes three gaps that prevent the platform from being used as a general-purpose, LangSmith-equivalent tracing tool:

1. **Attribution requires an internal UUID.** Tagging a trace today requires passing `metadata.application_id` as a raw database UUID. An external team cannot reasonably discover or hard-code that, so in practice all external traffic lands in "unassigned".
2. **No per-project credentials.** The `api_keys` table exists but is unused — there is no way to issue, list, or revoke a key, so every caller must share the single gateway master key. There is no way to attribute or revoke access per project.
3. **The dashboard has no visual identity.** All theme tokens are zero-chroma greyscale, rendering as an undifferentiated white screen.

**Terminology decision**: The existing `Application` entity *is* the project concept. This feature renames it to **Project** across the database, API, and UI to match the established industry vocabulary (LangSmith, Langfuse, W&B). There is no separate new entity.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trace Any External Project by Name (Priority: P1)

A developer with an unrelated existing codebase points their LLM client at the platform's gateway and adds a single project name to their request metadata. Their traces immediately appear attributed to that project, with no prior setup in the dashboard.

**Why this priority**: This is the core of f1+f2. Without human-readable project tagging, cost cannot be attributed per project, which is the primary reason to adopt the tool.

**Independent Test**: From a clean database, send a request through the gateway tagged with a previously unseen project name, and confirm a project is created automatically and the trace is attributed to it.

**Acceptance Scenarios**:

1. **Given** the platform is running, **When** a request is sent through the gateway with a project name in its metadata, **Then** the trace is recorded and attributed to a project of that name.
2. **Given** a project name has never been seen before, **When** a trace arrives tagged with it, **Then** the project is created automatically and the trace is attributed to it without error.
3. **Given** a project already exists with that name, **When** further traces arrive tagged with it, **Then** they attach to the existing project rather than creating a duplicate.
4. **Given** a trace arrives with no project tag, **When** analytics are viewed, **Then** it is grouped under "unassigned" exactly as before.
5. **Given** two project names differ only by letter case or surrounding whitespace, **When** traces arrive for both, **Then** they resolve to the same project rather than creating near-duplicates.

---

### User Story 2 - Manage Projects from the Dashboard (Priority: P2)

A team lead opens the dashboard, creates a project ahead of time, gives it a description and environment, and later reviews exactly how much that project has cost.

**Why this priority**: Explicit project management makes attribution intentional rather than incidental, and is required for the per-project cost view that motivates f2.

**Independent Test**: Create a project in the UI, send traces tagged with its name, and confirm the project view shows that project's own request count, token totals, and cost.

**Acceptance Scenarios**:

1. **Given** the user is on the projects page, **When** they create a project with a name, **Then** it appears in the project list and is immediately usable as a trace tag.
2. **Given** traces exist for several projects, **When** the user views project analytics, **Then** each project shows its own request count, token totals, and total cost.
3. **Given** a project was auto-created by an incoming trace, **When** the user views the projects page, **Then** it is listed and visually distinguishable from manually created projects.
4. **Given** the user renames or deletes a project, **When** they confirm the action, **Then** analytics reflect the change and previously recorded traces are never silently destroyed.
5. **Given** the user selects a project, **When** they apply it as a filter, **Then** every analytics view scopes to that project.

---

### User Story 3 - Issue and Revoke Per-Project API Keys (Priority: P3)

An operator issues a dedicated key to one project's team so that team can send traces without sharing the platform-wide master credential, and revokes that key when the project ends.

**Why this priority**: Required for f1's "any project" goal in a multi-team setting; secondary to name-based tagging working at all.

**Independent Test**: Generate a key for a project, use it to submit a trace, confirm the trace is attributed to that project without any metadata tag, then revoke the key and confirm subsequent submissions are rejected.

**Acceptance Scenarios**:

1. **Given** a project exists, **When** the operator generates an API key for it, **Then** the full key value is displayed exactly once and never retrievable again.
2. **Given** an API key has been generated, **When** the operator views the key list, **Then** only a non-secret prefix, name, creation time, and last-used time are shown.
3. **Given** a valid project API key is used to submit a trace, **When** the trace is recorded, **Then** it is attributed to that key's project without requiring any project name in the payload.
4. **Given** an API key is revoked, **When** it is used again, **Then** the request is rejected with a clear authentication error.
5. **Given** a key is deleted, **When** previously recorded traces are viewed, **Then** those traces remain intact and attributed to their project.

---

### User Story 4 - Read the Dashboard Comfortably (Priority: P4)

A user opens the dashboard and sees a professional, visually coherent dark interface where key metrics, charts, and states are immediately distinguishable.

**Why this priority**: f3 is a presentation concern — valuable for adoption and daily use, but it does not block correctness of measurement.

**Independent Test**: Open every dashboard page and confirm a consistent dark theme with teal/lime accents, readable contrast, and charts that remain legible.

**Acceptance Scenarios**:

1. **Given** the user opens any dashboard page, **When** it renders, **Then** it uses a consistent dark base with teal and lime accent colors rather than an undifferentiated white background.
2. **Given** a page shows charts, **When** multiple series are displayed, **Then** each series is visually distinguishable and legible against the dark background.
3. **Given** a page shows status information, **When** success, warning, and error states are present, **Then** each is distinguishable by more than color alone.
4. **Given** the user views any text, **When** it renders against its background, **Then** contrast meets accessibility guidance for body text.
5. **Given** the user navigates between pages, **When** each loads, **Then** spacing, typography, and component styling remain consistent.

---

### Edge Cases

- What happens when a project name is supplied that is empty, whitespace-only, or excessively long? It must be rejected or normalized rather than creating an unusable project.
- What happens when a project name collides with an existing project's generated identifier? Resolution must be deterministic and must not create duplicates.
- What happens when two traces for the same brand-new project arrive simultaneously? Exactly one project must be created; neither trace may be lost.
- What happens when a trace supplies both a project API key and a conflicting project name in metadata? Precedence must be explicit and documented.
- What happens when a project is deleted while traces still reference it? Historical traces must be preserved and must not break analytics.
- What happens when an API key is presented for a project that has since been deleted? The request must fail clearly rather than attributing to an arbitrary project.
- How does the interface behave for users who cannot distinguish teal from lime? Status must not be conveyed by hue alone.

## Requirements *(mandatory)*

### Functional Requirements

#### Project attribution (f1, f2)

- **FR-101**: System MUST allow a trace to be attributed to a project using a human-readable project **name**, without requiring the caller to know any internal identifier.
- **FR-102**: System MUST automatically create a project when a trace arrives referencing a project name that does not yet exist.
- **FR-103**: System MUST resolve project names deterministically, treating names that differ only by case or surrounding whitespace as the same project.
- **FR-104**: System MUST record traces that carry no project reference under a clearly labelled "unassigned" grouping.
- **FR-105**: System MUST guarantee that concurrent traces referencing the same new project name result in exactly one project being created, with no trace lost.
- **FR-106**: System MUST distinguish projects created automatically from those created explicitly by an operator.
- **FR-107**: System MUST reject project names that are empty, whitespace-only, or exceed the supported length, with a clear error.

#### Project management (f2)

- **FR-108**: System MUST let an operator create, view, update, and delete projects from the dashboard.
- **FR-109**: System MUST report request count, token totals, and total cost per project.
- **FR-110**: System MUST allow every analytics view to be filtered by project.
- **FR-111**: System MUST preserve previously recorded traces when their project is deleted, without corrupting historical analytics.
- **FR-112**: System MUST expose all project capabilities through the documented API, so the dashboard requires no direct storage access.

#### Project credentials (f1)

- **FR-113**: System MUST allow an operator to issue named API keys scoped to a specific project.
- **FR-114**: System MUST display a newly generated key exactly once and MUST NOT store or expose the raw key value thereafter.
- **FR-115**: System MUST store only a non-reversible hash of each key plus a short non-secret prefix for identification.
- **FR-116**: System MUST attribute a trace submitted with a valid project API key to that key's project without requiring any project name in the payload.
- **FR-117**: System MUST allow an operator to revoke a key, after which it MUST be rejected.
- **FR-118**: System MUST record when each key was last used, without recording the key itself.
- **FR-119**: System MUST define and document explicit precedence when both a project key and a project name are supplied.

#### Interface (f3)

- **FR-120**: System MUST present a consistent dark visual theme using teal and lime accent colors across every dashboard page.
- **FR-121**: System MUST render charts legibly against the dark background with visually distinguishable series.
- **FR-122**: System MUST convey status through more than color alone.
- **FR-123**: System MUST meet accessibility contrast guidance for body text and interactive controls.
- **FR-124**: System MUST apply consistent spacing, typography, and component styling across all pages.

#### Migration

- **FR-125**: System MUST migrate all existing application records and their trace associations to projects without data loss.
- **FR-126**: System MUST use consistent "project" terminology across the database, API, and interface.

### Key Entities

- **Project**: A named unit of work that LLM traces are attributed to (the renamed `Application`). Carries a display name, a stable derived identifier, optional description and environment, an origin marker distinguishing automatic from explicit creation, and timestamps.
- **Project API Key**: A revocable credential scoped to exactly one project, persisted only as a non-reversible hash plus a non-secret display prefix, with a name and last-used timestamp.
- **LLM Request (usage record)**: Unchanged from feature 001 except that its attribution now references a Project.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: A developer can attribute traces from an entirely separate codebase to a named project by adding a project name to their request, with no prior dashboard setup and no knowledge of internal identifiers.
- **SC-102**: 100% of traces carrying a project name are attributed to a project of that name; none fall through to "unassigned".
- **SC-103**: Sending traces concurrently for the same new project name yields exactly one project, with every trace recorded.
- **SC-104**: Recalculating any project's total cost from its individual traces matches the displayed project total with zero discrepancy.
- **SC-105**: A raw API key value is retrievable exactly once at creation and is unrecoverable from storage or any API response thereafter.
- **SC-106**: A revoked key is rejected on its next use, with no successful submissions after revocation.
- **SC-107**: Every existing application record and its associated traces remain intact and correctly attributed after migration, with zero orphaned traces.
- **SC-108**: Every dashboard page renders in the dark teal/lime theme, with body text meeting contrast guidance.

## Assumptions

- Project names are chosen by the callers themselves; the platform does not enforce a naming policy beyond length and emptiness validation.
- Auto-creation is the desired default (matching LangSmith); operators who want stricter control can rely on per-project API keys instead of open name-based tagging.
- A project API key identifies a project, not an end user; per-user identity and role-based access remain out of scope, consistent with feature 001's single-admin assumption.
- Nested traces, spans, and multi-step chain/agent tracing are out of scope for this feature; the unit of attribution remains a single LLM request.
- The dark theme is the single supported appearance for this feature; a light/dark toggle is a possible future enhancement.
- Existing deployments are development-stage, so a one-way rename migration is acceptable without a backward-compatibility shim.
