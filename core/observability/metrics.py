"""
Lightweight telemetry for Email Triage Agent.
Mirrors the RAG monitoring module for consistency across services.
"""

import time
import threading
from datetime import datetime
from functools import wraps


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
            "emails_processed": 0,
            "emails_approved": 0,
            "emails_rejected": 0,
            "pii_redactions": 0,
        }
        self._per_model: dict[str, dict] = {}
        self._per_project: dict[str, dict] = {}
        self._latencies: list[float] = []
        self._per_endpoint: dict[str, dict] = {}
        self._pii_by_type: dict[str, int] = {}

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

    def record_tokens(self, prompt_tokens: int, completion_tokens: int, model: str = "unknown", project: str = "unknown"):
        with self._lock:
            self._counters["tokens_prompt"] += prompt_tokens
            self._counters["tokens_completion"] += completion_tokens
            self._counters["tokens_total"] += prompt_tokens + completion_tokens
            self._counters["llm_calls"] += 1

            # Per-model tracking
            if model not in self._per_model:
                self._per_model[model] = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
            self._per_model[model]["prompt"] += prompt_tokens
            self._per_model[model]["completion"] += completion_tokens
            self._per_model[model]["total"] += prompt_tokens + completion_tokens
            self._per_model[model]["calls"] += 1

            # Per-project tracking
            if project not in self._per_project:
                self._per_project[project] = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
            self._per_project[project]["prompt"] += prompt_tokens
            self._per_project[project]["completion"] += completion_tokens
            self._per_project[project]["total"] += prompt_tokens + completion_tokens
            self._per_project[project]["calls"] += 1

    def record_pii(self, pii_types: list[str]):
        with self._lock:
            self._counters["pii_redactions"] += len(pii_types)
            for t in pii_types:
                self._pii_by_type[t] = self._pii_by_type.get(t, 0) + 1

    def snapshot(self) -> dict:
        with self._lock:
            sorted_latencies = sorted(self._latencies)
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
            avg_latency = sum(sorted_latencies) / len(sorted_latencies) if sorted_latencies else 0

            # Dynamic cost calculation based on model
            total_cost_usd = 0.0
            for model, usage in self._per_model.items():
                # Rough estimates for common models
                if "gpt-4o" in model:
                    rate_p, rate_c = 0.15, 0.60 # $ per 1M
                elif "llama-3" in model or "groq" in model:
                    rate_p, rate_c = 0.05, 0.08 # $ per 1M
                else:
                    rate_p, rate_c = 0.10, 0.20 # Default

                total_cost_usd += (usage["prompt"] * rate_p / 1_000_000)
                total_cost_usd += (usage["completion"] * rate_c / 1_000_000)

            return {
                "started_at": self._started_at,
                "uptime_snapshot": datetime.utcnow().isoformat() + "Z",
                "counters": dict(self._counters),
                "per_model": dict(self._per_model),
                "per_project": dict(self._per_project),
                "latency": {
                    "avg_ms": round(avg_latency * 1000, 1),
                    "p95_ms": round(p95 * 1000, 1),
                    "samples": len(sorted_latencies),
                },
                "cost_estimate_usd": round(total_cost_usd, 6),
                "pii_breakdown": dict(self._pii_by_type),
                "endpoints": dict(self._per_endpoint),
            }


metrics = MetricsCollector()


def track_endpoint(endpoint_name: str):
    """Decorator to track request count, latency, and errors for an endpoint."""
    def decorator(fn):
        import asyncio
        import inspect

        if inspect.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                metrics.inc("requests_total")
                start = time.time()
                try:
                    result = await fn(*args, **kwargs)
                    return result
                except Exception:
                    metrics.record_error(endpoint_name)
                    raise
                finally:
                    metrics.record_latency(endpoint_name, time.time() - start)
            return async_wrapper
        else:
            @wraps(fn)
            def wrapper(*args, **kwargs):
                metrics.inc("requests_total")
                start = time.time()
                try:
                    result = fn(*args, **kwargs)
                    return result
                except Exception:
                    metrics.record_error(endpoint_name)
                    raise
                finally:
                    metrics.record_latency(endpoint_name, time.time() - start)
            return wrapper
    return decorator

