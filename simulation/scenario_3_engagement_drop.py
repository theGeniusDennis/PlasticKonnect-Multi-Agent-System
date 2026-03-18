# simulation/scenario_3_engagement_drop.py
# Scenario 3: "The Quiet Tuesday"
#
# Only 4 students are active today (threshold = 20).
# Expected flow:
#   GamificationAgent detects drop →
#   INFORM(engagement_drop) → CampusCoordinatorAgent →
#   Coordinator logs that bonus event is acknowledged.

import logging
logging.disable(logging.INFO)
for _lib in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl"):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.mock_api import install, reset, add_user
install()

import config.settings as settings
settings.ENGAGEMENT_CHECK_HOURS = 2 / 3600  # ~2 seconds in simulation

from simulation.xmpp_server import start_xmpp_server, stop_xmpp_server
from config.agent_jids import COORDINATOR_JID, GAMIFICATION_JID
from config.settings import AGENT_PASSWORD, SIMULATION_LOG, ENGAGEMENT_THRESHOLD
from agents.gamification_agent import GamificationAgent
from agents.coordinator_agent import CampusCoordinatorAgent


def _log(text: str):
    os.makedirs("logs", exist_ok=True)
    with open(SIMULATION_LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


async def run():
    print("\n" + "="*60)
    print("SCENARIO 3 — The Quiet Tuesday")
    print("="*60)

    reset()

    # Only 4 active users — well below threshold of 20
    for i in range(1, 5):
        add_user(f"student{i}", streak=i, points=i * 10)

    _log(f"\n[Scenario 3] Active users: 4 | Threshold: {ENGAGEMENT_THRESHOLD}")
    _log("[Scenario 3] Expected: GamificationAgent triggers bonus event\n")

    await start_xmpp_server()

    coordinator = CampusCoordinatorAgent(COORDINATOR_JID, AGENT_PASSWORD)
    gamification = GamificationAgent(GAMIFICATION_JID, AGENT_PASSWORD)

    await coordinator.start(auto_register=True)
    await gamification.start(auto_register=True)

    _log("[Scenario 3] Agents started. Waiting for engagement check...")
    await asyncio.sleep(8)  # interval ~2s; allow a couple of checks

    await gamification.stop()
    await coordinator.stop()

    _log("\n[Scenario 3] Complete. Check logs/decisions.log for bonus event entry.")
    await stop_xmpp_server()
    print("\n[Scenario 3] DONE\n")


if __name__ == "__main__":
    asyncio.run(run())
