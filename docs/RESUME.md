# Verified resume bullets

- Built a Dockerized delivery dispatch platform with FastAPI, PostgreSQL, Redis, and React, modeling 5 relational entities and enforcing a 7-state order lifecycle with live WebSocket tracking.
- Verified dispatch, state transitions, input validation, and assignment safety with 22 Pytest cases passing on both SQLite and PostgreSQL, including 4 concurrent requests competing for assignments.
- Benchmarked Haversine and heap-based dispatch against nearest-driver selection at 100, 1,000, and 10,000 drivers over 100 measured trials per size; measured 7.96 ms median priority-selection latency at 10,000 drivers.

These figures describe the implemented MVP and recorded local results. They do not claim production traffic, user adoption, real-world delivery improvements, or end-to-end API latency.
