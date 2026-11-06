"""In-memory transfer metering.

Every download and upload is registered as an Active transfer and has its bytes
counted as they stream. A once-per-second sampler turns the running byte totals
into aggregate throughput and keeps a rolling 60-second history. Nothing is
persisted; a restart resets everything.
"""
import threading
import time
from collections import deque
from itertools import count

HISTORY_SECONDS = 60


class _Transfer:
    __slots__ = ("id", "name", "direction", "total", "bytes", "start")

    def __init__(self, tid: int, name: str, direction: str, total: int):
        self.id = tid
        self.name = name
        self.direction = direction  # "down" or "up"
        self.total = total          # expected bytes, 0 if unknown
        self.bytes = 0
        self.start = time.monotonic()


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ids = count(1)
        self._active: dict[int, _Transfer] = {}
        self._total_down = 0
        self._total_up = 0
        self._started = time.time()
        self._history: deque[dict] = deque(maxlen=HISTORY_SECONDS)
        self._last_down = 0
        self._last_up = 0
        self._last_sample = time.monotonic()

    def start_transfer(self, name: str, direction: str, total: int) -> int:
        with self._lock:
            tid = next(self._ids)
            self._active[tid] = _Transfer(tid, name, direction, total)
            return tid

    def add_bytes(self, tid: int, n: int, direction: str) -> None:
        with self._lock:
            t = self._active.get(tid)
            if t is not None:
                t.bytes += n
            if direction == "down":
                self._total_down += n
            else:
                self._total_up += n

    def end_transfer(self, tid: int) -> None:
        with self._lock:
            self._active.pop(tid, None)

    def sample(self) -> None:
        """Record one second of aggregate throughput. Called by the sampler."""
        now = time.monotonic()
        with self._lock:
            dt = max(now - self._last_sample, 1e-6)
            self._history.append({
                "t": time.time(),
                "down": (self._total_down - self._last_down) / dt,
                "up": (self._total_up - self._last_up) / dt,
            })
            self._last_down = self._total_down
            self._last_up = self._total_up
            self._last_sample = now

    def snapshot(self) -> dict:
        with self._lock:
            cur = self._history[-1] if self._history else {"down": 0.0, "up": 0.0}
            active = []
            for t in self._active.values():
                elapsed = max(time.monotonic() - t.start, 1e-6)
                active.append({
                    "id": t.id,
                    "name": t.name,
                    "direction": t.direction,
                    "total": t.total,
                    "bytes": t.bytes,
                    "pct": (t.bytes / t.total * 100) if t.total else None,
                    "speed": t.bytes / elapsed,
                })
            return {
                "down": cur["down"],
                "up": cur["up"],
                "active": active,
                "history": list(self._history),
                "total_down": self._total_down,
                "total_up": self._total_up,
                "uptime": time.time() - self._started,
            }
