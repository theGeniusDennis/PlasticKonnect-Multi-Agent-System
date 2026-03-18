# agents/coordinator_agent.py
# CampusCoordinatorAgent — central decision-maker.
# Receives alerts from all other agents, assigns/reassigns collector tasks,
# and relays fraud alerts to admin.
#
# Beliefs:  pending_alerts, collector_registry, active_assignments
# Goals:    G1.2, G1.3, G1.4 – Assignment/reassignment; G4.3 – Admin alert
# Receives: INFORM from WasteSensor, ClassificationAgent, GamificationAgent
#           AGREE / REFUSE / INFORM(task_complete) from CollectorAgents
# Sends:    REQUEST(assign_task) → CollectorAgents

import logging

from spade.agent import Agent
from spade.template import Template

from config.settings import AGENT_PASSWORD
from behaviours.coordinate import CoordinateBehaviour

logger = logging.getLogger(__name__)


class CampusCoordinatorAgent(Agent):
    """
    Central coordinator for the PlasticKonnect multi-agent system.

    Beliefs
    -------
    pending_alerts      : set[str]          — zones currently in alert state
    collector_registry  : dict[str, dict]   — JID → {name, current_tasks, max_tasks}
    active_assignments  : dict[int, str]    — request_id → collector_name
    unassigned_queue    : list[dict]        — alerts that couldn't be assigned
    busy_this_round     : set[str]          — collectors that refused in current round
    """

    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.pending_alerts: set[str] = set()
        self.collector_registry: dict[str, dict] = {}
        self.active_assignments: dict[int, str] = {}
        self.unassigned_queue: list[dict] = []
        self.busy_this_round: set[str] = set()

    def register_collector(self, jid: str, name: str,
                           max_tasks: int = 3):
        """Called by main.py after each CollectorAgent is started."""
        self.collector_registry[jid] = {
            "name": name,
            "current_tasks": 0,
            "max_tasks": max_tasks,
        }

    async def setup(self):
        logger.info(f"[Coordinator] Agent started: {self.jid}")

        template = Template()
        template.set_metadata("ontology", "plastickonnect-waste-management")

        behaviour = CoordinateBehaviour()
        self.add_behaviour(behaviour, template)
