# Measured dispatch benchmarks

Recorded October 15, 2026. Python 3.12.15; Linux-7.0.14-linuxkit-aarch64-with-glibc2.41. Docker Desktop on Apple Silicon, 8 logical CPUs assigned to the VM, 3.825 GiB VM memory. Results are a single local run under shared host load.

Seed 42; 100 measured trials plus 10 warmups per fleet size, about 85% available drivers. Both algorithms receive the same fleet, pickup, and preparation workload; execution order alternates. Timings use perf_counter_ns. Only the first ranked candidate is selected; database, HTTP, locks, Redis, and full-ranking iteration are excluded.

| Drivers | Algorithm | Median ms | p95 ms | Mean timing score (min) | Mean pickup km |
|---:|---|---:|---:|---:|---:|
| 100 | priority | 0.071 | 0.081 | 7.790 | 2.958 |
| 100 | nearest | 0.059 | 0.063 | 9.630 | 0.820 |
| 1,000 | priority | 0.761 | 1.184 | 7.398 | 2.938 |
| 1,000 | nearest | 0.615 | 0.877 | 9.734 | 0.262 |
| 10,000 | priority | 7.957 | 9.241 | 7.265 | 2.903 |
| 10,000 | nearest | 6.320 | 7.491 | 9.734 | 0.081 |

At 10,000 drivers, priority selection took 7.957 ms median versus 6.320 ms for nearest-driver. Its mean heuristic timing score was 7.265 versus 9.734 minutes (25.4% lower), while selecting drivers 2.903 km away versus 0.081 km. The priority selector directly minimizes this same heuristic, so its better score is expected by construction. This does not establish improved real-world delivery time, efficiency, fairness, or general optimality. The baseline is faster and minimizes pickup distance.

Reproduce from the project root:

```bash
docker compose exec backend python benchmark.py --repetitions 100 --output /tmp/benchmark.json
docker compose cp backend:/tmp/benchmark.json docs/benchmark-rerun.json
```

Raw primary run: [benchmark-docker.json](benchmark-docker.json). Independent earlier macOS Python 3.12.14 run: [benchmark.json](benchmark.json). Timing differs with load and platform; workload quality metrics match because the workload is deterministic. This is a microbenchmark, not an API load test.
