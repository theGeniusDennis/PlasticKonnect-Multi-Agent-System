# PlasticKonnect Multi-Agent System

**DCIT 403 — Intelligent Agent Systems | University of Ghana**
**Student:** Denis Annor
**Methodology:** Prometheus AOSE | **Framework:** SPADE 4.1.2 | **Language:** Python 3.12

---

## Overview

A Multi-Agent System (MAS) that automates the coordination layer of the [PlasticKonnect](https://github.com/theGeniusDennis/PlasticKonnect) campus plastic waste management platform. Five specialised agents communicate via FIPA-ACL messages over XMPP to handle zone overflow, collector dispatch, fraud detection, and student engagement — entirely without human intervention.

---

## Agents

| Agent | Role | Behaviour |
|-------|------|-----------|
| `WasteSensorAgent` | Monitors campus zones for overflow | PeriodicBehaviour (30s) |
| `CampusCoordinatorAgent` | Central orchestrator — routes all messages | CyclicBehaviour |
| `CollectorAgent` | Accepts or refuses task assignments | CyclicBehaviour |
| `ClassificationAgent` | Detects fraudulent scanning via sliding-window rate analysis | PeriodicBehaviour (30s) |
| `GamificationAgent` | Triggers bonus events and awards streak milestones | PeriodicBehaviour (1h) |

---

## Project Structure

```
intelligent_agents/
├── agents/                  # Agent identity and setup (one file per agent)
├── behaviours/              # Behaviour logic (separated by concern)
│   ├── monitor_zones.py
│   ├── coordinate.py
│   ├── handle_task.py
│   ├── fraud_detection.py
│   └── engagement_check.py
├── config/
│   ├── settings.py          # All thresholds and constants
│   └── agent_jids.py        # XMPP JID definitions
├── api/
│   └── client.py            # All HTTP calls to PlasticKonnect REST API
├── simulation/
│   ├── mock_api.py          # Monkey-patched API for offline testing
│   ├── xmpp_server.py       # Embedded pyjabber XMPP server manager
│   ├── scenario_1_zone_overflow.py
│   ├── scenario_2_collector_refuse.py
│   ├── scenario_3_engagement_drop.py
│   ├── scenario_4_fraud.py
│   └── run_all.py           # Run all 4 scenarios in sequence
├── logs/                    # agent_messages.log, decisions.log
├── main.py                  # Production entry point
├── requirements.txt
├── plan.md                  # Full Prometheus design document
└── report.md                # Project report
```

---

## Setup

**Requirements:** Python 3.12+

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt
```

---

## Running the Simulation

Run all 4 scenarios in sequence:

```bash
python -m simulation.run_all
```

Or run a specific scenario:

```bash
python -m simulation.scenario_1_zone_overflow
python -m simulation.scenario_2_collector_refuse
python -m simulation.scenario_3_engagement_drop
python -m simulation.scenario_4_fraud
```

After running, check the logs:

```bash
logs/agent_messages.log   # All FIPA-ACL message exchanges
logs/decisions.log        # Agent decisions and actions
```

---

## Simulation Scenarios

| # | Scenario | Setup | Expected Outcome |
|---|----------|-------|-----------------|
| 1 | **The Overflowing Zone** | Science Block = 22 pickups (threshold = 10) | Coordinator assigns to Kwame ✅ |
| 2 | **The Reluctant Collector** | Kwame at full capacity (3/3) | Kwame refuses → Abena accepts ✅ |
| 3 | **The Quiet Tuesday** | Only 4 active users (threshold = 20) | Bonus event triggered ✅ |
| 4 | **The Suspicious Scanner** | user99 has 60 scans in 4 min (threshold = 8) | user99 flagged for fraud ✅ |

---

## Key Configuration (`config/settings.py`)

| Constant | Default | Description |
|----------|---------|-------------|
| `ZONE_OVERFLOW_THRESHOLD` | 10 | Pending pickups before zone alert fires |
| `COLLECTOR_MAX_TASKS` | 3 | Max concurrent tasks per collector |
| `FRAUD_SCAN_THRESHOLD` | 8 | Max scans per 4-minute window |
| `ENGAGEMENT_THRESHOLD` | 20 | Min daily active users before bonus event |
| `STREAK_MILESTONES` | 7, 30, 100 | Days at which bonus points are awarded |

---

## Production Run

To run against the live PlasticKonnect API:

```bash
python main.py
```

Requires a running XMPP server (Prosody or ejabberd) with credentials matching `config/settings.py`.

---

## Report

Full project report: [report.md](report.md)
Full Prometheus design: [plan.md](plan.md)
