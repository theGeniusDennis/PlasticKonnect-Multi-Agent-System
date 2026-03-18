# simulation/scenario_2_collector_refuse.py
# Scenario 2: "The Reluctant Collector"
#
# Coordinator assigns task in Engineering Quad to Kwame (already at capacity).
# Kwame refuses → Coordinator reassigns to Abena (available).
# Expected flow:
#   WasteSensorAgent INFORM(zone_alert) →
#   Coordinator REQUEST → Kwame REFUSE(at_capacity) →
#   Coordinator REQUEST → Abena AGREE.

import logging
logging.disable(logging.INFO)
for _lib in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl"):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.mock_api import install, reset, set_zone_counts, add_request, add_collector
install()

import config.settings as settings
settings.MONITOR_INTERVAL = 2

from simulation.xmpp_server import start_xmpp_server, stop_xmpp_server
from config.agent_jids import COORDINATOR_JID, WASTE_SENSOR_JID, collector_jid
from config.settings import AGENT_PASSWORD, SIMULATION_LOG, COLLECTOR_MAX_TASKS
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
    print("SCENARIO 2 — The Reluctant Collector")
    print("="*60)

    reset()

    set_zone_counts({"Engineering Quad": 15})
    for i in range(1, 16):
        add_request(id=i, location_label="Engineering Quad", student=f"student{i}")
    add_collector("kwame")
    add_collector("abena")

    _log("\n[Scenario 2] Kwame starts at FULL capacity (3/3 tasks)")
    _log("[Scenario 2] Expected: Kwame refuses → Abena accepts\n")

    await start_xmpp_server()

    coordinator = CampusCoordinatorAgent(COORDINATOR_JID, AGENT_PASSWORD)
    # Kwame is already at max capacity
    collector_kwame = CollectorAgent(
        collector_jid("kwame"), AGENT_PASSWORD,
        collector_name="kwame"
    )
    collector_kwame.current_tasks = COLLECTOR_MAX_TASKS  # pre-fill to capacity

    collector_abena = CollectorAgent(
        collector_jid("abena"), AGENT_PASSWORD,
        collector_name="abena"
    )

    sensor = WasteSensorAgent(WASTE_SENSOR_JID, AGENT_PASSWORD)

    # Register both collectors — Kwame is shown as full
    coordinator.register_collector(collector_jid("kwame"), "kwame")
    coordinator.collector_registry[collector_jid("kwame")]["current_tasks"] = COLLECTOR_MAX_TASKS
    coordinator.register_collector(collector_jid("abena"), "abena")

    await coordinator.start(auto_register=True)
    await collector_kwame.start(auto_register=True)
    await collector_abena.start(auto_register=True)
    await sensor.start(auto_register=True)

    _log("[Scenario 2] Agents started. Waiting for negotiation to complete...")
    await asyncio.sleep(10)  # interval=2s; allow refusal + reassignment cycle

    await sensor.stop()
    await collector_kwame.stop()
    await collector_abena.stop()
    await coordinator.stop()

    _log("\n[Scenario 2] Complete. Check logs/decisions.log for reassignment trail.")
    await stop_xmpp_server()
    print("\n[Scenario 2] DONE\n")


if __name__ == "__main__":
    asyncio.run(run())
