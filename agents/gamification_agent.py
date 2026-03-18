# agents/gamification_agent.py
# GamificationAgent — manages student engagement, streaks, and bonus events.
#
# Beliefs:  daily_active_count, bonus_event_active, checked_milestones
# Goals:    G2.1–G2.4 – Sustain student participation; G3.3 – Log point transactions
# Sends:    INFORM(engagement_drop / bonus_triggered) → CampusCoordinatorAgent

import logging

from spade.agent import Agent

from config.settings import ENGAGEMENT_CHECK_HOURS, AGENT_PASSWORD
from behaviours.engagement_check import EngagementCheckBehaviour

logger = logging.getLogger(__name__)

ENGAGEMENT_CHECK_SECONDS = ENGAGEMENT_CHECK_HOURS * 3600


class GamificationAgent(Agent):
    """
    Monitors student engagement and manages reward events.

    Beliefs
    -------
    daily_active_count : int      — today's active user count
    bonus_event_active : bool     — whether a bonus event is running
    checked_milestones : set[str] — "username:milestone" already awarded
    """

    def __init__(self, jid: str, password: str):
        super().__init__(jid, password)
        self.daily_active_count: int = 0
        self.bonus_event_active: bool = False
        self.checked_milestones: set[str] = set()

    async def setup(self):
        logger.info(f"[Gamification] Agent started: {self.jid}")
        behaviour = EngagementCheckBehaviour(period=ENGAGEMENT_CHECK_SECONDS)
        self.add_behaviour(behaviour)
