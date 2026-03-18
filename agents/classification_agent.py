# agents/classification_agent.py
# ClassificationAgent — validates scans and detects fraudulent scanning patterns.
#
# Beliefs:  scan_history (dict username → list of timestamps)
# Goals:    G3.1, G3.2 – Validate scans; G4.1–G4.3 – Fraud detection
# Sends:    FAILURE(fraud_alert) → CampusCoordinatorAgent

import logging

from spade.agent import Agent

from config.settings import MONITOR_INTERVAL, AGENT_PASSWORD
from behaviours.fraud_detection import FraudDetectionBehaviour

logger = logging.getLogger(__name__)


class ClassificationAgent(Agent):
    """
    Validates scan quality and detects fraudulent scanning patterns.

    Beliefs
    -------
    flagged_users : set[str]  — usernames already flagged this session
    """

    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.flagged_users: set[str] = set()

    async def setup(self):
        logger.info(f"[Classifier] Agent started: {self.jid}")
        behaviour = FraudDetectionBehaviour(period=MONITOR_INTERVAL)
        self.add_behaviour(behaviour)
