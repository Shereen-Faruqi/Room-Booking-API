# room-booking-api

A tiny room-booking API built with FastAPI and SQLite. It is deliberately small and plain: it exists to give three plain-English policies (see [Policies](#policies)) something real to check.

All data is fake. There is no real authentication, no front end and no third-party service.

## Quick start

Requires Python 3.12 or newer (tested on 3.12 and 3.13).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app
```

The API is now at http://127.0.0.1:8000 and interactive docs are at http://127.0.0.1:8000/docs.

The SQLite database is created as `bookings.db` in the current folder. Set the `BOOKINGS_DB` environment variable to use a different path. Database migrations are applied automatically on startup.

## Demo users (fake)

Login is faked: send a token in the `X-User-Token` header. Two demo users are defined in `config/demo_users.json`.

| User  | Token              |
|-------|--------------------|
| alice | `demo-token-alice` |
| bob   | `demo-token-bob`   |

These are public example values for local use. They are not real credentials.

## API

| Method and path | What it does | Success | Errors |
|---|---|---|---|
| `POST /bookings` | Create a booking owned by the caller | `201` with the booking | `401` missing or unknown token, `422` invalid input |
| `GET /bookings` | List the caller's own bookings only, ordered by start time. Optional `?date=YYYY-MM-DD` keeps only bookings that start on that UTC day | `200` with a list | `401` missing or unknown token, `422` badly formatted date |

Rules for `POST /bookings`:

- `room`: text, 1 to 50 characters.
- `starts_at` and `ends_at`: ISO 8601 timestamps that include a timezone, for example `2026-11-02T09:00:00Z`. They are stored and returned in UTC, to the second. `ends_at` must be after `starts_at`.
- `customer_email`: must look like an email address.
- The owner always comes from the token, never from the request body.

Examples:

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -H "X-User-Token: demo-token-alice" \
  -d '{"room":"A1","starts_at":"2026-11-02T09:00:00Z","ends_at":"2026-11-02T10:00:00Z","customer_email":"guest@example.com"}'

curl http://127.0.0.1:8000/bookings -H "X-User-Token: demo-token-alice"

curl "http://127.0.0.1:8000/bookings?date=2026-11-02" -H "X-User-Token: demo-token-alice"
```

## Tests

```bash
pytest
```

The tests check that both endpoints reject missing or unknown tokens, that bookings are owned by the caller, that invalid input is rejected, that one user can never see another user's bookings, that the customer email is not written to the logs, and that a migration can be applied and undone.

## Database migrations

Migrations are plain SQL files in `migrations/`, named `NNN_name.up.sql` and `NNN_name.down.sql`.

```bash
python -m app.migrate up         # apply all pending migrations
python -m app.migrate down       # undo the most recent migration
python -m app.migrate down 2     # undo the last two
```

## Policies

The `policies/` folder holds three plain-English rules, one per file. The code on `main` meets all three:

1. Every feature that accepts user input has a test proving it checks who is allowed to use it. The 401 tests and the "cannot see another user's bookings" test cover both endpoints.
2. Customer emails are never written to log files. Booking events are logged by numeric ID only (for example `booking created id=7`), and a test checks this.
3. Every database change has a way to undo it. Migration `001` ships with both an up and a down file.

## Dependencies and licences

Every package is open source under an OSI-approved licence. Versions are pinned exactly in `requirements.txt` and `requirements-dev.txt`, and the licences below were read from each installed package's metadata.

Runtime packages (needed to run the app):

| Package | Version | Licence | Why it is here |
|---|---|---|---|
| fastapi | 0.143.3 | MIT | The web framework (routing, validation, docs). Used directly. |
| uvicorn | 0.53.0 | BSD-3-Clause | Runs the app. Used directly. |
| starlette | 1.8.0 | BSD-3-Clause | Web toolkit that FastAPI is built on. |
| pydantic | 2.14.1 | MIT | Request and response validation. |
| pydantic_core | 2.50.1 | MIT | Pydantic's validation engine. |
| annotated-types | 0.8.0 | MIT | Helper used by pydantic. |
| annotated-doc | 0.0.5 | MIT | Typing helper used by FastAPI. |
| typing-inspection | 0.4.4 | MIT | Typing helper used by FastAPI and pydantic. |
| typing_extensions | 4.16.0 | PSF-2.0 | Typing backports used by several packages above. |
| anyio | 4.15.1 | MIT | Async support used by Starlette. |
| idna | 3.20 | BSD-3-Clause | Domain-name helper used by anyio. |
| click | 8.5.0 | BSD-3-Clause | Command-line toolkit used by uvicorn. |
| h11 | 0.16.0 | MIT | HTTP/1.1 protocol library used by uvicorn. |
| opentelemetry-api | 1.45.1 | Apache-2.0 | Pulled in by FastAPI. This app does not use it directly. |

Development and test packages (only needed to run the tests):

| Package | Version | Licence | Why it is here |
|---|---|---|---|
| pytest | 9.1.1 | MIT | Test runner. Used directly. |
| httpx | 0.28.1 | BSD-3-Clause | Required by FastAPI's test client. Used directly. |
| httpcore | 1.0.9 | BSD-3-Clause | HTTP engine used by httpx. |
| certifi | 2026.7.22 | MPL-2.0 | Certificate bundle used by httpx. |
| iniconfig | 2.3.1 | MIT | Config-file reader used by pytest. |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | Version handling used by pytest. |
| pluggy | 1.7.0 | MIT | Plugin system used by pytest. |
| Pygments | 2.21.0 | BSD-2-Clause | Syntax colouring in pytest output. |

## Repository layout

```
app/            the API (main.py), login (auth.py), request shapes (schemas.py),
                database helper (db.py) and migration runner (migrate.py)
config/         the fake demo users
migrations/     SQL migrations, each with an up and a down file
policies/       the three plain-English policies
tests/          pytest tests
.gitlab-ci.yml  pipeline that runs the tests
```

## Licence

MIT. See [LICENSE](LICENSE).
