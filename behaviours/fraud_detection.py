# behaviours/fraud_detection.py
# PeriodicBehaviour for ClassificationAgent.
# Scans all user activity and flags accounts whose scan rate is
# statistically impossible within the configured time window.

import json
import logging
from datetime import datetime, timedelta

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from config.settings import (
    FRAUD_SCAN_THRESHOLD,
    FRAUD_WINDOW_MINUTES,
    DECISIONS_LOG,
    AGENT_MESSAGES_LOG,
)
from config.agent_jids import COORDINATOR_JID
import api.client as api

logger = logging.getLogger(__name__)


def _log(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class FraudDetectionBehaviour(PeriodicBehaviour):
    """
    Runs every MONITOR_INTERVAL seconds.
    Fetches recent scan activity per user and flags anyone who exceeds
    FRAUD_SCAN_THRESHOLD scans within FRAUD_WINDOW_MINUTES.

    Expects self.agent to have:
        flagged_users : set[str]
    """

    async def run(self):
        agent = self.agent
        users = api.get_all_users()

        for user in users:
            username = user.get("username")
            if not username:
                continue

            activity = api.get_activity(username)
            if not activity:
                continue

            window_start = datetime.utcnow() - timedelta(minutes=FRAUD_WINDOW_MINUTES)
            recent_scans = [
                a for a in activity
                if a.get("type") == "scan"
                and self._parse_ts(a.get("created_at", "")) >= window_start
            ]

            if len(recent_scans) > FRAUD_SCAN_THRESHOLD and username not in agent.flagged_users:
                agent.flagged_users.add(username)
                await self._send_fraud_alert(username, len(recent_scans), recent_scans)

    def _parse_ts(self, ts_str: str) -> datetime:
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.min

    async def _send_fraud_alert(self, username: str, count: int, scans: list):
        timestamps = [s.get("created_at", "") for s in scans[:5]]

        msg = Message(to=COORDINATOR_JID)
        msg.set_metadata("performative", "failure")
        msg.set_metadata("ontology", "plastickonnect-waste-management")
        msg.body = json.dumps({
            "type": "fraud_alert",
            "username": username,
            "scan_count": count,
            "window_minutes": FRAUD_WINDOW_MINUTES,
            "sample_timestamps": timestamps,
            "threshold": FRAUD_SCAN_THRESHOLD,
        })
        await self.send(msg)
        api.flag_user_fraud(username)

        entry = (
            f"[Classifier → Coordinator] FAILURE fraud_alert | "
            f"user={username} scans={count} in {FRAUD_WINDOW_MINUTES}min"
        )
        logger.warning(entry)
        _log(AGENT_MESSAGES_LOG, entry)
        _log(DECISIONS_LOG,
             f"[Classifier] FRAUD detected: '{username}' submitted {count} scans "
             f"in {FRAUD_WINDOW_MINUTES} min (threshold={FRAUD_SCAN_THRESHOLD}). "
             f"Alert forwarded to Coordinator.")
