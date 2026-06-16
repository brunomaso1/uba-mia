---
name: group-management-design
description: Full-stack design for user group management feature — backend API, frontend feature, portal page update
metadata:
  type: project
---

# Design: Group Management Feature

**Date:** 2026-06-16
**Stack:** Angular 22 · FastAPI 0.136.3 · PostgreSQL 18.4

---

## 1. Scope

Allow authenticated users to manage expense groups:

- Create a group
- Rename a group
- Delete a group (cascades expenses — no warning, no restriction on who can delete)
- Add another user to a group (no invite/authorization required; once added, cannot be removed)
- View the list of members of a group (detail page)

**Explicitly excluded:** expense recording, splits, settlements, removing members, role-based access control.

---

## 2. Database

No schema changes required. The existing tables are sufficient:

- `groups (id, name, created_by, created_at)`
- `group_member (user_id, group_id, joined_at)` — composite PK prevents duplicates

The only behavioral note: `POST /groups` must insert a row in both `groups` and `group_member` (creator is auto-added as a member).

---

## 3. Backend

### 3.1 New files

| File | Purpose |
|------|---------|
| `backend/app/schemas/group.py` | Pydantic request/response schemas for groups and members |
| `backend/app/services/group.py` | Business logic and DB queries for groups |
| `backend/app/routers/groups.py` | Route handlers for the groups resource |

`backend/app/routers/users.py` gains a `GET /users` list endpoint.

### 3.2 API endpoints

All endpoints are under `/api/v1` and require a valid JWT (enforced by Keycloak middleware).

#### Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users` | List all registered users (id, display_name, email) |
| GET | `/users/me` | Current user profile (existing) |

#### Groups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groups` | List groups where current user is a member |
| POST | `/groups` | Create group; creator auto-added as first member |
| PATCH | `/groups/{id}` | Rename group |
| DELETE | `/groups/{id}` | Delete group (cascades expenses via FK) |
| POST | `/groups/{id}/members` | Add a user to the group by user_id |
| GET | `/groups/{id}/members` | List all members of the group |

### 3.3 Schemas (`schemas/group.py`)

```python
# Request
GroupCreate    { name: str }
GroupRename    { name: str }
AddMemberBody  { user_id: UUID }

# Response
GroupRead      { id, name, created_by, created_at, member_count: int }
MemberRead     { user_id, display_name, email, joined_at }
```

### 3.4 Service logic (`services/group.py`)

- `list_for_user(db, user_id)` — JOIN groups + group_member WHERE user_id = current user; include member count via subquery
- `create(db, name, creator_id)` — insert group, insert group_member row for creator
- `rename(db, group_id, name)` — UPDATE groups SET name
- `delete(db, group_id)` — DELETE groups WHERE id (FK cascade handles members + expenses)
- `add_member(db, group_id, user_id)` — INSERT INTO group_member; ignore if already member (ON CONFLICT DO NOTHING)
- `list_members(db, group_id)` — SELECT users JOIN group_member WHERE group_id

---

## 4. Frontend

### 4.1 Folder structure

```
frontend/src/app/features/groups/
├── groups.service.ts          # HttpClient wrapper for all groups + users endpoints
├── groups.routes.ts           # Lazy-loaded routes: /groups, /groups/:id
├── pages/
│   ├── groups-page/           # ts + html + scss + spec
│   └── group-detail-page/     # ts + html + scss + spec
└── components/
    ├── group-card/            # ts + html + scss + spec — one card per group
    └── add-member-form/       # ts + html + scss + spec — inline add-member
```

### 4.2 Routes

```
/groups       → GroupsPage       (title: 'Mis Grupos')
/groups/:id   → GroupDetailPage  (title: 'Detalle del Grupo')
```

Both are lazy-loaded children of the root AppShell layout route.

### 4.3 GroupsPage (`/groups`)

State managed via `httpResource` — no separate store.

**Layout:** page header with "Mis Grupos" title + "Nuevo grupo" button. Below: grid of `GroupCardComponent`, one per group.

**Create:** "Nuevo grupo" button reveals an inline name input + confirm. On submit → `POST /groups` → refresh resource.

**GroupCardComponent inputs:** `group` (GroupRead), emits `renamed`, `deleted`, `memberAdded`.

**Card contents:**
- Group name (static); edit icon → turns into inline input; on confirm → `PATCH /groups/:id`
- Trash icon → `DELETE /groups/:id` → remove from list
- Member count badge → "Ver miembros" button → `router.navigate(['/groups', id])`
- `AddMemberFormComponent` at card bottom

**AddMemberFormComponent:**
- Autocomplete input bound to `GET /users`
- Filters out users already in the group (uses `GET /groups/:id/members` fetched on card load)
- On select + "Agregar" → `POST /groups/:id/members`

### 4.4 GroupDetailPage (`/groups/:id`)

- Fetches `GET /groups/:id/members` via `httpResource`
- Renders a Material list of members: avatar initial, display name, email, joined date
- Back button → `router.navigate(['/groups'])`

### 4.5 Portal page update

- Remove `UserCardComponent` from `PortalPage`
- Replace with a single Material card: title "Mis Grupos", short description, "Ir a grupos" button linking to `/groups`
- The `UserCardComponent` itself can stay in `shared/components/` for potential future reuse, but is no longer rendered on the portal

### 4.6 Navigation

Add `{ label: 'Grupos', path: '/groups' }` to `navItems` in `AppHeaderComponent`.

---

## 5. Error handling

- `POST /groups/:id/members` with a duplicate user_id → backend uses ON CONFLICT DO NOTHING and returns 200 (idempotent)
- `httpResource` loading/error states surface in each component the same way `UserCardComponent` already does (spinner while loading, error message on failure)
- No optimistic updates — wait for server confirmation before updating the UI

---

## 6. README update

Add a "Group Management" section under Features documenting:
- What the feature does
- The components and pages involved
- The API endpoints it uses
