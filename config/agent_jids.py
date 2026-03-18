# config/agent_jids.py
# XMPP JID (Jabber ID) definitions for every agent in the system
# Format: username@xmpp_server

from config.settings import XMPP_SERVER

# Core agents
COORDINATOR_JID    = f"coordinator@{XMPP_SERVER}"
WASTE_SENSOR_JID   = f"waste_sensor@{XMPP_SERVER}"
CLASSIFIER_JID     = f"classifier@{XMPP_SERVER}"
GAMIFICATION_JID   = f"gamification@{XMPP_SERVER}"

# Collector agents — one JID per collector
# In production these are created dynamically from the collectors list in the API.
# For simulation, two collectors are pre-defined.
COLLECTOR_JIDS = {
    "kwame":  f"collector_kwame@{XMPP_SERVER}",
    "abena":  f"collector_abena@{XMPP_SERVER}",
    "kofi":   f"collector_kofi@{XMPP_SERVER}",
}

def collector_jid(name: str) -> str:
    """Return JID for a named collector, creating an ad-hoc one if not pre-defined."""
    return COLLECTOR_JIDS.get(name, f"collector_{name.lower()}@{XMPP_SERVER}")
