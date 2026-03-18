# config/settings.py
# Central configuration for PlasticKonnect multi-agent system

# ── PlasticKonnect API ──────────────────────────────────────────────────────
API_BASE_URL = "https://plastickonnet-production.up.railway.app"
API_TIMEOUT  = 10  # seconds

# ── Zone monitoring ─────────────────────────────────────────────────────────
ZONE_OVERFLOW_THRESHOLD = 10   # pending pickups before alert is sent
MONITOR_INTERVAL        = 30   # seconds between zone polls

# Campus zones (label → used as zone_id when querying the API)
CAMPUS_ZONES = [
    "Science Block",
    "Arts Centre",
    "Volta Hall",
    "Commonwealth Hall",
    "Bush Canteen",
    "Engineering Quad",
    "Great Hall",
    "Balme Library",
]

# ── Collector capacity ───────────────────────────────────────────────────────
COLLECTOR_MAX_TASKS = 3   # refuse if already at this load

# ── Fraud detection ──────────────────────────────────────────────────────────
FRAUD_SCANS_PER_MINUTE  = 2    # max legitimate scans per minute per student
FRAUD_WINDOW_MINUTES    = 4    # observation window
FRAUD_SCAN_THRESHOLD    = FRAUD_SCANS_PER_MINUTE * FRAUD_WINDOW_MINUTES  # = 8

# ── Engagement / gamification ────────────────────────────────────────────────
ENGAGEMENT_THRESHOLD    = 20   # min active students per day before drop event
ENGAGEMENT_CHECK_HOURS  = 1    # how often GamificationAgent checks (hours)
BONUS_EVENT_DURATION_H  = 3    # hours the bonus-points window lasts

STREAK_MILESTONES = [7, 30, 100]  # days
MILESTONE_BONUS_POINTS = {
    7:   10,
    30:  30,
    100: 100,
}

# ── Scan confidence ──────────────────────────────────────────────────────────
MIN_SCAN_CONFIDENCE = 0.6   # scans below this are rejected by ClassificationAgent

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_DIR               = "logs"
AGENT_MESSAGES_LOG    = f"{LOG_DIR}/agent_messages.log"
DECISIONS_LOG         = f"{LOG_DIR}/decisions.log"
SIMULATION_LOG        = f"{LOG_DIR}/simulation_results.log"

# ── XMPP / SPADE ─────────────────────────────────────────────────────────────
XMPP_SERVER  = "localhost"
XMPP_PORT    = 5222
AGENT_PASSWORD = "plastickonnet2024"   # shared password for all agent JIDs (dev only)
