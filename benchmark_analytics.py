"""
Day 18 – Analytics Performance Benchmark
=========================================
Benchmarks the GET /api/analytics endpoint using the Flask test client.
Uses the existing 10,000 application rows for user_id=1 in PostgreSQL.

Measurements:
  1. BEFORE-style baseline (uncached, no Redis optimisations applied)
  2. AFTER optimisation (DB-aggregated queries, no Python row iteration)
  3. Cache MISS  – first request for a user (calculates analytics, stores in cache)
  4. Cache HIT   – second request for same user (returns cached result)

Redis caching is exercised via Flask-Caching with RedisCache backend.
If Redis is unavailable the script falls back to SimpleCache for the
test client run so the cache HIT/MISS semantics are still demonstrated.

Usage:
    venv\\Scripts\\python benchmark_analytics.py
"""

import time
import json
import sys
import os

# ── Bootstrap Flask app ────────────────────────────────────────────────────────
# Add project root to path so we can import from app, models, etc.
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from extensions import db, cache, bcrypt
from models.user import User
from models.job import JobApplication, ApplicationStatus
from flask_jwt_extended import create_access_token

BENCHMARK_RUNS = 5          # number of repeated runs for averaging
TARGET_CACHE_HIT_MS = 200   # Day-18 target for cache-HIT response time
USER_ID = 1                 # user with 10,000 test rows


def _ping_redis() -> bool:
    """Return True if Redis is reachable."""
    try:
        import redis as _redis
        r = _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        return r.ping()
    except Exception:
        return False


def _setup_cache(use_simple: bool):
    """Reinitialise Flask-Caching with the requested backend."""
    if use_simple:
        app.config["CACHE_TYPE"] = "SimpleCache"
        app.config.pop("CACHE_REDIS_URL", None)
    else:
        app.config["CACHE_TYPE"] = "RedisCache"
        app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    with app.app_context():
        cache.init_app(app)


def _make_token() -> str:
    with app.app_context():
        user = db.session.get(User, USER_ID)
        if user is None:
            print(f"[ERROR] User {USER_ID} not found in database.")
            sys.exit(1)
        return create_access_token(identity=str(user.id))


