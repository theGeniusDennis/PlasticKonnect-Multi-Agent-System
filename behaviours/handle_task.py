# behaviours/handle_task.py
# CyclicBehaviour for CollectorAgent.
# Listens for REQUEST(assign_task) messages from the CampusCoordinatorAgent
# and replies with AGREE or REFUSE based on current task load.

import json
import logging

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from config.settings import (
    DECISIONS_LOG,
    AGENT_MESSAGES_LOG,
)
from config.agent_jids import COORDINATOR_JID
import api.client as api

logger = logging.getLogger(__name__)


def _log(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class HandleTaskBehaviour(CyclicBehaviour):
    """
    Listens for REQUEST(assign_task) messages from the Coordinator.
    Accepts if under capacity, refuses otherwise.
    On acceptance, calls the API to confirm assignment.

    Expects self.agent to have:
        collector_name  : str
        max_tasks       : int
        current_tasks   : int
        active_task_ids : list[int]
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        try:
            payload = json.loads(msg.body)
        except (json.JSONDecodeError, AttributeError):
            return

        msg_type = payload.get("type")
        agent = self.agent

        if msg_type == "assign_task":
            request_id = payload.get("request_id")
            zone = payload.get("zone", "Unknown")

            if agent.current_tasks < agent.max_tasks:
                await self._accept(request_id, zone)
            else:
                await self._refuse(request_id, zone)

        elif msg_type == "task_complete":
            request_id = payload.get("request_id")
            if request_id in agent.active_task_ids:
                agent.active_task_ids.remove(request_id)
                agent.current_tasks = max(0, agent.current_tasks - 1)
                logger.info(
                    f"[{agent.collector_name}] Task {request_id} completed. "
                    f"Remaining: {agent.current_tasks}/{agent.max_tasks}"
                )

    async def _accept(self, request_id: int, zone: str):
        agent = self.agent
        agent.current_tasks += 1
        agent.active_task_ids.append(request_id)

        reply = Message(to=COORDINATOR_JID)
        reply.set_metadata("performative", "agree")
        reply.set_metadata("ontology", "plastickonnect-waste-management")
        reply.body = json.dumps({
            "type": "task_accepted",
            "request_id": request_id,
            "collector": agent.collector_name,
        })
        await self.send(reply)

        api.assign_pickup_to_collector(request_id, agent.collector_name)

        entry = (
            f"[{agent.collector_name} → Coordinator] AGREE task_accepted | "
            f"request_id={request_id} zone={zone} "
            f"load={agent.current_tasks}/{agent.max_tasks}"
        )
        logger.info(entry)
        _log(AGENT_MESSAGES_LOG, entry)
        _log(DECISIONS_LOG,
             f"[Collector:{agent.collector_name}] Accepted task {request_id} "
             f"in zone '{zone}'. Load: {agent.current_tasks}/{agent.max_tasks}.")

    async def _refuse(self, request_id: int, zone: str):
        agent = self.agent

        reply = Message(to=COORDINATOR_JID)
        reply.set_metadata("performative", "refuse")
        reply.set_metadata("ontology", "plastickonnect-waste-management")
        reply.body = json.dumps({
            "type": "task_refused",
            "request_id": request_id,
            "collector": agent.collector_name,
            "reason": "at_capacity",
            "current_tasks": agent.current_tasks,
        })
        await self.send(reply)

        entry = (
            f"[{agent.collector_name} → Coordinator] REFUSE task_refused | "
            f"request_id={request_id} reason=at_capacity "
            f"load={agent.current_tasks}/{agent.max_tasks}"
        )
        logger.warning(entry)
        _log(AGENT_MESSAGES_LOG, entry)
        _log(DECISIONS_LOG,
             f"[Collector:{agent.collector_name}] REFUSED task {request_id}. "
             f"At capacity ({agent.current_tasks}/{agent.max_tasks}).")
