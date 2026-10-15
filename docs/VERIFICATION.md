# Verification record

Verified locally on October 15, 2026:

- Python 3.12.14 host: 22 Pytest cases passed.
- Python 3.12.15 Docker container, SQLite: 22 passed.
- Python 3.12.15 Docker container, PostgreSQL 16: 22 passed; includes duplicate order dispatch and four concurrent requests competing for two drivers. Partial unique indexes prevented overlapping active assignments.
- PostgreSQL Alembic upgrade → downgrade → upgrade completed successfully in a dedicated `dispatch_test` database.
- Frontend TypeScript check and Vite production build passed locally and inside Docker.
- All four Compose services started. PostgreSQL, Redis, and backend health checks passed; Nginx served the dashboard.
- Browser verified Redis-backed WebSocket live connection, dispatch assignment, driver acceptance, pickup, route simulation, completion, and released availability. Browser also created a new order through the mobile form.
- Dashboard inspected at 1440px desktop and 390px mobile widths. Screenshots: `dashboard.png` and `mobile.png`.
- Actual seeded benchmarks ran for 100, 1,000, and 10,000 drivers on both macOS and Linux containers; raw reports are included.

Pytest emitted one upstream Starlette/AnyIO deprecation warning. It did not fail tests. The first container `pytest` command exposed a Python import-path configuration issue; `pytest.ini` fixes it, and the final direct `pytest` invocation passed. A benchmark attempt overlapped a container rebuild and could not copy its output; the completed rerun produced the included report.

GitHub Actions is configured but has not run remotely. No public deployment, authenticated multi-user behavior, extended soak test, traffic-aware routing, end-to-end throughput benchmark, or formal security audit is claimed. Browser simulation uses straight-line interpolation. Role controls are demo views, not authorization.
