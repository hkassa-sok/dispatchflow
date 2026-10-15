"""Reproducible in-process ranking benchmark; excludes HTTP/DB/Redis latency."""
import argparse
import json
import platform
import random
import statistics
import time
from pathlib import Path
from app.dispatch import Candidate, rank, nearest, score, haversine

def run(repetitions):
    rng = random.Random(42)
    rows = []
    for size in [100,1000,10000]:
        drivers = [Candidate(i,40.72+rng.uniform(-.08,.08),-74+rng.uniform(-.08,.08),rng.random()>.15) for i in range(size)]
        lookup = {d.id:d for d in drivers}
        times = {"priority":[],"nearest":[]}
        quality = {"priority":[],"nearest":[]}
        distance = {"priority":[],"nearest":[]}
        for iteration in range(repetitions+10):
            pickup = (40.72+rng.uniform(-.02,.02),-74+rng.uniform(-.02,.02))
            prep = rng.uniform(0,15)
            # Alternate execution order to reduce order effects; first 10 are warmups.
            for name in (["priority","nearest"] if iteration%2 else ["nearest","priority"]):
                start = time.perf_counter_ns()
                result = next(rank(drivers,pickup,prep)) if name == "priority" else nearest(drivers,pickup)
                elapsed = (time.perf_counter_ns()-start)/1e6
                if iteration>=10:
                    times[name].append(elapsed)
                    driver=lookup[result[1]]
                    quality[name].append(score(driver,pickup,prep))
                    distance[name].append(haversine((driver.lat,driver.lng),pickup))
        for name in times:
            rows.append({"drivers":size,"algorithm":name,"median_ms":statistics.median(times[name]),"p95_ms":sorted(times[name])[int(.95*(repetitions-1))],"mean_objective_minutes":statistics.mean(quality[name]),"mean_pickup_distance_km":statistics.mean(distance[name])})
    return {"python":platform.python_version(),"platform":platform.platform(),"seed":42,"repetitions":repetitions,"warmups":10,"scope":"in-process ranking only; objective is the dispatch score, not observed delivery time", "results":rows}
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repetitions",type=int,default=100)
    parser.add_argument("--output",default="../docs/benchmark.json")
    args=parser.parse_args()
    if args.repetitions<2:
        parser.error("repetitions must be >= 2")
    result=run(args.repetitions)
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
