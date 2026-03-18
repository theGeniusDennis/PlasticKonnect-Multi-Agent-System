# behaviours/monitor_zones.py
# PeriodicBehaviour for WasteSensorAgent.
# Polls PlasticKonnect every MONITOR_INTERVAL seconds and sends zone overflow
# alerts (or resolution notices) to the CampusCoordinatorAgent.

import json
import logging

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from config.settings import (
    ZONE_OVERFLOW_THRESHOLD,
    DECISIONS_LOG,
    AGENT_MESSAGES_LOG,
)
from config.agent_jids import COORDINATOR_JID
import api.client as api

logger = logging.getLogger(__name__)


def _log(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class MonitorZonesBehaviour(PeriodicBehaviour):
    """
    Runs every MONITOR_INTERVAL seconds.
    Polls PlasticKonnect for pending pickup counts per zone.
    Sends an INFORM alert to the Coordinator when a zone overflows.
    Sends a RESOLVE notice when a previously alerted zone clears.

    Expects self.agent to have:
        zone_counts   : dict[str, int]
        alerted_zones : set[str]
    """

    async def run(self):
        zone_counts = api.get_pending_pickups_by_zone()
        agent = self.agent

        for zone, count in zone_counts.items():

            if count >= ZONE_OVERFLOW_THRESHOLD and zone not in agent.alerted_zones:
                # ── New overflow ──────────────────────────────────────────────
                agent.alerted_zones.add(zone)
                agent.zone_counts[zone] = count

                msg = Message(to=COORDINATOR_JID)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "plastickonnect-waste-management")
                msg.body = json.dumps({
                    "type": "zone_alert",
                    "zone": zone,
                    "count": count,
                    "threshold": ZONE_OVERFLOW_THRESHOLD,
                })
                await self.send(msg)

                entry = (
                    f"[WasteSensor → Coordinator] INFORM zone_alert | "
                    f"zone={zone} count={count}"
                )
                logger.info(entry)
                _log(AGENT_MESSAGES_LOG, entry)
                _log(DECISIONS_LOG,
                     f"[WasteSensor] Zone '{zone}' exceeded threshold "
                     f"({count} >= {ZONE_OVERFLOW_THRESHOLD}). Alert sent.")

            elif count < ZONE_OVERFLOW_THRESHOLD and zone in agent.alerted_zones:
                # ── Zone cleared ──────────────────────────────────────────────
                agent.alerted_zones.discard(zone)
                agent.zone_counts[zone] = count

                msg = Message(to=COORDINATOR_JID)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "plastickonnect-waste-management")
                msg.body = json.dumps({
                    "type": "zone_resolved",
                    "zone": zone,
                    "count": count,
                })
                await self.send(msg)

                entry = (
                    f"[WasteSensor → Coordinator] INFORM zone_resolved | "
                    f"zone={zone} count={count}"
                )
                logger.info(entry)
                _log(AGENT_MESSAGES_LOG, entry)

        agent.zone_counts.update(zone_counts)