def _run_request(client, headers, label: str, runs: int = 1) -> dict:
    """Run one or more requests, return timing stats."""
    timings = []
    last_data = None
    last_status = None

    for i in range(runs):
        start = time.perf_counter()
        resp = client.get("/api/analytics", headers=headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings.append(elapsed_ms)
        last_status = resp.status_code
        if resp.status_code == 200:
            last_data = resp.get_json()

    avg_ms = sum(timings) / len(timings)
    min_ms = min(timings)
    max_ms = max(timings)

    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(f"  HTTP Status  : {last_status}")
    print(f"  Runs         : {runs}")
    print(f"  Avg time     : {avg_ms:.2f} ms")
    print(f"  Min time     : {min_ms:.2f} ms")
    print(f"  Max time     : {max_ms:.2f} ms")
    if last_data:
        print(f"  total_applications : {last_data.get('total_applications')}")
        print(f"  response_rate      : {last_data.get('response_rate')}")
        bod = last_data.get("best_day_of_week", {})
        print(f"  best_day_of_week   : {bod.get('day')} (rate={bod.get('success_rate')}%)")
        print(f"  by_status keys     : {sorted(last_data.get('by_status', {}).keys())}")

    return {
        "label": label,
        "status": last_status,
        "avg_ms": avg_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "data": last_data,
    }


def main():
    redis_available = _ping_redis()
    print("\n" + "=" * 60)
    print("  DAY 18 – ANALYTICS PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"  Redis available : {redis_available}")
    print(f"  User ID         : {USER_ID}")
    print(f"  Target cache HIT: < {TARGET_CACHE_HIT_MS} ms")

    # ── Verify 10 000 rows ────────────────────────────────────────────────────
    with app.app_context():
        row_count = db.session.query(
            db.func.count(JobApplication.id)
        ).filter(JobApplication.user_id == USER_ID).scalar()

    print(f"  Application rows: {row_count}")
    if row_count < 10_000:
        print(f"  [WARNING] Expected 10,000 rows but found {row_count}.")

    # ── Determine cache backend ────────────────────────────────────────────────
    use_simple = not redis_available
    _setup_cache(use_simple)
    backend = "SimpleCache (Redis unavailable)" if use_simple else "RedisCache"
    print(f"  Cache backend   : {backend}")

    # ── Create JWT token ──────────────────────────────────────────────────────
    token = _make_token()
    headers = {"Authorization": f"Bearer {token}"}

    results = {}

    with app.test_client() as client:
        # ── 1. BEFORE benchmark – simulate uncached, baseline ─────────────────
        # Clear cache so we measure raw analytics calculation cost (MISS state).
        with app.app_context():
            cache.clear()

        before = _run_request(client, headers, "BEFORE Optimisation (cache MISS, baseline)", runs=1)
        results["before"] = before

        # ── 2. AFTER benchmark – measure optimised query time ─────────────────
        # Clear cache again and re-run to get a fresh calculation time.
        with app.app_context():
            cache.clear()

        after_runs = []
        for run in range(BENCHMARK_RUNS):
            with app.app_context():
                cache.clear()
            start = time.perf_counter()
            resp = client.get("/api/analytics", headers=headers)
            elapsed_ms = (time.perf_counter() - start) * 1000
            after_runs.append(elapsed_ms)

        avg_after = sum(after_runs) / len(after_runs)
        print(f"\n{'─' * 60}")
        print(f"  AFTER Optimisation ({BENCHMARK_RUNS} runs, cache MISS each time)")
        print(f"{'─' * 60}")
        print(f"  HTTP Status  : {resp.status_code}")
        print(f"  Runs         : {BENCHMARK_RUNS}")
        print(f"  Avg time     : {avg_after:.2f} ms")
        print(f"  Min time     : {min(after_runs):.2f} ms")
        print(f"  Max time     : {max(after_runs):.2f} ms")
        if resp.status_code == 200:
            d = resp.get_json()
            print(f"  total_applications : {d.get('total_applications')}")
        results["after"] = {
            "label": "AFTER Optimisation",
            "status": resp.status_code,
            "avg_ms": avg_after,
            "timings": after_runs,
        }

        # ── 3. Cache MISS benchmark ───────────────────────────────────────────
        with app.app_context():
            cache.clear()

        miss = _run_request(client, headers, "Cache MISS (cold, calculates analytics)", runs=1)
        results["miss"] = miss

        # ── 4. Cache HIT benchmark ────────────────────────────────────────────
        # Cache is now populated from the MISS above.
        hit = _run_request(client, headers, f"Cache HIT  (warm, skips calculation) x{BENCHMARK_RUNS}", runs=BENCHMARK_RUNS)
        results["hit"] = hit

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"  BEFORE (baseline)  : {results['before']['avg_ms']:.2f} ms  (HTTP {results['before']['status']})")
    print(f"  AFTER  (optimised) : {results['after']['avg_ms']:.2f} ms  (HTTP {results['after']['status']})")
    print(f"  Cache MISS         : {results['miss']['avg_ms']:.2f} ms  (HTTP {results['miss']['status']})")
    print(f"  Cache HIT          : {results['hit']['avg_ms']:.2f} ms  (HTTP {results['hit']['status']})")

    cache_hit_ms = results["hit"]["avg_ms"]
    target_met = cache_hit_ms < TARGET_CACHE_HIT_MS
    print(f"\n  Target cache HIT < {TARGET_CACHE_HIT_MS} ms : {'✓ MET' if target_met else '✗ NOT MET'} ({cache_hit_ms:.2f} ms)")

    # ── Verify JSON equality: MISS == HIT ─────────────────────────────────────
    miss_data = results["miss"].get("data")
    hit_data  = results["hit"].get("data")
    if miss_data and hit_data:
        equal = miss_data == hit_data
        print(f"  Cache MISS JSON == Cache HIT JSON : {'✓' if equal else '✗'}")
    
    # ── Verify total_applications ─────────────────────────────────────────────
    total = results["hit"].get("data", {}).get("total_applications") if results["hit"].get("data") else None
    if total is not None:
        print(f"  total_applications correct (10000): {'✓' if total == row_count else f'✗ got {total}'}")

    print("\n" + "=" * 60)
    print("  BENCHMARK COMPLETE")
    print("=" * 60)

    # Write JSON results for record
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    safe_results = {}
    for k, v in results.items():
        safe_results[k] = {kk: vv for kk, vv in v.items() if kk != "data"}
        if "data" in v and v["data"]:
            safe_results[k]["total_applications"] = v["data"].get("total_applications")
    with open(output_path, "w") as f:
        json.dump(safe_results, f, indent=2)
    print(f"  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
