# behaviours/coordinate.py
# CyclicBehaviour for CampusCoordinatorAgent.
# Central message-processing loop — handles alerts from all agents,
# selects collectors, sends task assignments, and manages refusals.

import json
import logging

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from config.settings import (
    DECISIONS_LOG,
    AGENT_MESSAGES_LOG,
)
import api.client as api

logger = logging.getLogger(__name__)


def _log(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class CoordinateBehaviour(CyclicBehaviour):
    """
    Processes all incoming messages for the CampusCoordinatorAgent.

    Message types handled:
        INFORM  zone_alert        ← WasteSensorAgent overflow
        INFORM  zone_resolved     ← WasteSensorAgent clear
        INFORM  engagement_drop   ← GamificationAgent
        FAILURE fraud_alert       ← ClassificationAgent
        AGREE   task_accepted     ← CollectorAgent
        REFUSE  task_refused      ← CollectorAgent

    Expects self.agent to have:
        pending_alerts     : set[str]
        collector_registry : dict[str, dict]
        active_assignments : dict[int, str]
        unassigned_queue   : list[dict]
        busy_this_round    : set[str]
    """

    async def run(self):
        msg = await self.receive(timeout=10)
        if not msg:
            return

        performative = msg.metadata.get("performative", "")
        try:
            payload = json.loads(msg.body)
        except (json.JSONDecodeError, AttributeError):
            return

        msg_type = payload.get("type", "")
        agent = self.agent

        if performative == "inform" and msg_type == "zone_alert":
            await self._handle_zone_alert(payload)

        elif performative == "inform" and msg_type == "zone_resolved":
            zone = payload.get("zone")
            agent.pending_alerts.discard(zone)
            _log(DECISIONS_LOG, f"[Coordinator] Zone '{zone}' resolved. Alert cleared.")

        elif performative == "failure" and msg_type == "fraud_alert":
            await self._handle_fraud_alert(payload)

        elif performative == "inform" and msg_type == "engagement_drop":
            active = payload.get("active_users")
            duration = payload.get("bonus_duration_hours")
            entry = (
                f"[Coordinator] Engagement drop received. Active={active}. "
                f"Bonus event of {duration}h acknowledged."
            )
            logger.info(entry)
            _log(DECISIONS_LOG, entry)

        elif performative == "agree" and msg_type == "task_accepted":
            request_id = payload.get("request_id")
            collector = payload.get("collector")
            agent.active_assignments[request_id] = collector
            entry = f"[Coordinator] Task {request_id} ACCEPTED by '{collector}'."
            logger.info(entry)
            _log(DECISIONS_LOG, entry)
            _log(AGENT_MESSAGES_LOG,
                 f"[{collector} → Coordinator] AGREE task_accepted request_id={request_id}")

        elif performative == "refuse" and msg_type == "task_refused":
            await self._handle_refusal(payload)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _handle_zone_alert(self, payload: dict):
        agent = self.agent
        zone = payload.get("zone")
        count = payload.get("count")
        agent.pending_alerts.add(zone)

        all_pending = api.get_all_pending_requests()
        zone_requests = [r for r in all_pending if r.get("location_label") == zone]

        if not zone_requests:
            _log(DECISIONS_LOG,
                 f"[Coordinator] Alert for '{zone}' but no pending requests found.")
            return

        request_id = zone_requests[0].get("id")
        collector_jid = self._select_collector()

        if not collector_jid:
            _log(DECISIONS_LOG,
                 f"[Coordinator] No available collector for zone '{zone}'. "
                 f"Task {request_id} queued.")
            agent.unassigned_queue.append(payload)
            return

        await self._send_assignment(request_id, zone, count, collector_jid)

    async def _handle_refusal(self, payload: dict):
        agent = self.agent
        request_id = payload.get("request_id")
        refused_by = payload.get("collector")
        zone = payload.get("zone", "Unknown")

        _log(DECISIONS_LOG,
             f"[Coordinator] Task {request_id} REFUSED by '{refused_by}'. "
             f"Searching for next available collector.")

        agent.busy_this_round.add(refused_by)
        collector_jid = self._select_collector(exclude=agent.busy_this_round)

        if collector_jid:
            await self._send_assignment(request_id, zone, None, collector_jid)
        else:
            _log(DECISIONS_LOG,
                 f"[Coordinator] No alternative collector for task {request_id}. "
                 f"Task remains pending in API.")
            agent.busy_this_round.clear()

    async def _handle_fraud_alert(self, payload: dict):
        username = payload.get("username")
        count = payload.get("scan_count")
        window = payload.get("window_minutes")

        entry = (
            f"[Coordinator] FRAUD ALERT — user='{username}' "
            f"submitted {count} scans in {window} min. "
            f"Account flagged. Admin notified via decisions.log."
        )
        logger.warning(entry)
        _log(DECISIONS_LOG, entry)

    def _select_collector(self, exclude: set = None) -> str | None:
        """Return JID of least-loaded available collector not in exclude set."""
        exclude = exclude or set()
        agent = self.agent
        best_jid, best_load = None, float("inf")

        for jid, info in agent.collector_registry.items():
            name = info.get("name", "")
            if name in exclude:
                continue
            load = info.get("current_tasks", 0)
            max_load = info.get("max_tasks", 3)
            if load < max_load and load < best_load:
                best_load = load
                best_jid = jid

        return best_jid

    async def _send_assignment(self, request_id: int, zone: str,
                               count, collector_jid: str):
        msg = Message(to=collector_jid)
        msg.set_metadata("performative", "request")
        msg.set_metadata("ontology", "plastickonnect-waste-management")
        msg.body = json.dumps({
            "type": "assign_task",
            "request_id": request_id,
            "zone": zone,
            "count": count,
        })
        await self.send(msg)

        collector_name = collector_jid.split("@")[0].replace("collector_", "")
        entry = (
            f"[Coordinator → {collector_name}] REQUEST assign_task | "
            f"request_id={request_id} zone={zone}"
        )
        logger.info(entry)
        _log(AGENT_MESSAGES_LOG, entry)
        _log(DECISIONS_LOG,
             f"[Coordinator] Assigned task {request_id} (zone='{zone}') "
             f"to collector '{collector_name}'.")
