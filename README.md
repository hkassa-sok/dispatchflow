# DispatchFlow

**Real-time delivery dispatch & tracking.** A full-stack software engineering portfolio MVP built with Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, Redis, React, TypeScript, Tailwind, WebSockets, Pytest, and Docker Compose.

![DispatchFlow dashboard](docs/dashboard.png)

## Run locally

Install Docker Desktop and start its engine, then from this directory:

```bash
docker compose up --build -d
```

- Dashboard: http://localhost:8080
- Interactive API: http://localhost:8000/docs
- Database and Redis stay on the internal Compose network.
- Sample data seeds automatically on the first boot: 1 customer, 2 merchants, 6 drivers, and 4 orders.
- Stop with `docker compose down`. PostgreSQL data persists in a named volume. `docker compose down -v` deletes this project's database.

The default database password is for local demo use. Set `POSTGRES_PASSWORD` in an ignored `.env` file to override it. Services expose local demo APIs without authentication; do not expose them to the public internet.

## Try a complete delivery

1. Create an order using the dashboard.
2. Select **Merchant** and move the order through Accepted → Preparing → Ready for pickup.
3. Select **Dispatch** and choose **Find best driver** or **Dispatch**.
4. Select **Driver**, accept the assignment, and pick up the ready order.
5. Enable **Simulate routes** to move accepted drivers toward the merchant or delivery destination. Pause when finished.
6. In Driver view, complete the delivery. The driver becomes available again.
7. Customer view displays progress and cancellation controls. Drivers view toggles availability for unassigned drivers.

Role selection changes demo controls. It is not authentication or access control. All views use the same persisted workspace.

## Architecture

