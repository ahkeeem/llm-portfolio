"""
Lightweight telemetry for RAG backend.

Tracks request count, latency, token usage, and error counts
via in-memory counters. Exposes a /metrics endpoint for observability.
No external dependencies (Prometheus/Grafana optional, can scrape the JSON).
"""

import time
import threading
from datetime import datetime
from functools import wraps
from typing import Any


class MetricsCollector:
    """Thread-safe, in-memory metrics store."""

    def __init__(self):
        self._lock = threading.Lock()
        self._started_at = datetime.utcnow().isoformat() + "Z"
        self._counters = {
            "requests_total": 0,
            "errors_total": 0,
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "tokens_total": 0,
            "llm_calls": 0,
            "cache_hits": 0,
            "pii_redactions": 0,
            "flags_submitted": 0,
            "evaluations_run": 0,
        }
        self._latencies: list[float] = []
        self._per_endpoint: dict[str, dict] = {}

    def inc(self, key: str, amount: int = 1):
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + amount

    def record_latency(self, endpoint: str, duration_s: float):
        with self._lock:
            self._latencies.append(duration_s)
            if endpoint not in self._per_endpoint:
                self._per_endpoint[endpoint] = {"count": 0, "total_latency_s": 0.0, "errors": 0}
            self._per_endpoint[endpoint]["count"] += 1
            self._per_endpoint[endpoint]["total_latency_s"] += duration_s

    def record_error(self, endpoint: str):
        with self._lock:
            self._counters["errors_total"] += 1
            if endpoint not in self._per_endpoint:
                self._per_endpoint[endpoint] = {"count": 0, "total_latency_s": 0.0, "errors": 0}
            self._per_endpoint[endpoint]["errors"] += 1

    def record_tokens(self, prompt_tokens: int, completion_tokens: int):
        with self._lock:
            self._counters["tokens_prompt"] += prompt_tokens
            self._counters["tokens_completion"] += completion_tokens
            self._counters["tokens_total"] += prompt_tokens + completion_tokens
            self._counters["llm_calls"] += 1

    def snapshot(self) -> dict:
        with self._lock:
            sorted_latencies = sorted(self._latencies)
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
            avg_latency = sum(sorted_latencies) / len(sorted_latencies) if sorted_latencies else 0

            # Cost estimate: Groq Llama 3.1 8B ≈ $0.05 / 1M prompt + $0.08 / 1M completion
            cost_usd = (
                self._counters["tokens_prompt"] * 0.05 / 1_000_000
                + self._counters["tokens_completion"] * 0.08 / 1_000_000
            )

            return {
                "started_at": self._started_at,
                "uptime_snapshot": datetime.utcnow().isoformat() + "Z",
                "counters": dict(self._counters),
                "latency": {
                    "avg_ms": round(avg_latency * 1000, 1),
                    "p95_ms": round(p95 * 1000, 1),
                    "samples": len(sorted_latencies),
                },
                "cost_estimate_usd": round(cost_usd, 6),
                "endpoints": dict(self._per_endpoint),
            }


# Global singleton
metrics = MetricsCollector()


def track_endpoint(endpoint_name: str):
    """Decorator to track request count, latency, and errors for an endpoint."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            metrics.inc("requests_total")
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                return result
            except Exception as exc:
                metrics.record_error(endpoint_name)
                raise
            finally:
                metrics.record_latency(endpoint_name, time.time() - start)
        return wrapper
    return decorator
