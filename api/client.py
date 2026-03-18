# api/client.py
# All HTTP calls to the PlasticKonnect backend in one place.
# Agents import from here — no raw requests calls anywhere else.

import requests
import logging
from datetime import datetime, timedelta
from config.settings import API_BASE_URL, API_TIMEOUT

logger = logging.getLogger(__name__)


def _get(path: str, params: dict = None) -> dict | list | None:
    """GET request helper. Returns parsed JSON or None on failure."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"GET {path} failed: {e}")
        return None


def _post(path: str, payload: dict = None) -> dict | None:
    """POST request helper. Returns parsed JSON or None on failure."""
    url = f"{API_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload or {}, timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"POST {path} failed: {e}")
        return None


# ── Zone / Pickup endpoints ──────────────────────────────────────────────────

def get_pending_pickups_by_zone() -> dict[str, int]:
    """
    Returns a dict mapping zone_label → count of pending bag requests.
    Uses GET /api/admin/bag-requests?status=pending (admin endpoint).
    Falls back to empty dict on failure.
    """
    data = _get("/api/admin/bag-requests", params={"status": "pending"})
    if not data:
        return {}

    zone_counts: dict[str, int] = {}
    for req in data:
        label = req.get("location_label", "Unknown")
        zone_counts[label] = zone_counts.get(label, 0) + 1
    return zone_counts


def assign_pickup_to_collector(request_id: int, collector_username: str) -> bool:
    """Assign a bag request to a collector. Returns True on success."""
    result = _post(f"/api/collector/pickups/{request_id}/assign",
                   {"collector_username": collector_username})
    return result is not None


def mark_pickup_verified(request_id: int, plastic_count: int) -> dict | None:
    """Mark a pickup as verified with a plastic item count. Returns API response."""
    return _post(f"/api/collector/pickups/{request_id}/verify",
                 {"plastic_count": plastic_count})


def mark_pickup_rejected(request_id: int, reason: str) -> bool:
    """Reject a pickup request. Returns True on success."""
    result = _post(f"/api/collector/pickups/{request_id}/reject",
                   {"reason": reason})
    return result is not None


def get_all_pending_requests() -> list[dict]:
    """Return list of all pending bag requests."""
    data = _get("/api/admin/bag-requests", params={"status": "pending"})
    return data if isinstance(data, list) else []


# ── User / Scan endpoints ────────────────────────────────────────────────────

def get_user(username: str) -> dict | None:
    """Fetch user profile including points, streak, tier."""
    return _get(f"/api/user/{username}")


def get_activity(username: str) -> list[dict]:
    """Fetch scan/redemption activity for a user."""
    data = _get(f"/api/activity/{username}")
    return data if isinstance(data, list) else []


def get_recent_scans(minutes: int = 4) -> list[dict]:
    """
    Return scan submissions from the last `minutes` minutes across all users.
    Uses GET /api/stats — returns global stats; for simulation we mock this.
    """
    # The real API doesn't expose a raw scan feed, so we use global stats
    # and supplement with per-user activity in simulation.
    stats = _get("/api/stats")
    return stats if isinstance(stats, list) else []


def get_all_users() -> list[dict]:
    """Return all users from the leaderboard (all-time, large limit)."""
    data = _get("/api/leaderboard", params={"period": "all", "limit": 500})
    return data if isinstance(data, list) else []


def get_daily_active_users() -> int:
    """
    Count users who have scanned at least once today.
    Approximated from the leaderboard weekly data.
    """
    data = _get("/api/leaderboard", params={"period": "weekly", "limit": 500})
    if not isinstance(data, list):
        return 0
    # Count users who appear in weekly leaderboard (at least 1 scan this week)
    return len(data)


def flag_user_fraud(username: str) -> bool:
    """
    Flag a user account for fraud.
    NOTE: PlasticKonnect doesn't yet have a dedicated fraud endpoint —
    we log locally and the admin sees it via decisions.log.
    Returns True always (local-only action).
    """
    logger.warning(f"FRAUD FLAG: user '{username}' flagged for suspicious scanning.")
    return True


def award_bonus_points(username: str, points: int, reason: str) -> bool:
    """
    Award bonus points to a student by creating a special redemption credit.
    Uses the admin redeem endpoint with a negative cost (credit).
    """
    result = _post("/api/redeem", {
        "username": username,
        "item": reason,
        "cost": -abs(points),   # negative = credit (points added back)
    })
    return result is not None


def get_user_streak(username: str) -> int:
    """Return the current streak in days for a user. 0 if not found."""
    user = get_user(username)
    if user:
        return user.get("streak", 0)
    return 0


# ── Collector endpoints ──────────────────────────────────────────────────────

def get_collectors() -> list[dict]:
    """Return list of all collector accounts."""
    data = _get("/api/admin/collectors")
    return data if isinstance(data, list) else []


def get_collector_pickups(token: str) -> list[dict]:
    """Return pickups visible to a collector (pending + assigned to them)."""
    data = _get("/api/collector/pickups",
                params={"token": token})
    return data if isinstance(data, list) else []


# ── Stats ────────────────────────────────────────────────────────────────────

def get_global_stats() -> dict:
    """Return global platform stats: total_users, total_plastics, co2_saved."""
    return _get("/api/stats") or {}
