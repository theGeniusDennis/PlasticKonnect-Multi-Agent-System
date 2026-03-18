# simulation/mock_api.py
# Simulated PlasticKonnect API responses for offline testing.
# Import this module to monkey-patch api.client before running scenarios.

import api.client as _real

# ── Shared mutable state (reset between scenarios) ───────────────────────────
_state = {
    "zone_counts": {},       # zone_label → pending count
    "users": [],             # list of user dicts
    "activity": {},          # username → list of activity dicts
    "requests": [],          # list of bag request dicts
    "collectors": [],        # list of collector dicts
    "flagged_users": set(),
    "bonus_events": [],
}


def reset():
    """Reset simulation state to empty."""
    _state["zone_counts"] = {}
    _state["users"] = []
    _state["activity"] = {}
    _state["requests"] = []
    _state["collectors"] = []
    _state["flagged_users"] = set()
    _state["bonus_events"] = []


def set_zone_counts(counts: dict):
    _state["zone_counts"] = dict(counts)


def add_user(username: str, streak: int = 0, points: int = 0):
    _state["users"].append({
        "username": username,
        "streak": streak,
        "points": points,
        "tier": "bronze",
    })


def add_activity(username: str, entries: list):
    _state["activity"][username] = entries


def add_request(id: int, location_label: str, student: str = "student1",
                status: str = "pending"):
    _state["requests"].append({
        "id": id,
        "location_label": location_label,
        "student_username": student,
        "status": status,
    })


def add_collector(username: str):
    _state["collectors"].append({"username": username, "name": username.title()})


# ── Patched API functions ─────────────────────────────────────────────────────

def _get_pending_pickups_by_zone():
    counts = {}
    for r in _state["requests"]:
        if r["status"] == "pending":
            label = r["location_label"]
            counts[label] = counts.get(label, 0) + 1
    return counts


def _get_all_pending_requests():
    return [r for r in _state["requests"] if r["status"] == "pending"]


def _assign_pickup_to_collector(request_id, collector_username):
    for r in _state["requests"]:
        if r["id"] == request_id:
            r["status"] = "assigned"
            r["collector_username"] = collector_username
    return True


def _mark_pickup_verified(request_id, plastic_count):
    for r in _state["requests"]:
        if r["id"] == request_id:
            r["status"] = "verified"
            r["plastic_count"] = plastic_count
    return {"points_awarded": min(plastic_count, 50) * 2}


def _mark_pickup_rejected(request_id, reason):
    for r in _state["requests"]:
        if r["id"] == request_id:
            r["status"] = "rejected"
            r["reject_reason"] = reason
    return True


def _get_all_users():
    return list(_state["users"])


def _get_daily_active_users():
    return len(_state["users"])


def _get_activity(username):
    return _state["activity"].get(username, [])


def _flag_user_fraud(username):
    _state["flagged_users"].add(username)
    return True


def _award_bonus_points(username, points, reason):
    _state["bonus_events"].append({
        "username": username,
        "points": points,
        "reason": reason,
    })
    return True


def _get_user(username):
    for u in _state["users"]:
        if u["username"] == username:
            return u
    return None


def _get_collectors():
    return list(_state["collectors"])


def _get_global_stats():
    return {
        "total_users": len(_state["users"]),
        "total_plastics": 0,
        "co2_saved": 0,
    }


def install():
    """Monkey-patch api.client with mock functions. Call before importing agents."""
    _real.get_pending_pickups_by_zone  = _get_pending_pickups_by_zone
    _real.get_all_pending_requests     = _get_all_pending_requests
    _real.assign_pickup_to_collector   = _assign_pickup_to_collector
    _real.mark_pickup_verified         = _mark_pickup_verified
    _real.mark_pickup_rejected         = _mark_pickup_rejected
    _real.get_all_users                = _get_all_users
    _real.get_daily_active_users       = _get_daily_active_users
    _real.get_activity                 = _get_activity
    _real.flag_user_fraud              = _flag_user_fraud
    _real.award_bonus_points           = _award_bonus_points
    _real.get_user                     = _get_user
    _real.get_collectors               = _get_collectors
    _real.get_global_stats             = _get_global_stats
    print("[MockAPI] Installed — all API calls are now simulated.")
