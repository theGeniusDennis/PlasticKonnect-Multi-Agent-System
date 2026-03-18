# simulation/scenario_4_fraud.py
# Scenario 4: "The Suspicious Scanner"
#
# user99 submits 60 scans within 4 minutes (threshold = 8 in 4 min).
# Expected flow:
#   ClassificationAgent detects impossible scan rate →
#   FAILURE(fraud_alert) → CampusCoordinatorAgent →
#   Coordinator logs fraud and flags account.

import logging
logging.disable(logging.INFO)
for _lib in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl"):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.mock_api import install, reset, add_user, add_activity
install()

import config.settings as settings
settings.MONITOR_INTERVAL = 2  # fire fraud check every 2s in simulation

from simulation.xmpp_server import start_xmpp_server, stop_xmpp_server
from config.agent_jids import COORDINATOR_JID, CLASSIFIER_JID
from config.settings import AGENT_PASSWORD, SIMULATION_LOG, FRAUD_SCAN_THRESHOLD, FRAUD_WINDOW_MINUTES
from agents.classification_agent import ClassificationAgent
from agents.coordinator_agent import CampusCoordinatorAgent
import simulation.mock_api as mock


def _log(text: str):
    os.makedirs("logs", exist_ok=True)
    with open(SIMULATION_LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


async def run():
    print("\n" + "="*60)
    print("SCENARIO 4 — The Suspicious Scanner")
    print("="*60)

    reset()

    # user99 with 60 scans in the last 4 minutes
    add_user("user99", streak=2, points=500)

    now = datetime.utcnow()
    fake_scans = [
        {
            "type": "scan",
            "created_at": (now - timedelta(seconds=i * 4)).isoformat(),
            "points": 5,
            "description": "PET Bottle detected",
        }
        for i in range(60)
    ]
    add_activity("user99", fake_scans)

    _log(f"\n[Scenario 4] user99 has 60 scans in {FRAUD_WINDOW_MINUTES} min")
    _log(f"[Scenario 4] Fraud threshold: {FRAUD_SCAN_THRESHOLD} scans/{FRAUD_WINDOW_MINUTES}min")
    _log("[Scenario 4] Expected: ClassificationAgent flags user99 as fraudulent\n")

    await start_xmpp_server()

    coordinator = CampusCoordinatorAgent(COORDINATOR_JID, AGENT_PASSWORD)
    classifier = ClassificationAgent(CLASSIFIER_JID, AGENT_PASSWORD)

    await coordinator.start(auto_register=True)
    await classifier.start(auto_register=True)

    _log("[Scenario 4] Agents started. Waiting for fraud detection...")
    await asyncio.sleep(8)  # interval=2s; allow a couple of detection cycles

    await classifier.stop()
    await coordinator.stop()

    # Verify fraud flag was set in mock state
    if "user99" in mock._state["flagged_users"]:
        _log("\n[Scenario 4] PASS — user99 successfully flagged for fraud.")
    else:
        _log("\n[Scenario 4] FAIL — user99 was NOT flagged. Check ClassificationAgent logic.")

    await stop_xmpp_server()
    print("\n[Scenario 4] DONE\n")


if __name__ == "__main__":
    asyncio.run(run())
