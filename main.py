# main.py
# Entry point — starts all PlasticKonnect agents against the live Railway API.
#
# Usage:
#   source venv/Scripts/activate        (Windows)
#   python main.py
#
# Requires a running XMPP server (Prosody or ejabberd) on localhost:5222
# with JIDs pre-registered, OR use simulation/ scripts for offline demo.

import asyncio
import logging
import os
import signal
import sys

# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/agent_messages.log"),
    ],
)
logger = logging.getLogger("main")

# ── Agent imports ─────────────────────────────────────────────────────────────
from config.settings import AGENT_PASSWORD
from config.agent_jids import (
    COORDINATOR_JID,
    WASTE_SENSOR_JID,
    CLASSIFIER_JID,
    GAMIFICATION_JID,
    COLLECTOR_JIDS,
)
from agents.coordinator_agent import CampusCoordinatorAgent
from agents.waste_sensor_agent import WasteSensorAgent
from agents.classification_agent import ClassificationAgent
from agents.gamification_agent import GamificationAgent
from agents.collector_agent import CollectorAgent
import api.client as api


async def main():
    logger.info("Starting PlasticKonnect Multi-Agent System...")

    # ── 1. Fetch collector accounts from live API ─────────────────────────────
    collectors_data = api.get_collectors()
    if not collectors_data:
        logger.warning(
            "No collector accounts found in API. "
            "Falling back to pre-defined collector JIDs."
        )
        collectors_data = [
            {"username": "kwame"},
            {"username": "abena"},
        ]

    # ── 2. Start CampusCoordinatorAgent ──────────────────────────────────────
    coordinator = CampusCoordinatorAgent(COORDINATOR_JID, AGENT_PASSWORD)
    await coordinator.start(auto_register=True)
    logger.info(f"Coordinator started: {COORDINATOR_JID}")

    # ── 3. Start CollectorAgents (one per collector) ─────────────────────────
    collector_agents = []
    for c in collectors_data:
        name = c["username"]
        jid = COLLECTOR_JIDS.get(name, f"collector_{name}@localhost")
        agent = CollectorAgent(jid, AGENT_PASSWORD, collector_name=name)
        await agent.start(auto_register=True)
        coordinator.register_collector(jid, name)
        collector_agents.append(agent)
        logger.info(f"CollectorAgent started: {jid}")

    # ── 4. Start sensing and reasoning agents ────────────────────────────────
    sensor = WasteSensorAgent(WASTE_SENSOR_JID, AGENT_PASSWORD)
    await sensor.start(auto_register=True)
    logger.info(f"WasteSensorAgent started: {WASTE_SENSOR_JID}")

    classifier = ClassificationAgent(CLASSIFIER_JID, AGENT_PASSWORD)
    await classifier.start(auto_register=True)
    logger.info(f"ClassificationAgent started: {CLASSIFIER_JID}")

    gamification = GamificationAgent(GAMIFICATION_JID, AGENT_PASSWORD)
    await gamification.start(auto_register=True)
    logger.info(f"GamificationAgent started: {GAMIFICATION_JID}")

    logger.info("All agents running. Press Ctrl+C to stop.")

    # ── 5. Run until interrupted ──────────────────────────────────────────────
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received. Stopping agents...")

    # ── 6. Graceful shutdown ──────────────────────────────────────────────────
    await gamification.stop()
    await classifier.stop()
    await sensor.stop()
    for agent in collector_agents:
        await agent.stop()
    await coordinator.stop()

    logger.info("All agents stopped. Goodbye.")


if __name__ == "__main__":
    asyncio.run(main())
