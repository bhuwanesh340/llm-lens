# Tasks: Project-Scoped Tracing & Professional UI Theme

**Feature Branch**: `002-project-tracing-and-theme`

**Spec**: [spec.md](./spec.md)

**Depends on**: Feature 001 (Phases 1-7 complete)

## Decisions

| Decision | Choice |
| --- | --- |
| Terminology | Rename `Application` → `Project` across DB, API, and UI |
| Unknown project name on a trace | Auto-create the project (LangSmith behavior) |
| Theme | Dark base with teal/lime accents |
| Attribution precedence | Project API key wins over `metadata.project` name |
| Key hashing | SHA-256 (keys are high-entropy; bcrypt is for low-entropy passwords) |

---

## Phase 1: Rename Application → Project (Foundational) 🎯 BLOCKING

**Goal**: Consistent "project" terminology end-to-end, with zero data loss.

**Independent Test**: Existing traces remain attributed correctly after migration; all backend quality gates pass.

- [ ] T101 [P] Rename model `Application` → `Project` in backend/app/db/models/application.py → backend/app/db/models/project.py; add `auto_created` boolean (FR-106)
- [ ] T102 Rename `application_id` → `project_id` FK in backend/app/db/models/request.py (incl. index name)
- [ ] T103 Rename `application_id` → `project_id` FK in backend/app/db/models/api_key.py
- [ ] T104 Update model exports in backend/app/db/models/__init__.py and backend/app/db/base.py imports
- [ ] T105 Write Alembic migration renaming `applications` → `projects`, `llm_requests.application_id` → `project_id`, `api_keys.application_id` → `project_id`, and adding `projects.auto_created` (FR-125)
- [ ] T106 [P] Rename backend/app/schemas/applications.py → projects.py (`ProjectCreate`, `ProjectUpdate`, `ProjectResponse`)
- [ ] T107 [P] Rename backend/app/services/application_service.py → project_service.py (`DuplicateSlugError` retained)
- [ ] T108 Rename `get_costs_by_application` → `get_costs_by_project` and group column in backend/app/services/analytics_service.py
- [ ] T109 Rename `application_id` filter → `project_id` (retaining `"unassigned"` sentinel) in backend/app/services/query_filters.py (FR-104)
- [ ] T110 Rename backend/app/api/v1/applications.py → projects.py with prefix `/projects`; update backend/app/api/router.py
- [ ] T111 Rename `/costs/by-application` → `/costs/by-project` in backend/app/api/v1/costs.py
- [ ] T112 Update `application_id` → `project_id` across backend/app/api/deps.py and all v1 route filter params
- [ ] T113 [P] Rename backend/tests/api/test_applications.py → test_projects.py and update all `application_*` references in backend/tests/

**Checkpoint**: `uv run ruff check .`, `uv run mypy app`, `uv run pytest` all pass.

---

## Phase 2: Project Tagging by Name (US1 - P1) 🎯 MVP

**Goal**: Any external codebase can attribute traces by human-readable project name, with auto-creation.

**Independent Test**: From a clean DB, send a gateway request tagged with an unseen project name; confirm the project is created and the trace attributed.

### Tests

- [ ] T114 [P] [US1] Unit tests for project name normalization + slug derivation (case, whitespace, empty, over-length) in backend/tests/unit/test_project_resolution.py (FR-103, FR-107)
- [ ] T115 [P] [US1] Integration test: auto-create on first trace, reuse on second, concurrent-same-name creates exactly one (FR-102, FR-105) in backend/tests/integration/test_project_autocreate.py

### Implementation

- [ ] T116 [US1] Implement `normalize_project_name()` + `resolve_or_create_project()` in backend/app/services/project_service.py, using an atomic upsert so concurrent inserts collapse to one row (FR-102, FR-103, FR-105, FR-107)
- [ ] T117 [US1] Add optional `project` (name) field to `RawTelemetryEvent` and resolved `project_id` to `NormalizedTelemetryEvent` in backend/app/telemetry/events.py (FR-101)
- [ ] T118 [US1] Resolve project name → `project_id` during ingestion in backend/app/telemetry/collector.py, applying key-over-name precedence (FR-101, FR-116, FR-119)
- [ ] T119 [US1] Forward `metadata.project` from the gateway in litellm/custom_callbacks.py
- [ ] T120 [US1] Document project tagging (metadata field, auto-creation, precedence) in README.md

**Checkpoint**: A trace tagged `{"metadata": {"project": "my-app"}}` creates and attributes to project `my-app`.

---

## Phase 3: Project Management UI (US2 - P2)

**Goal**: Operators create and review projects, and filter every analytics view by project.

**Independent Test**: Create a project in the UI, send tagged traces, and confirm its request/token/cost totals.

