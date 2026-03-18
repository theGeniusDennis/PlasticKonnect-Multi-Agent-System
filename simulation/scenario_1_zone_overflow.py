# simulation/scenario_1_zone_overflow.py
# Scenario 1: "The Overflowing Zone"
#
# Science Block accumulates 22 pending pickups (threshold = 10).
# Expected flow:
#   WasteSensorAgent detects overflow →
#   INFORM(zone_alert) → CampusCoordinatorAgent →
#   REQUEST(assign_task) → CollectorAgent_Kwame →
#   AGREE(task_accepted) → Coordinator logs assignment.

import logging
logging.disable(logging.INFO)
for _lib in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl"):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.mock_api import install, reset, set_zone_counts, add_request, add_collector
install()  # must be before any agent imports

import config.settings as settings
settings.MONITOR_INTERVAL = 2   # fire every 2s in simulation (default is 30s)

from simulation.xmpp_server import start_xmpp_server, stop_xmpp_server
from config.agent_jids import COORDINATOR_JID, WASTE_SENSOR_JID, collector_jid
from config.settings import AGENT_PASSWORD, SIMULATION_LOG
from agents.waste_sensor_agent import WasteSensorAgent
from agents.coordinator_agent import CampusCoordinatorAgent
from agents.collector_agent import CollectorAgent


def _log(text: str):
    os.makedirs("logs", exist_ok=True)
    with open(SIMULATION_LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


async def run():
    print("\n" + "="*60)
    print("SCENARIO 1 — The Overflowing Zone")
    print("="*60)

    reset()

    # ── Setup: Science Block has 22 pending pickups ──────────────────────────
    set_zone_counts({"Science Block": 22})
    for i in range(1, 23):
        add_request(id=i, location_label="Science Block", student=f"student{i}")
    add_collector("kwame")
    add_collector("abena")

    _log("\n[Scenario 1] Environment: Science Block = 22 pending pickups")
    _log("[Scenario 1] Threshold: 10 | Expected: Coordinator assigns to Kwame\n")

    # ── Start XMPP server ─────────────────────────────────────────────────────
    await start_xmpp_server()

    # ── Start agents ─────────────────────────────────────────────────────────
    coordinator = CampusCoordinatorAgent(COORDINATOR_JID, AGENT_PASSWORD)
    collector_kwame = CollectorAgent(
        collector_jid("kwame"), AGENT_PASSWORD,
        collector_name="kwame"
    )
    sensor = WasteSensorAgent(WASTE_SENSOR_JID, AGENT_PASSWORD)

    # Register collectors with coordinator before starting
    coordinator.register_collector(collector_jid("kwame"), "kwame")

    await coordinator.start(auto_register=True)
    await collector_kwame.start(auto_register=True)
    await sensor.start(auto_register=True)

    _log("[Scenario 1] All agents started. Waiting for message exchange...")
    await asyncio.sleep(8)  # allow a few monitor cycles (interval = 2s)

    await sensor.stop()
    await collector_kwame.stop()
    await coordinator.stop()

    _log("\n[Scenario 1] Complete. Check logs/agent_messages.log and logs/decisions.log")
    await stop_xmpp_server()
    print("\n[Scenario 1] DONE\n")


if __name__ == "__main__":
    asyncio.run(run())