```mermaid
flowchart LR
    UI[React + TypeScript + Tailwind] --> NGINX[Nginx reverse proxy]
    NGINX --> API[FastAPI routes]
    API --> SERVICES[Order / assignment services]
    SERVICES --> RANK[Haversine + priority queue]
    SERVICES --> DB[(PostgreSQL)]
    API --> EVENTS[Event publisher]
    EVENTS --> REDIS[(Redis Pub/Sub)]
    REDIS --> WS[WebSocket clients]
    WS --> UI
```

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    MERCHANTS ||--o{ ORDERS : prepares
    ORDERS ||--o{ ASSIGNMENTS : receives
    DRIVERS ||--o{ ASSIGNMENTS : handles
```

- `backend/app/api.py`: REST and WebSocket routes, validated request schemas.
- `backend/app/services.py`: transactional state changes, row locking, assignment invariants.
- `backend/app/dispatch.py`: deterministic pure ranking and baseline algorithms.
- `backend/app/models.py`: 5 relational entities, foreign keys, indexes, check constraints, and partial unique indexes.
- `backend/app/events.py`: Redis fanout; bounded per-client queues prevent unbounded memory growth.
- `backend/alembic`: versioned, frozen initial migration with upgrade and downgrade.
- `frontend/src`: responsive operations dashboard with map, queue, order creation, role controls, and route simulation.

An assignment is reserved when dispatch succeeds; driver acceptance is a separate action. Availability is changed in the same database transaction as the assignment. PostgreSQL locks the order row, then locks candidate drivers with `FOR UPDATE SKIP LOCKED`, rechecking availability after acquiring the lock. Partial unique indexes enforce at most one active assignment per driver and order even if an application bug bypasses those checks. A race or unavailable fleet returns HTTP 409; callers can refresh and retry. Completion/cancellation releases the reservation atomically.

SQLite is supported for lightweight tests/local development, but does not provide PostgreSQL row locking. Its unique indexes still prevent duplicate active assignments, and lock conflicts become 409 responses. PostgreSQL tests are the authority for production locking behavior.

## Order state machine

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> ACCEPTED
    ACCEPTED --> PREPARING
    PREPARING --> READY_FOR_PICKUP
    READY_FOR_PICKUP --> PICKED_UP
    PICKED_UP --> DELIVERED
    CREATED --> CANCELLED
    ACCEPTED --> CANCELLED
    PREPARING --> CANCELLED
    READY_FOR_PICKUP --> CANCELLED
```

Pickup and delivery require an active, accepted assignment. Delivered and cancelled orders are terminal. No cancellation is permitted after pickup.

## API examples

```bash
curl -X POST http://localhost:8000/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"merchant_id":1,"lat":40.741,"lng":-73.982,"prep_minutes":8}'

# Replace 5 with the ID returned above.
curl -X PATCH http://localhost:8000/api/orders/5/status \
  -H 'Content-Type: application/json' -d '{"status":"ACCEPTED"}'
curl -X POST http://localhost:8000/api/orders/5/dispatch
curl http://localhost:8000/api/dashboard
```

Other endpoints: `GET /api/orders`, `GET /api/orders/{id}`, `POST /api/drivers`, `PATCH /api/drivers/{id}`, `POST /api/assignments/{id}/accept`, and `POST /api/demo/step`. `/docs` is the full executable API reference. WebSocket `/ws` emits event type and affected ID; clients fetch a fresh dashboard snapshot. Heartbeats, reconnects, and 15-second polling repair missed notifications.

Validation failures return 422, missing resources 404, invalid transitions or assignment conflicts 409. Requests include an `X-Request-ID` response header and JSON logs with request duration.

## Dispatch algorithm

For each available driver, compute straight-line distance with Haversine and estimate travel time at a fixed 24 km/h:

```
travel_minutes = distance_km / 0.4
score = max(travel_minutes, prep_minutes) + 0.35 × abs(travel_minutes - prep_minutes)
```

Lower is better. The score balances when pickup can happen against mismatched arrival/preparation times. Heapify `(score, driver_id)` tuples, then pop candidates until a driver can be reserved. IDs deterministically break ties. Unavailable drivers are ineligible. The baseline chooses the minimum Haversine distance with a linear scan.

For n available drivers and k attempted reservations: ranking/heap creation is **O(n)** time and **O(n)** space; k heap pops add **O(k log n)** time. Selecting the first candidate is O(n); consuming the entire ranking is O(n log n). Baseline selection is **O(n)** time and **O(1)** extra space. Database round trips and lock contention add costs beyond these in-process bounds.

See [the measured benchmark report](docs/BENCHMARKS.md) and [raw results](docs/benchmark.json). The timing objective is a heuristic; its improvement is not evidence of faster real deliveries or better fleet-wide efficiency.

## Tests and benchmarks

Run in an isolated container (SQLite tests):

```bash
docker compose exec backend pytest -q
```

PostgreSQL integration tests drop/recreate all tables in the test database. **Always use a dedicated test database**:

```bash
docker compose exec postgres createdb -U dispatch dispatch_test
docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://dispatch:dispatch_local@postgres:5432/dispatch_test backend pytest -q
```

If you changed the local password, substitute it in the test URL. Run the reproducible benchmark and copy its report out:

```bash
docker compose exec backend python benchmark.py --repetitions 100 --output /tmp/benchmark.json
docker compose cp backend:/tmp/benchmark.json docs/benchmark-rerun.json
```

Without Docker, create a Python 3.12 virtual environment, install `backend/requirements.txt`, and run `python -m pytest -q` from `backend`. For a SQLite demo run `alembic upgrade head` then `uvicorn app.main:app --port 8000`. From `frontend`, install Node 22 and pnpm 11.25.0, run `pnpm install --frozen-lockfile`, then `pnpm dev`. Vite proxies API/WebSocket calls to port 8000. Without `REDIS_URL`, this single-process mode uses an in-memory event bus.

GitHub Actions runs SQLite and PostgreSQL tests, migrations, and the TypeScript/production build. The workflow has not been executed on GitHub until this project is pushed.

See [verification record](docs/VERIFICATION.md), [tradeoffs and future work](docs/ENGINEERING.md), and [resume bullets](docs/RESUME.md).
