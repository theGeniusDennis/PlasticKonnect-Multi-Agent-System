# simulation/run_all.py
# Runs all 4 scenarios in sequence and summarises results.

import logging
logging.disable(logging.INFO)          # silence INFO and below globally
for _lib in ("pyjabber", "slixmpp", "spade", "aioxmpp", "aioopenssl", "asyncio"):
    logging.getLogger(_lib).setLevel(logging.CRITICAL)

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation import (
    scenario_1_zone_overflow,
    scenario_2_collector_refuse,
    scenario_3_engagement_drop,
    scenario_4_fraud,
)
from config.settings import SIMULATION_LOG

os.makedirs("logs", exist_ok=True)

# Clear previous simulation log
with open(SIMULATION_LOG, "w", encoding="utf-8") as f:
    f.write("PlasticKonnect Multi-Agent Simulation — All Scenarios\n")
    f.write("=" * 60 + "\n\n")


async def main():
    print("\n" + "="*60)
    print("  PlasticKonnect MAS — Running All Scenarios")
    print("="*60 + "\n")

    await scenario_1_zone_overflow.run()
    await asyncio.sleep(1)

    await scenario_2_collector_refuse.run()
    await asyncio.sleep(1)

    await scenario_3_engagement_drop.run()
    await asyncio.sleep(1)

    await scenario_4_fraud.run()

    print("\n" + "="*60)
    print("  All scenarios complete.")
    print(f"  Results: logs/simulation_results.log")
    print(f"  Messages: logs/agent_messages.log")
    print(f"  Decisions: logs/decisions.log")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
