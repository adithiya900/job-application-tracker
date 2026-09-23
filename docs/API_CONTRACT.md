# Job Application Tracker — Frozen API Contract (Day 20)

**Frozen on:** Day 20 (Backend Integration Test & Freeze)
**Machine-readable contract:** [`openapi.json`](../openapi.json) (OpenAPI 3.0.3, generated from `/swagger.json` via `convert_openapi.py`)
**Base URL (dev):** `http://127.0.0.1:5000`
**Auth:** JWT Bearer tokens (`Authorization: Bearer <access_token>`), refresh via `POST /refresh`.

## Freeze Policy

1. This contract is **frozen** for frontend integration. Existing response shapes must not change.
2. **No removals or renames.** Both `/applications*` and `/api/applications*` aliases stay — some clients use the bare form, some use the `/api` form.
3. `/api/v1/*` and `/api/v2/*` versioned blueprints remain available and untouched.
4. New fields may be **added** to responses (backward compatible). Fields must never be removed or repurposed.
5. Breaking changes require a new version prefix (`/api/v3`) — never an in-place change.

## Endpoints (frozen)

| Method | Path | Auth | Success | Notes |
|---|---|---|---|---|
| POST | `/register` | none | 201 | name, email, password required |
| POST | `/login` | none | 200 | returns access + refresh tokens |
| POST | `/logout` | JWT | 200 | revokes token |
| POST | `/refresh` | refresh JWT | 200 | returns new access token |
| GET | `/api/health` | none | 200 | `{status, database, redis}` |
| GET | `/applications`, `/api/applications` | JWT | 200 | `search`, `status`, `sort`, `page`, `per_page` query params |
| POST | `/applications`, `/api/applications` | JWT | 201 | company + role required; duplicate → 409 |
| GET | `/applications/<id>`, `/api/applications/<id>` | JWT | 200 | 404 if not owned |
| PUT/PATCH | `/applications/<id>`, `/api/applications/<id>` | JWT | 200 | partial update allowed |
| DELETE | `/applications/<id>`, `/api/applications/<id>` | JWT | 200 | 404 if not owned |
| GET | `/dashboard/statistics`, `/api/applications/stats` | JWT | 200 | status-wise counts |
| GET | `/api/analytics` | JWT | 200 | Redis cached 300s |
| GET | `/api/applications/export` | JWT | 200 | CSV download |
| POST | `/api/applications/import` | JWT | 200 | multipart CSV upload |
| GET | `/api/applications/import/errors` | JWT | 200 | last import row errors |
| POST | `/api/applications/bulk-status` | JWT | 200 | `{ids[], status}` |
| GET | `/api/applications/<id>/resume` | JWT | 200 | resume file download |
| GET | `/api/applications/<id>/resume/text` | JWT | 200 | extracted resume text + skills |
| GET | `/api/jobs/search` | JWT | 200 | `q` required; Adzuna backed; 502/503 on external failure |
| GET | `/api/admin/users` | admin JWT | 200 | `{users[], count}` |
| POST | `/api/admin/users/<id>/impersonate` | admin JWT | 200 | 400 self, 404 missing; audited |
| DELETE | `/api/admin/users/<id>` | admin JWT | 200 | 400 self, 404 missing; audited |
| POST | `/notifications/weekly-digest` | JWT | 200 | email digest (Mailtrap in dev) |
| GET | `/swagger.json` | none | 200 | Swagger 2.0 document |
| GET | `/swagger` | none | 200 | Swagger UI |

## Error format

All errors return `{ "error": "<message>" }` with an appropriate 4xx/5xx status.

## Rate limiting

Default `100 per minute` per IP (env: `RATE_LIMIT_DEFAULT`). Exceeding returns `429 Too Many Requests`.

## Full schemas

Request/response schemas, parameters and status codes for every operation are in **`openapi.json`** — import it into Postman, Swagger UI, or openapi-generator.
