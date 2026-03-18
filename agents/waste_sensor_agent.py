# agents/waste_sensor_agent.py
# WasteSensorAgent — monitors campus zones for plastic waste overflow.
#
# Beliefs:  zone_counts (dict), alerted_zones (set)
# Goals:    G1.1 – Detect zone overflow
# Sends:    INFORM(zone_alert) → CampusCoordinatorAgent

import logging

from spade.agent import Agent

from config.settings import MONITOR_INTERVAL, AGENT_PASSWORD
from behaviours.monitor_zones import MonitorZonesBehaviour

logger = logging.getLogger(__name__)


class WasteSensorAgent(Agent):
    """
    Continuously monitors campus zones for plastic waste overflow.

    Beliefs
    -------
    zone_counts  : dict[str, int]  — latest pending pickup count per zone
    alerted_zones: set[str]        — zones currently in alerted state
    """

    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.zone_counts: dict[str, int] = {}
        self.alerted_zones: set[str] = set()

    async def setup(self):
        logger.info(f"[WasteSensor] Agent started: {self.jid}")
        behaviour = MonitorZonesBehaviour(period=MONITOR_INTERVAL)
        self.add_behaviour(behaviour)
