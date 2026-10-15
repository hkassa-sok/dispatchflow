"""Pure ranking functions. Scores are estimated minutes, assuming 24 km/h."""
from dataclasses import dataclass
from math import radians, sin, cos, atan2, sqrt
import heapq

@dataclass(frozen=True)
class Candidate:
    id: int
    lat: float
    lng: float
    available: bool = True

def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    h = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 6371 * 2 * atan2(sqrt(min(1, h)), sqrt(max(0, 1-h)))

def score(driver, pickup, prep):
    travel = haversine((driver.lat, driver.lng), pickup) / 0.4
    return max(travel, prep) + 0.35 * abs(travel - prep)

def rank(drivers, pickup, prep):
    heap = [(score(d, pickup, prep), d.id) for d in drivers if d.available]
    heapq.heapify(heap)
    while heap:
        yield heapq.heappop(heap)

def nearest(drivers, pickup):
    return min(((haversine((d.lat,d.lng),pickup),d.id) for d in drivers if d.available), default=None)