- [ ] T121 [P] [US2] Rename `applicationsApi` → `projectsApi` and `by-application` → `by-project` in frontend/src/lib/api.ts
- [ ] T122 [P] [US2] Rename `Application*` types → `Project*` and `application_id` → `project_id` in frontend/src/lib/types.ts
- [ ] T123 [US2] Rename `application_id` → `project_id` filter key in frontend/src/lib/use-range-filters.ts
- [ ] T124 [US2] Move frontend/src/app/applications/page.tsx → frontend/src/app/projects/page.tsx; label auto-created projects (FR-106, FR-108)
- [ ] T125 [US2] Update nav link `/applications` → `/projects` in frontend/src/components/nav.tsx
- [ ] T126 [US2] Add a project selector to frontend/src/components/filter-bar.tsx so all views can scope by project (FR-110)
- [ ] T127 [US2] Update the by-project tab in frontend/src/app/costs/page.tsx

**Checkpoint**: Projects page lists both manual and auto-created projects; project filter applies across views.

---

## Phase 4: Project API Keys (US3 - P3)

**Goal**: Per-project credentials that attribute traces without a name tag, and can be revoked.

**Independent Test**: Generate a key, submit a trace with it, confirm attribution, revoke it, confirm rejection.

### Tests

- [ ] T128 [P] [US3] API tests for key generate/list/revoke, one-time reveal, and post-revocation rejection in backend/tests/api/test_project_keys.py (FR-113 - FR-118)

### Implementation

- [ ] T129 [US3] Implement key generation (`llk_` prefix, SHA-256 hash, non-secret display prefix), verification, and revocation in backend/app/services/api_key_service.py (FR-114, FR-115, FR-117)
- [ ] T130 [US3] Add `ApiKeyCreate`, `ApiKeyResponse` (no secret), `ApiKeyCreatedResponse` (secret once) to backend/app/schemas/api_keys.py (FR-114)
- [ ] T131 [US3] Implement `POST/GET /api/v1/projects/{id}/keys` and `DELETE /api/v1/keys/{key_id}` in backend/app/api/v1/api_keys.py; register in router (FR-113, FR-117)
- [ ] T132 [US3] Accept a project API key on the telemetry ingestion endpoint and attribute to its project, updating `last_used_at` (FR-116, FR-118)
- [ ] T133 [P] [US3] Build key management UI (generate, one-time reveal with copy, revoke) in frontend/src/app/projects/[projectId]/page.tsx
- [ ] T134 [US3] Document project API key issuance and usage in README.md

**Checkpoint**: A revoked key is rejected; historical traces survive key deletion.

---

## Phase 5: Professional Dark Theme (US4 - P4)

**Goal**: A cohesive dark teal/lime interface across every page.

**Independent Test**: Every page renders in the dark theme with legible charts and accessible contrast.

- [ ] T135 [US4] Replace zero-chroma tokens with a dark teal/lime palette (background, foreground, card, primary, accent, border, ring, destructive, and `--chart-1..5`) in frontend/src/app/globals.css (FR-120, FR-121, FR-123)
- [ ] T136 [US4] Apply the dark class and theme metadata in frontend/src/app/layout.tsx
- [ ] T137 [P] [US4] Restyle nav with active-state accent and brand mark in frontend/src/components/nav.tsx
- [ ] T138 [P] [US4] Restyle the login screen in frontend/src/app/login/page.tsx
- [ ] T139 [US4] Apply themed chart colors and grid/axis/tooltip styling in frontend/src/app/page.tsx
- [ ] T140 [P] [US4] Add icon/text status affordances so state is not conveyed by color alone across status badges (FR-122)
- [ ] T141 [US4] Normalize spacing, headings, and card styling across all dashboard pages (FR-124)

**Checkpoint**: All pages render consistently; `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` pass.

---

## Phase 6: Validation

- [ ] T142 Update contracts/api.md and data-model.md for project terminology, key endpoints, and the `auto_created` field
- [ ] T143 Run full backend gates (`ruff`, `mypy app`, `pytest`) and frontend gates (`lint`, `typecheck`, `test`, `build`)
- [ ] T144 End-to-end validation against SC-101 - SC-108 with a live stack

---

## Dependencies

```
Phase 1 (rename) ──> Phase 2 (name tagging) ──> Phase 3 (project UI)
                                    │
                                    └────────> Phase 4 (API keys)

Phase 5 (theme) ── independent of Phases 1-4, but Phase 3 pages should exist first
```

- **Phase 1 blocks everything** — it renames the entities all later phases build on.
- **Phase 2 is the MVP**: it alone delivers f1 + the core of f2.
- **Phase 5 is independent** and can be done in parallel with Phases 2-4.
