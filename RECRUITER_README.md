# DispatchFlow — Recruiter Conversation Guide

DispatchFlow is a portfolio MVP inspired by the engineering problems behind last-mile delivery. It connects order management, driver assignment, and live tracking in one application. It is an independent project, not a DoorDash product or a reproduction of DoorDash's internal systems.

## A 30-second introduction

“I built DispatchFlow, a simplified delivery dispatch and tracking platform, to explore the backend problems behind last-mile logistics. It uses FastAPI, PostgreSQL, Redis, and React. Orders follow a validated seven-state lifecycle, and the dispatch service ranks available drivers using geographic distance and pickup readiness. I focused on preventing overlapping assignments under concurrent requests, then added live tracking, automated tests, and reproducible benchmarks.”

## The problem it solves

A merchant needs a driver to collect an order, a driver needs a clear assignment, and a customer needs visibility into delivery progress. These actions can happen simultaneously. The interesting engineering challenge is keeping the system consistent while providing timely updates.

The MVP supports:

- Creating orders and moving them through seven validated states.
- Maintaining driver availability and geographic location.
- Reserving drivers, accepting assignments, and completing deliveries.
- Preventing overlapping active assignments for the same driver or order.
- Broadcasting changes through WebSockets and displaying simulated driver movement.
- Exploring customer, merchant, driver, and dispatch views in a seeded demo.

## How the system works

React and TypeScript provide the dashboard. Nginx forwards requests to FastAPI. SQLAlchemy services write to PostgreSQL inside transactions. Redis Pub/Sub distributes update notifications to WebSocket clients, which refresh their dashboard data.

PostgreSQL stores five related entities: customers, merchants, drivers, orders, and assignments. Alembic manages schema migrations. Docker Compose starts the frontend, backend, PostgreSQL, and Redis together.

## Three engineering decisions to discuss

### 1. Correctness belongs in the database too

Two dispatch requests could otherwise choose the same available driver before either saves its assignment. Dispatch locks the order row and attempts to lock eligible driver rows with PostgreSQL's `FOR UPDATE SKIP LOCKED`. It rechecks availability before reserving the driver.

Partial unique indexes independently enforce at most one active assignment per driver and per order. Creating the assignment and marking the driver unavailable happen in the same transaction. Completion or cancellation releases that reservation atomically.

A useful explanation: “I used application checks for clear behavior and database constraints as a final safeguard against races.”

### 2. Nearest is a baseline, not the only objective

The baseline selects the closest available driver using Haversine distance. The priority algorithm also considers the mismatch between estimated driver arrival and preparation time:

```
travel_minutes = distance_km / 0.4
score = max(travel_minutes, prep_minutes)
        + 0.35 * abs(travel_minutes - prep_minutes)
```

The speed assumption is 24 km/h. Lower scores rank first in a priority queue; driver IDs break ties deterministically.

Heap construction takes O(n) time and O(n) space. Trying k candidates adds O(k log n). Nearest-driver selection takes O(n) time and O(1) extra space.

The tradeoff matters: this heuristic can select a farther driver to align arrival with pickup readiness. It is greedy and does not optimize the whole fleet.

### 3. Live notifications are not durable state

PostgreSQL is authoritative. Redis carries ephemeral notifications; it does not own assignment locks. Clients reconnect and periodically refresh snapshots to recover current state after missed events.

A process can fail after committing but before publishing. A transactional outbox would be a sensible next step if every event needed guaranteed delivery and replay.

## What was actually verified

- 22 Pytest cases passed against SQLite and PostgreSQL.
- Tests cover input validation, state transitions, unavailable drivers, duplicate assignments, and concurrent dispatch requests.
- Four concurrent requests were exercised in assignment tests.
- TypeScript checks and frontend production builds passed.
- PostgreSQL migration upgrade, downgrade, and upgrade passed in a dedicated test database.
- All four Docker Compose services started successfully.
- Browser checks exercised assignment, acceptance, pickup, simulated movement, completion, released availability, and mobile order creation.

GitHub Actions is configured; it has not been verified through a remote GitHub run.

## Benchmark results to describe accurately

Actual seeded workloads used 100, 1,000, and 10,000 drivers, with 100 measured trials and 10 warmups per size. At 10,000 drivers in the recorded Linux container run:

| Measurement | Priority algorithm | Nearest-driver baseline |
|---|---:|---:|
| Median selection latency | 7.96 ms | 6.32 ms |
| Mean heuristic timing score | 7.265 min | 9.734 min |
| Mean pickup distance | 2.903 km | 0.081 km |

The priority algorithm ran slower and selected farther-away drivers. It achieved a lower score on the objective it was designed to minimize. These are in-process algorithm measurements, not end-to-end API latency or evidence of faster real-world deliveries.

A useful explanation: “Benchmarking exposed a tradeoff rather than a universal improvement. I kept the baseline and reported latency, timing score, and pickup distance so the comparison would be honest.”

See [the benchmark methodology and report](docs/BENCHMARKS.md).

## A short demo sequence

1. Open the dashboard and explain the order, driver, and dispatch views.
2. Create an order and use Merchant controls to advance preparation.
3. Dispatch it and show the reserved driver becoming unavailable.
4. Use Driver controls to accept and pick up the order.
5. Start route simulation and show the live map.
6. Complete the delivery and show the driver becoming available again.
7. Point to the concurrency tests and measured benchmark report.

## Limits and sensible next steps

This is a production-style local MVP, not a production delivery service. Role selection changes demo controls; there is no authentication or ownership enforcement. Movement follows straight-line interpolation rather than road routing. Speed and preparation estimates are simplified. There are no payments, traffic predictions, assignment timeouts, or global fleet optimization.

Priorities for further work:

1. Authentication, authorization, and driver ownership checks before public deployment.
2. Assignment rejection, expiration, and reassignment.
3. A transactional outbox for durable event delivery.
4. Spatial filtering, pagination, and measured end-to-end load testing.

## How to discuss authorship

This project was implemented with AI assistance. Describe the parts you have reviewed, can explain, and can modify confidently. Avoid claiming independent implementation of code you have not yet understood. Use our follow-up conversation to walk through the request flow, locking, state machine, tests, and benchmark methodology until you can defend each decision in your own words.

## Questions to prepare for

- Why did you choose PostgreSQL transactions instead of Redis locks?
- What happens if two orders try to reserve the same driver?
- Why can the ranking algorithm choose a farther-away driver?
- What exactly did your benchmark measure?
- What happens when a WebSocket notification is lost?
- What would you change before supporting real customers?

## Run the project

From the project directory:

```bash
docker compose up --build -d
```

Dashboard: http://localhost:8080

API documentation: http://localhost:8000/docs

For detailed setup, architecture diagrams, API examples, and test commands, see [README.md](README.md). For limitations, see [engineering notes](docs/ENGINEERING.md).
