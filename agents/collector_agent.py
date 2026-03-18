# agents/collector_agent.py
# CollectorAgent — one instance per physical collector.
# Receives task assignments from CampusCoordinatorAgent, decides to accept
# or refuse based on current capacity, and confirms completion.
#
# Beliefs:  collector_id, current_tasks, max_tasks
# Goals:    G1.2 – Execute collection task
# Receives: REQUEST(assign_task) from CampusCoordinatorAgent
# Sends:    AGREE / REFUSE / INFORM(task_complete) → CampusCoordinatorAgent

import logging

from spade.agent import Agent
from spade.template import Template

from config.settings import COLLECTOR_MAX_TASKS, AGENT_PASSWORD
from behaviours.handle_task import HandleTaskBehaviour

logger = logging.getLogger(__name__)


class CollectorAgent(Agent):
    """
    Represents one physical collector on campus.

    Parameters
    ----------
    collector_name : str  — username matching the PlasticKonnect collectors table
    max_tasks      : int  — override default capacity (default = COLLECTOR_MAX_TASKS)

    Beliefs
    -------
    current_tasks  : int       — number of active tasks
    active_task_ids: list[int] — request IDs currently assigned
    """

    def __init__(self, jid: str, password: str,
                 collector_name: str, max_tasks: int = COLLECTOR_MAX_TASKS):
        super().__init__(jid, password)
        self.collector_name = collector_name
        self.max_tasks = max_tasks
        self.current_tasks: int = 0
        self.active_task_ids: list[int] = []

    async def setup(self):
        logger.info(f"[Collector:{self.collector_name}] Agent started: {self.jid}")

        # Only listen to messages intended for this collector
        template = Template()
        template.set_metadata("ontology", "plastickonnect-waste-management")

        behaviour = HandleTaskBehaviour()
        self.add_behaviour(behaviour, template)
