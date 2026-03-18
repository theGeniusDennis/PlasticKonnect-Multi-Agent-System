# behaviours/engagement_check.py
# PeriodicBehaviour for GamificationAgent.
# Checks daily active user count and streak milestones.
# Triggers bonus events and awards milestone badges.

import json
import logging

from spade.behaviour import PeriodicBehaviour
from spade.message import Message

from config.settings import (
    ENGAGEMENT_THRESHOLD,
    BONUS_EVENT_DURATION_H,
    STREAK_MILESTONES,
    MILESTONE_BONUS_POINTS,
    DECISIONS_LOG,
    AGENT_MESSAGES_LOG,
)
from config.agent_jids import COORDINATOR_JID
import api.client as api

logger = logging.getLogger(__name__)


def _log(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


class EngagementCheckBehaviour(PeriodicBehaviour):
    """
    Runs every ENGAGEMENT_CHECK_HOURS (converted to seconds).
    1. Counts daily active users — triggers bonus event if below threshold.
    2. Scans all users for streak milestones and awards bonus points.

    Expects self.agent to have:
        daily_active_count : int
        bonus_event_active : bool
        checked_milestones : set[str]
    """

    async def run(self):
        agent = self.agent

        # ── 1. Daily engagement check ────────────────────────────────────────
        active_count = api.get_daily_active_users()
        agent.daily_active_count = active_count

        if active_count < ENGAGEMENT_THRESHOLD and not agent.bonus_event_active:
            agent.bonus_event_active = True

            msg = Message(to=COORDINATOR_JID)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "plastickonnect-waste-management")
            msg.body = json.dumps({
                "type": "engagement_drop",
                "active_users": active_count,
                "threshold": ENGAGEMENT_THRESHOLD,
                "bonus_duration_hours": BONUS_EVENT_DURATION_H,
            })
            await self.send(msg)

            entry = (
                f"[Gamification → Coordinator] INFORM engagement_drop | "
                f"active={active_count} threshold={ENGAGEMENT_THRESHOLD}"
            )
            logger.warning(entry)
            _log(AGENT_MESSAGES_LOG, entry)
            _log(DECISIONS_LOG,
                 f"[Gamification] Only {active_count} active users today "
                 f"(threshold={ENGAGEMENT_THRESHOLD}). "
                 f"Bonus event triggered for {BONUS_EVENT_DURATION_H}h.")

        elif active_count >= ENGAGEMENT_THRESHOLD and agent.bonus_event_active:
            agent.bonus_event_active = False
            entry = (
                f"[Gamification] Engagement recovered: {active_count} active users. "
                f"Bonus event deactivated."
            )
            logger.info(entry)
            _log(DECISIONS_LOG, entry)

        # ── 2. Streak milestone check ─────────────────────────────────────────
        users = api.get_all_users()
        for user in users:
            username = user.get("username")
            streak = user.get("streak", 0)
            if not username or streak == 0:
                continue

            for milestone in STREAK_MILESTONES:
                key = f"{username}:{milestone}"
                if streak >= milestone and key not in agent.checked_milestones:
                    agent.checked_milestones.add(key)
                    bonus = MILESTONE_BONUS_POINTS[milestone]

                    api.award_bonus_points(
                        username, bonus,
                        f"streak_milestone_{milestone}_days"
                    )

                    entry = (
                        f"[Gamification] Milestone! {username} reached "
                        f"{milestone}-day streak → +{bonus} pts awarded."
                    )
                    logger.info(entry)
                    _log(DECISIONS_LOG, entry)
                    _log(AGENT_MESSAGES_LOG, entry)
