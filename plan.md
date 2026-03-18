# DCIT 403 – Individual Intelligent Agent Project
## PlasticKonnect Campus Waste Coordination System

**Student:** Denis Annor
**Course:** DCIT 403 – Designing Intelligent Agent Systems
**University:** University of Ghana
**Methodology:** Prometheus Agent-Oriented Software Engineering
**Framework:** SPADE (Smart Python Agent Development Environment)
**Language:** Python 3.9+

---

## Project Directory Structure

```
intelligent_agents/
│
├── plan.md                          ← This document (full Prometheus design)
│
├── main.py                          ← Entry point — starts all agents
├── requirements.txt                 ← Python dependencies
├── README.md                        ← Setup and run instructions
│
├── agents/                          ← One file per agent type
│   ├── __init__.py
│   ├── waste_sensor_agent.py        ← WasteSensorAgent
│   ├── classification_agent.py      ← ClassificationAgent
│   ├── collector_agent.py           ← CollectorAgent (parameterised — one instance per collector)
│   ├── gamification_agent.py        ← GamificationAgent
│   └── coordinator_agent.py         ← CampusCoordinatorAgent
│
├── behaviours/                      ← SPADE behaviour classes (separated for reuse)
│   ├── __init__.py
│   ├── monitor_zones.py             ← PeriodicBehaviour — polls API every 30s
│   ├── handle_task.py               ← CyclicBehaviour — collector task accept/refuse loop
│   ├── coordinate.py                ← CyclicBehaviour — coordinator assignment logic
│   ├── engagement_check.py          ← PeriodicBehaviour — daily engagement check
│   └── fraud_detection.py           ← CyclicBehaviour — scan rate analysis
│
├── api/                             ← PlasticKonnect API client
│   ├── __init__.py
│   └── client.py                    ← All HTTP calls to PlasticKonnect backend in one place
│
├── config/                          ← Configuration and constants
│   ├── __init__.py
│   ├── settings.py                  ← API base URL, thresholds, timeouts
│   └── agent_jids.py                ← JID (XMPP address) definitions for all agents
│
├── simulation/                      ← Scripts to simulate the 4 scenarios without live API
│   ├── __init__.py
│   ├── mock_api.py                  ← Simulated API responses (fake zone/scan/pickup data)
│   ├── scenario_1_zone_overflow.py  ← Runs Scenario 1: Zone Overflow
│   ├── scenario_2_collector_refuse.py ← Runs Scenario 2: Collector Rejection
│   ├── scenario_3_engagement_drop.py ← Runs Scenario 3: Low Engagement
│   ├── scenario_4_fraud.py          ← Runs Scenario 4: Fraud Detection
│   └── run_all.py                   ← Runs all 4 scenarios in sequence
│
├── logs/                            ← Auto-generated at runtime
│   ├── agent_messages.log           ← All FIPA-ACL messages sent/received
│   ├── decisions.log                ← Coordinator decision trail
│   └── simulation_results.log       ← Output from simulation runs
│
└── diagrams/                        ← Static design artifacts (Draw.io exports)
    ├── system_architecture.png      ← 5-agent architecture diagram
    ├── acquaintance_diagram.png      ← Which agents communicate
    ├── fsm_sensor_agent.png         ← FSM: MONITORING → ALERT → RESOLVED
    ├── goal_hierarchy.png           ← Prometheus goal tree (Phase 1)
    ├── auml_scenario_1.png          ← Interaction diagram — Zone Overflow
    ├── auml_scenario_2.png          ← Interaction diagram — Collector Refuse
    ├── auml_scenario_3.png          ← Interaction diagram — Engagement Drop
    ├── auml_scenario_4.png          ← Interaction diagram — Fraud Detection
    └── capability_diagrams.png      ← All 5 agent capability diagrams
```

### Key Design Decisions

| Decision | Reasoning |
|----------|-----------|
| `agents/` and `behaviours/` are separate | Keeps agent identity (JID, beliefs) separate from logic; behaviours can be unit-tested independently |
| `api/client.py` centralises all HTTP calls | If the PlasticKonnect API changes, only one file needs updating |
| `simulation/mock_api.py` mirrors real API | Allows all 4 scenarios to run in GitHub Codespaces without needing the live Railway backend |
| One file per scenario in `simulation/` | Each scenario maps directly to a Phase 1 scenario — easy to demo per deliverable |
| `logs/` is auto-generated | Provides the message logs and execution traces required as lab deliverables |
| `diagrams/` contains exported PNGs | Draw.io files are edited externally; exported images are committed for submission |

---

# PHASE 1 – System Specification

> *This phase defines what the system should do, not how.*

---

## 1. Problem Description

### What problem are you solving?

Plastic waste mismanagement is a growing environmental problem on university campuses.
At the University of Ghana, students generate large volumes of plastic waste daily — bottles,
sachets, packaging — but the collection and coordination process is entirely manual.
Collectors do not know which zones have the most pending pickups. Students have no
real incentive to sort and submit their waste consistently. When engagement drops,
nobody intervenes proactively. When a zone overflows with uncollected bags, no one
is automatically notified.

The result: plastic waste sits unattended, collection is inefficient, and student
participation declines over time because there is no feedback loop keeping them engaged.

### Why is an agent appropriate?

A traditional software system reacts only when a user takes an action. This problem
requires a system that **acts on its own** — one that continuously monitors the
environment, notices when something is wrong, makes decisions, and takes corrective
action without waiting for a human to initiate it.

Specifically:
- The environment changes constantly (new scans, new pickups, student activity rising and falling)
- Decisions depend on dynamic conditions (which collector is available, how severe a zone is)
- Multiple independent tasks must run simultaneously (monitoring zones while also tracking student engagement)
- Coordination between actors (students, collectors, admin) is complex and can fail (e.g., a collector rejects a task)

These are precisely the conditions where an **intelligent, autonomous, goal-directed agent** is the appropriate solution.

### Who are the users/stakeholders?

| Stakeholder | Role |
|-------------|------|
| **Students** | Scan and submit plastic waste to earn eco-points |
| **Collectors** | Physically pick up bags of sorted plastic from zones |
| **Campus Admin** | Oversees the system; receives alerts for fraud or failures |
| **PlasticKonnect Platform** | The live system the agents interact with via API |

---

## 2. Goal Specification

### Top-Level Goals (Main Objectives)

| ID | Goal |
|----|------|
| G1 | Maximize plastic waste collection efficiency across all campus zones |
| G2 | Sustain consistent student participation in waste scanning |
| G3 | Ensure all eco-point rewards are distributed correctly and fairly |
| G4 | Protect system integrity against fraudulent scanning activity |

### Sub-Goals (Supporting Objectives)

```
G1 – Maximize collection efficiency
    G1.1 – Detect when a zone has too many pending pickups
    G1.2 – Assign a collector to the zone promptly
    G1.3 – Handle collector rejection and reassign the task
    G1.4 – Confirm task completion and update zone status

G2 – Sustain student participation
    G2.1 – Monitor daily scan activity per student
    G2.2 – Detect when engagement falls below acceptable threshold
    G2.3 – Trigger a bonus points event to re-motivate students
    G2.4 – Track and reward streak milestones (7, 30, 100 days)

G3 – Correct reward distribution
    G3.1 – Award eco-points only after a valid, verified scan
    G3.2 – Confirm scan confidence is above the required threshold
    G3.3 – Log all point transactions for audit

G4 – Protect system integrity
    G4.1 – Monitor scan frequency per student
    G4.2 – Detect statistically impossible scanning patterns
    G4.3 – Flag suspicious accounts and alert admin
```

---

## 3. Functionalities

*What the system should be able to do (no technical details):*

1. **Monitor campus zones** — continuously check how much plastic waste is waiting to be collected in each zone of the campus
2. **Detect zone overflow** — recognise when a zone has more pending pickups than it can handle without intervention
3. **Assign collection tasks** — automatically direct available collectors to zones that need attention, ranked by urgency
4. **Handle task rejection** — if a collector cannot take a task, find another one and reassign without losing the request
5. **Validate plastic scans** — confirm that a submitted scan is genuine and correctly classified before awarding points
6. **Detect fraud** — identify when a student is scanning at an implausible rate and alert the administrator
7. **Track student streaks** — maintain daily engagement records and celebrate milestones automatically
8. **Trigger engagement events** — when student activity falls too low, activate a bonus reward period to revive participation
9. **Log all agent decisions** — keep a full record of what each agent decided, why, and what action it took

---

## 4. Scenarios

### Scenario 1: "The Overflowing Zone"
It is Monday afternoon at the Science Block. Students returning from lectures have
scanned 22 plastic bottles, creating 22 pending pickup entries. The system notices
this number has crossed the critical threshold of 10. Without any human input, it
identifies the least-loaded available collector, sends them an assignment, and the
collector accepts and heads to Science Block. Once the pickup is done, the students'
points are confirmed and the zone status resets. The whole process takes under 2 minutes.

### Scenario 2: "The Reluctant Collector"
The Coordinator assigns a high-priority task in the Engineering Quad to Collector Kwame.
Kwame already has 3 active tasks and sends back a refusal. The Coordinator does not
panic — it immediately checks the next available collector, finds Abena who has capacity,
and reassigns the task to her. Abena accepts and completes the pickup. The failed
assignment and successful reassignment are both logged for performance review.

### Scenario 3: "The Quiet Tuesday"
By 10 AM on a Tuesday, only 4 students have scanned any plastic — well below the
daily engagement threshold of 20. The system's engagement monitor detects this drop.
It decides to activate a double-points event for the next 3 hours and logs the decision.
By 1 PM, 31 students have scanned, bringing engagement back to healthy levels.

### Scenario 4: "The Suspicious Scanner"
A student account named "user99" submits 60 scan records within 4 minutes. Given
that manual scanning takes at least 30 seconds per item, this is physically impossible.
The system flags this as a fraud pattern, immediately pauses point-earning for that
account, and sends an alert to the administrator with the scan timestamps and count
as evidence.

### Scenario 5: "The 30-Day Streak"
Ama has scanned plastic waste every day for 30 consecutive days. The gamification
monitor detects this milestone. It awards her a special badge and a bonus 30 eco-points.
A log entry is created celebrating the achievement, which also appears in her activity
feed on the PlasticKonnect app.

---

## 5. Environment Description

### The Environment

The agents operate in a **mixed digital-physical environment**:

- **Physical:** University of Ghana campus, divided into named zones (Science Block, Arts Centre, Volta Hall, Commonwealth Hall, Bush Canteen, etc.). Each zone has physical plastic waste collection points.
- **Digital:** The PlasticKonnect web application and its REST API backend (FastAPI, deployed on Railway). This is the authoritative source of truth — scan records, pickup requests, user points, and collector availability all live here.

### What does the agent perceive?

| Percept | Source |
|---------|--------|
| Number of pending pickups per zone | PlasticKonnect `/api/pickups` endpoint |
| Time since last scan in a zone | PlasticKonnect scan records |
| Collector availability and current task load | PlasticKonnect collector records |
| Student scan count per day | PlasticKonnect user activity data |
| Student streak history | PlasticKonnect user database |
| Scan confidence scores from AI classifier | PlasticKonnect `/api/scan` result |
| Scan frequency per student per minute | PlasticKonnect scan timestamps |
| FIPA-ACL messages from other agents | XMPP server |

### What can it act upon?

| Action | Effect |
|--------|--------|
| Send zone alert to Coordinator | Triggers task assignment process |
| Assign pickup task to Collector | Collector navigates to zone and collects |
| Trigger bonus points event | Doubles student point earnings for a period |
| Award badge to student | Updates student profile and activity feed |
| Flag fraudulent account | Freezes point-earning for that account |
| Log decisions | Creates audit trail for all agent activity |
| Reassign rejected tasks | Ensures no pickup request is left unhandled |

### How can the agents affect the environment?

Agents affect the environment by calling the PlasticKonnect REST API to:
- Update pickup status (assigned, completed)
- Modify user point balances (bonus events, badge awards)
- Add entries to the redemption/activity feed
- Flag user accounts for admin review
- Change zone alert status

The environment is therefore **dynamic and partially observable** — agents can see
the data exposed by the API but cannot observe physical collector positions directly.
Decisions must account for this uncertainty.

---

# PHASE 2 – Architectural Design

> *This phase defines the structure of the agent system.*

---

## 1. Agent Types

The system uses **5 agent types**. Multiple agents are justified because:

- The problem has **distinct, separable concerns** (sensing, classifying, collecting, rewarding, coordinating) that would create an unmanageable single agent if combined
- Some agents need to run **simultaneously** (zone monitoring and engagement checking cannot block each other)
- **Multiple Collector Agents** (one per active collector) allow genuine task negotiation — a core MAS requirement
- Separate agents can **fail independently** without crashing the whole system

| Agent | Count | Purpose |
|-------|-------|---------|
| WasteSensorAgent | 1 | Monitors zone waste levels continuously |
| ClassificationAgent | 1 | Validates scans and detects fraud |
| CollectorAgent | 1 per collector | Receives, accepts/rejects, and executes pickup tasks |
| GamificationAgent | 1 | Manages streaks, badges, and engagement events |
| CampusCoordinatorAgent | 1 | Central decision-maker; coordinates all other agents |

---

## 2. Grouping Functionalities

| Functionality | Agent Assigned | Reasoning |
|---------------|---------------|-----------|
| Monitor zone pending pickups | WasteSensorAgent | Sensing is a distinct concern; runs on a timer independently of decision-making |
| Detect zone overflow | WasteSensorAgent | Same data source as monitoring; natural grouping |
| Assign collection tasks | CampusCoordinatorAgent | Requires knowledge of all zones AND all collectors — only Coordinator has both |
| Handle task rejection/reassignment | CampusCoordinatorAgent | Reassignment is a coordination decision, not a sensing or collecting one |
| Validate scan confidence | ClassificationAgent | Classification logic is self-contained and reusable |
| Detect fraudulent scanning | ClassificationAgent | Shares the same scan data source as validation |
| Track student streaks | GamificationAgent | Gamification state is internal and does not depend on other agents' data |
| Trigger bonus events | GamificationAgent | Engagement decisions are self-contained within the reward domain |
| Execute physical pickup | CollectorAgent | Each collector is an autonomous entity that decides its own capacity |

---

## 3. Acquaintance Diagram

```
                    ┌──────────────────────────┐
                    │   CampusCoordinatorAgent  │
                    └───┬──────┬───────┬────────┘
                        │      │       │
           INFORM(alert)│      │       │INFORM(engagement_drop)
                        │      │       │
              ┌─────────▼──┐   │   ┌───▼─────────────┐
              │WasteSensor │   │   │ GamificationAgent│
              │   Agent    │   │   └─────────────────-┘
              └────────────┘   │
                               │REQUEST(assign_task)
                    ┌──────────▼──────────────────┐
                    │      CollectorAgent(s)        │
                    │  (AGREE / REFUSE / INFORM)    │
                    └──────────────────────────────┘

              ┌────────────────────┐
              │ ClassificationAgent│──FAILURE(fraud)──► CampusCoordinatorAgent
              └────────────────────┘
```

**Communication summary:**
- WasteSensorAgent → CampusCoordinatorAgent: zone overflow alerts
- CampusCoordinatorAgent → CollectorAgent: task assignment requests
- CollectorAgent → CampusCoordinatorAgent: accept, refuse, or completion
- GamificationAgent → CampusCoordinatorAgent: engagement drop notifications
- ClassificationAgent → CampusCoordinatorAgent: fraud alerts

---

## 4. Agent Descriptors

### WasteSensorAgent

| Field | Detail |
|-------|--------|
| **Responsibilities** | Poll the PlasticKonnect API every 30 seconds; compare pending pickup counts against thresholds; send alerts when zones overflow; send resolution notices when zones clear |
| **Goals handled** | G1.1 – Detect zone overflow |
| **Data used** | Zone IDs, pending pickup counts, overflow thresholds, last-alert timestamps |
| **Interactions** | Sends INFORM messages to CampusCoordinatorAgent |

### ClassificationAgent

| Field | Detail |
|-------|--------|
| **Responsibilities** | Monitor new scan events; verify confidence score meets minimum threshold; detect implausible scan frequencies; flag fraud accounts |
| **Goals handled** | G3.1, G3.2 – Validate scans; G4.1, G4.2, G4.3 – Fraud detection |
| **Data used** | Scan records, confidence scores, scan timestamps per student, fraud frequency threshold |
| **Interactions** | Sends FAILURE (fraud) messages to CampusCoordinatorAgent |

### CollectorAgent

| Field | Detail |
|-------|--------|
| **Responsibilities** | Receive task assignments; decide to accept based on current capacity; execute the pickup by calling the API; report completion or failure |
| **Goals handled** | G1.2 – Carry out collection task |
| **Data used** | Own collector ID, current task count, max capacity (3 tasks), assigned task list |
| **Interactions** | Receives REQUEST from CampusCoordinatorAgent; replies with AGREE or REFUSE; sends INFORM on completion |

### GamificationAgent

| Field | Detail |
|-------|--------|
| **Responsibilities** | Check daily active user count; detect engagement drops; trigger bonus events; check streak milestones; award badges |
| **Goals handled** | G2.1–G2.4 – Sustain student participation; G3.3 – Log point transactions |
| **Data used** | Daily scan counts, engagement threshold, student streak records, milestone values (7, 30, 100 days), bonus event flag |
| **Interactions** | Sends INFORM (engagement_drop / bonus_triggered) to CampusCoordinatorAgent |

### CampusCoordinatorAgent

| Field | Detail |
|-------|--------|
| **Responsibilities** | Receive all alerts; select the best available collector for each task; send task assignments; handle refusals and reassign; log all decisions; relay fraud alerts to admin |
| **Goals handled** | G1.2, G1.3, G1.4 – Assignment and reassignment; G4.3 – Admin alert |
| **Data used** | Zone severity map, collector availability map, active assignment list, reassignment history |
| **Interactions** | Receives from WasteSensorAgent, ClassificationAgent, GamificationAgent; sends REQUEST to CollectorAgents |

---

# PHASE 3 – Interaction Design

> *This phase defines how agents communicate.*

---

## 1. Interaction Diagrams

### Message Structure

All messages follow FIPA-ACL format over XMPP:

```
ACLMessage {
  performative: INFORM | REQUEST | AGREE | REFUSE | FAILURE | PROPOSE
  sender:       <agent_jid>@localhost
  receiver:     <agent_jid>@localhost
  content:      JSON string
  ontology:     "plastickonnect-waste-management"
  language:     "JSON"
}
```

---

### Interaction 1: Zone Overflow → Pickup Assigned (Scenario 1)

```
WasteSensorAgent          CampusCoordinatorAgent       CollectorAgent_A
       |                          |                           |
       |──INFORM(zone_alert)─────>|                           |
       |  {zone:"science_block",  |                           |
       |   pending:22,            |                           |
       |   severity:"HIGH"}       |                           |
       |                          |──REQUEST(assign_task)────>|
       |                          |  {zone:"science_block",   |
       |                          |   pickup_ids:[12,13,14],  |
       |                          |   priority:"HIGH"}        |
       |                          |                           |
       |                          |<──AGREE─────────────────--|
       |                          |                           |──(executes pickup)
       |                          |                           |
       |                          |<──INFORM(task_complete)---|
       |                          |  {zone:"science_block",   |
       |                          |   status:"done"}          |
       |──INFORM(resolved)───────>|                           |
```

---

### Interaction 2: Collector Rejection → Reassignment (Scenario 2)

```
CampusCoordinatorAgent       CollectorAgent_A        CollectorAgent_B
       |                          |                       |
       |──REQUEST(assign_task)───>|                       |
       |                          |                       |
       |<──REFUSE─────────────────|                       |
       |  {reason:"at_capacity"}  |                       |
       |                          |                       |
       |──REQUEST(assign_task)────────────────────────────>|
       |                          |                       |
       |<──AGREE───────────────────────────────────────────|
       |                          |                       |──(executes)
       |<──INFORM(task_complete)───────────────────────────|
```

---

### Interaction 3: Engagement Drop → Bonus Event (Scenario 3)

```
GamificationAgent         CampusCoordinatorAgent
       |                          |
       |──INFORM(engagement_drop)>|
       |  {active_today:4,        |
       |   threshold:20,          |
       |   suggestion:"bonus"}    |
       |                          |──(calls PlasticKonnect API to activate bonus)
       |<──INFORM(bonus_active)───|
       |  {duration_hours:3}      |
```

---

### Interaction 4: Fraud Detection (Scenario 4)

```
ClassificationAgent        CampusCoordinatorAgent
       |                          |
       |──FAILURE(fraud_detected)>|
       |  {username:"user99",     |
       |   scan_count:60,         |
       |   window_minutes:4,      |
       |   evidence:[timestamps]} |
       |                          |──(freezes account + alerts admin)
```

---

# PHASE 4 – Detailed Design

> *This phase defines agent internals.*

---

## 1. Capabilities

### WasteSensorAgent Capabilities

| Capability | Grouped Behaviors | Triggering Event |
|------------|------------------|-----------------|
| `sense_zone_levels` | Poll API, parse pending counts | Timer fires every 30 seconds |
| `evaluate_thresholds` | Compare counts against limits | New poll data received |
| `send_zone_alert` | Compose and send INFORM message | Zone count exceeds threshold |
| `send_resolution` | Notify zone has cleared | Zone count returns below threshold |

### ClassificationAgent Capabilities

| Capability | Grouped Behaviors | Triggering Event |
|------------|------------------|-----------------|
| `validate_scan` | Check confidence score ≥ 0.85 | New scan event detected |
| `detect_fraud` | Compute scan rate per student per minute | New scan event detected |
| `report_anomaly` | Send FAILURE message to Coordinator | Fraud pattern identified |

### CollectorAgent Capabilities

| Capability | Grouped Behaviors | Triggering Event |
|------------|------------------|-----------------|
| `evaluate_capacity` | Check current_tasks < MAX_TASKS | REQUEST message received |
| `accept_task` | Send AGREE, update task list | Capacity available |
| `reject_task` | Send REFUSE with reason | At capacity |
| `execute_pickup` | Call PlasticKonnect API to complete pickup | Task accepted |
| `report_completion` | Send INFORM(task_complete) to Coordinator | API confirms completion |

### GamificationAgent Capabilities

| Capability | Grouped Behaviors | Triggering Event |
|------------|------------------|-----------------|
| `check_daily_engagement` | Count active students in last 24h | Daily timer (08:00) |
| `trigger_bonus_event` | Send INFORM to Coordinator | Active count < threshold |
| `check_streak_milestones` | Compare streak against 7, 30, 100 | Scan logged for student |
| `award_badge` | Update student profile via API | Milestone reached |

### CampusCoordinatorAgent Capabilities

| Capability | Grouped Behaviors | Triggering Event |
|------------|------------------|-----------------|
| `receive_zone_alert` | Process INFORM from SensorAgent | INFORM(zone_alert) received |
| `select_collector` | Find collector with lowest load | Zone alert processing |
| `assign_task` | Send REQUEST to selected collector | Collector selected |
| `handle_refusal` | Try next collector | REFUSE received |
| `confirm_completion` | Update zone status | INFORM(task_complete) received |
| `handle_fraud_alert` | Freeze account, alert admin | FAILURE(fraud) received |

---

## 2. Plans

### Plan: monitor_zones (WasteSensorAgent)
```
TRIGGER: Timer — every 30 seconds

STEPS:
  1. Call GET /api/pickups on PlasticKonnect API
  2. Group pending pickups by zone
  3. FOR each zone:
       IF pending_count > OVERFLOW_THRESHOLD (10):
         IF zone not already alerted:
           send INFORM(zone_alert) to CampusCoordinatorAgent
           mark zone as alerted
       IF pending_count ≤ CLEAR_THRESHOLD (3):
         IF zone was previously alerted:
           send INFORM(zone_resolved) to CampusCoordinatorAgent
           clear alert flag for zone

FAILURE HANDLING:
  IF API call fails: retry after 10 seconds; log failure
```

### Plan: assign_pickup_task (CampusCoordinatorAgent)
```
TRIGGER: INFORM(zone_alert) received from WasteSensorAgent

STEPS:
  1. Extract zone_id and severity from message
  2. Query available CollectorAgents (current_tasks < MAX_TASKS)
  3. Sort by ascending current_tasks (least loaded first)
  4. Send REQUEST(assign_task) to first collector
  5. Wait for AGREE or REFUSE (timeout: 15 seconds)
  6. IF AGREE:
       Record assignment; wait for INFORM(task_complete)
  7. IF REFUSE or timeout:
       Try next collector in list
       IF no collectors available:
         Log "unassigned_zone_alert" for admin review

ALTERNATIVE PLAN: If all collectors refuse, log to admin dashboard and retry
after 10 minutes.
```

### Plan: handle_task_assignment (CollectorAgent)
```
TRIGGER: REQUEST(assign_task) message received

STEPS:
  1. Read current_tasks count from beliefs
  2. IF current_tasks < MAX_TASKS (3):
       Send AGREE to CampusCoordinatorAgent
       Add task to assigned_tasks belief
       Call POST /api/pickup/{id}/assign on PlasticKonnect API
       [simulate travel + collection]
       Call POST /api/pickup/{id}/complete
       Remove task from assigned_tasks
       Send INFORM(task_complete) to CampusCoordinatorAgent
  3. ELSE:
       Send REFUSE with body {reason: "at_capacity"}

FAILURE HANDLING:
  IF API call fails during execution: send FAILURE to Coordinator
  Coordinator will mark task as unresolved and reassign
```

### Plan: check_engagement (GamificationAgent)
```
TRIGGER: Daily timer at 08:00 OR scan rate drops below alert level

STEPS:
  1. Call GET /api/users/activity?period=24h
  2. Count distinct users who scanned at least once
  3. IF active_count < ENGAGEMENT_THRESHOLD (20):
       Send INFORM(engagement_drop) to CampusCoordinatorAgent
         body: {active_today, threshold, suggestion: "bonus_event"}
  4. FOR each student:
       Check consecutive_scan_days
       IF streak in [7, 30, 100]:
         Call POST /api/users/{id}/badge to award milestone badge
         Log achievement
```

### Plan: detect_fraud (ClassificationAgent)
```
TRIGGER: New scan event received

STEPS:
  1. Retrieve last N scans for this student in the past TIME_WINDOW (5 minutes)
  2. IF scan_count_in_window > FRAUD_THRESHOLD (15):
       Compute scan rate (scans per minute)
       IF rate > MAX_PLAUSIBLE_RATE (3 per minute):
         Compile evidence (timestamps, count, rate)
         Send FAILURE(fraud_detected) to CampusCoordinatorAgent
  3. ELSE: approve scan and log as valid
```

---

## 3. Data Description

### WasteSensorAgent Beliefs

```python
beliefs = {
    "zone_status": {
        "science_block":   {"pending": 0, "alerted": False},
        "arts_centre":     {"pending": 0, "alerted": False},
        "volta_hall":      {"pending": 0, "alerted": False},
        "bush_canteen":    {"pending": 0, "alerted": False},
    },
    "overflow_threshold": 10,
    "clear_threshold": 3,
    "poll_interval_seconds": 30
}
```

### CollectorAgent Beliefs

```python
beliefs = {
    "collector_id": "collector_001",
    "current_tasks": [],          # list of active task IDs
    "max_tasks": 3,
    "availability": True,
    "location": "main_gate"       # approximate zone
}
```

### CampusCoordinatorAgent Beliefs

```python
beliefs = {
    "active_alerts": {},          # zone_id -> alert details
    "assignments": {},            # task_id -> collector_id
    "collector_loads": {},        # collector_id -> task count
    "reassignment_history": []    # log of all reassignments
}
```

### GamificationAgent Beliefs

```python
beliefs = {
    "engagement_threshold": 20,
    "active_today": 0,
    "bonus_active": False,
    "streak_milestones": [7, 30, 100],
    "student_streaks": {}         # username -> streak_days
}
```

---

## 4. Percepts and Actions

### WasteSensorAgent

| Percepts (Inputs) | Actions (Outputs) |
|-------------------|-------------------|
| Pending pickup count per zone (from API) | Send INFORM(zone_alert) to Coordinator |
| Time of last scan per zone | Send INFORM(zone_resolved) to Coordinator |
| Timer tick (every 30s) | Update zone_status beliefs |

### ClassificationAgent

| Percepts (Inputs) | Actions (Outputs) |
|-------------------|-------------------|
| New scan event (username, item, confidence, timestamp) | Approve scan (no action needed) |
| Scan history for student (last 5 minutes) | Send FAILURE(fraud_detected) to Coordinator |
| Confidence score from AI classifier | Log scan validity result |

### CollectorAgent

| Percepts (Inputs) | Actions (Outputs) |
|-------------------|-------------------|
| REQUEST(assign_task) message | Send AGREE to Coordinator |
| Own current task count | Send REFUSE to Coordinator |
| Task completion confirmation from API | Send INFORM(task_complete) to Coordinator |

### GamificationAgent

| Percepts (Inputs) | Actions (Outputs) |
|-------------------|-------------------|
| Daily active user count (from API) | Send INFORM(engagement_drop) to Coordinator |
| Student streak history (from API) | Award badge via API call |
| Timer trigger (daily at 08:00) | Log engagement report |
| Scan event (streak update) | Update student streak belief |

### CampusCoordinatorAgent

| Percepts (Inputs) | Actions (Outputs) |
|-------------------|-------------------|
| INFORM(zone_alert) from SensorAgent | Send REQUEST(assign_task) to CollectorAgent |
| AGREE from CollectorAgent | Record assignment in beliefs |
| REFUSE from CollectorAgent | Try next available CollectorAgent |
| INFORM(task_complete) from CollectorAgent | Update zone status; clear alert |
| FAILURE(fraud_detected) from ClassificationAgent | Freeze account via API; alert admin |
| INFORM(engagement_drop) from GamificationAgent | Activate bonus event via API |

---

# PHASE 5 – Implementation

---

## 1. Prototype

### Core Agent Loop (perceive → decide → act)

Every agent in the system implements the perceive-decide-act cycle using SPADE behaviors:

```python
import spade
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
import json
import requests

API_BASE = "https://plastickonnect.up.railway.app"

# ── WasteSensorAgent ───────────────────────────────────────────────────────────
class WasteSensorAgent(Agent):

    class MonitorZonesBehaviour(PeriodicBehaviour):
        OVERFLOW_THRESHOLD = 10
        CLEAR_THRESHOLD = 3

        async def run(self):
            # PERCEIVE
            try:
                resp = requests.get(f"{API_BASE}/api/pickups?status=pending")
                pickups = resp.json()
            except Exception:
                return  # retry next tick

            # Count per zone
            zone_counts = {}
            for p in pickups:
                z = p.get("zone", "unknown")
                zone_counts[z] = zone_counts.get(z, 0) + 1

            # DECIDE + ACT
            for zone, count in zone_counts.items():
                alerted = self.agent.zone_alerts.get(zone, False)
                if count > self.OVERFLOW_THRESHOLD and not alerted:
                    # Send alert to Coordinator
                    msg = Message(to="coordinator@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = json.dumps({
                        "type": "zone_alert",
                        "zone_id": zone,
                        "pending": count,
                        "severity": "HIGH"
                    })
                    await self.send(msg)
                    self.agent.zone_alerts[zone] = True
                    print(f"[SensorAgent] ALERT sent for zone: {zone} ({count} pending)")

                elif count <= self.CLEAR_THRESHOLD and alerted:
                    # Zone resolved
                    msg = Message(to="coordinator@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = json.dumps({"type": "zone_resolved", "zone_id": zone})
                    await self.send(msg)
                    self.agent.zone_alerts[zone] = False

    async def setup(self):
        self.zone_alerts = {}
        self.add_behaviour(self.MonitorZonesBehaviour(period=30))


# ── CollectorAgent ─────────────────────────────────────────────────────────────
class CollectorAgent(Agent):

    class HandleTaskBehaviour(CyclicBehaviour):
        MAX_TASKS = 3

        async def run(self):
            # PERCEIVE — wait for a message
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            data = json.loads(msg.body)

            # DECIDE
            if data.get("type") == "pickup_assignment":
                if len(self.agent.current_tasks) < self.MAX_TASKS:
                    # ACT — Accept
                    reply = Message(to=str(msg.sender))
                    reply.set_metadata("performative", "agree")
                    reply.body = json.dumps({"task_id": data["pickup_ids"][0]})
                    await self.send(reply)
                    self.agent.current_tasks.extend(data["pickup_ids"])
                    print(f"[CollectorAgent {self.agent.collector_id}] ACCEPTED task for {data['zone_id']}")

                    # Execute pickup
                    for pid in data["pickup_ids"]:
                        requests.post(f"{API_BASE}/api/pickup/{pid}/complete",
                                      json={"collector": self.agent.collector_id})
                    self.agent.current_tasks = [
                        t for t in self.agent.current_tasks
                        if t not in data["pickup_ids"]
                    ]

                    # Report completion
                    done = Message(to=str(msg.sender))
                    done.set_metadata("performative", "inform")
                    done.body = json.dumps({
                        "type": "task_complete",
                        "zone_id": data["zone_id"]
                    })
                    await self.send(done)

                else:
                    # ACT — Refuse
                    reply = Message(to=str(msg.sender))
                    reply.set_metadata("performative", "refuse")
                    reply.body = json.dumps({"reason": "at_capacity"})
                    await self.send(reply)
                    print(f"[CollectorAgent {self.agent.collector_id}] REFUSED — at capacity")

    async def setup(self):
        self.collector_id = self.jid.localpart
        self.current_tasks = []
        self.add_behaviour(self.HandleTaskBehaviour())


# ── CampusCoordinatorAgent ─────────────────────────────────────────────────────
class CampusCoordinatorAgent(Agent):

    class CoordinateBehaviour(CyclicBehaviour):
        COLLECTORS = [
            "collector_1@localhost",
            "collector_2@localhost",
            "collector_3@localhost"
        ]

        async def run(self):
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            data = json.loads(msg.body)
            perf = msg.get_metadata("performative")

            if data.get("type") == "zone_alert":
                print(f"[Coordinator] Zone alert: {data['zone_id']} — assigning collector")
                await self.assign_task(data)

            elif data.get("type") == "task_complete":
                print(f"[Coordinator] Task complete for zone: {data['zone_id']}")

            elif perf == "failure" and data.get("type") == "fraud_detected":
                print(f"[Coordinator] FRAUD: {data['username']} — {data['scan_count']} scans")
                requests.post(f"{API_BASE}/api/admin/flag-user",
                              json={"username": data["username"], "reason": "fraud"})

        async def assign_task(self, alert_data):
            for collector_jid in self.COLLECTORS:
                req = Message(to=collector_jid)
                req.set_metadata("performative", "request")
                req.body = json.dumps({
                    "type": "pickup_assignment",
                    "zone_id": alert_data["zone_id"],
                    "pickup_ids": alert_data.get("pickup_ids", []),
                    "priority": alert_data["severity"]
                })
                await self.send(req)
                reply = await self.receive(timeout=15)
                if reply and reply.get_metadata("performative") == "agree":
                    print(f"[Coordinator] Task assigned to {collector_jid}")
                    return
                print(f"[Coordinator] {collector_jid} refused — trying next")
            print("[Coordinator] WARNING: No collectors available for zone")

    async def setup(self):
        self.add_behaviour(self.CoordinateBehaviour())


# ── Main entry point ───────────────────────────────────────────────────────────
async def main():
    sensor     = WasteSensorAgent("sensor@localhost",     "password")
    collector1 = CollectorAgent("collector_1@localhost",  "password")
    collector2 = CollectorAgent("collector_2@localhost",  "password")
    coordinator = CampusCoordinatorAgent("coordinator@localhost", "password")

    await sensor.start()
    await collector1.start()
    await collector2.start()
    await coordinator.start()

    print("All agents running. Press Ctrl+C to stop.")
    await spade.wait_until_finished(sensor)

if __name__ == "__main__":
    spade.run(main())
```

---

## 2. Report (500–800 words)

### PlasticKonnect Multi-Agent Waste Coordination System

**Platform and Language Justification**

This project is implemented in Python 3.9 using the SPADE (Smart Python Agent
Development Environment) framework. SPADE was chosen because it supports FIPA-ACL
compliant messaging over XMPP, provides native asynchronous behaviour types
(PeriodicBehaviour, CyclicBehaviour, FSMBehaviour), and integrates well with
standard Python HTTP libraries needed to communicate with the PlasticKonnect
REST API. Python was chosen for its readability, strong library support, and
direct compatibility with the existing PlasticKonnect backend (also Python/FastAPI).

**Phase 1 Summary — System Specification**

The domain is campus plastic waste management at the University of Ghana. The
core problem is that collection is inefficient, student engagement is inconsistent,
and the system has no mechanism for autonomous response to changing conditions.
An agent-based approach is appropriate because the environment is dynamic,
decisions are distributed across multiple actors, and continuous autonomous
monitoring is required. Stakeholders are students (scanners), collectors (pickup
agents), and campus administrators.

**Phase 2 Summary — Architectural Design**

Five agent types were identified: WasteSensorAgent, ClassificationAgent,
CollectorAgent (multiple instances), GamificationAgent, and CampusCoordinatorAgent.
Multiple agents were chosen because each concern — sensing, classifying, collecting,
rewarding, coordinating — is genuinely independent and benefits from running
concurrently. The CampusCoordinatorAgent acts as the system's decision hub, receiving
alerts from sensing agents and dispatching instructions to CollectorAgents. This
hub-and-spoke topology was chosen because the Coordinator is the only agent with
complete situational awareness (zone states + collector availability simultaneously).

**Phase 3 Summary — Interaction Design**

Agents communicate exclusively through FIPA-ACL messages using INFORM, REQUEST,
AGREE, REFUSE, and FAILURE performatives. The key interaction protocols are:
(1) zone overflow → assignment flow using INFORM/REQUEST/AGREE/INFORM;
(2) task rejection → reassignment using REFUSE and retry logic;
(3) fraud detection using FAILURE messages.
All messages carry JSON-structured content bodies with typed payloads, allowing
agents to parse and respond without ambiguity.

**Phase 4 Summary — Detailed Design**

Each agent's internals were designed using the BDI model. Beliefs represent what
the agent currently knows (zone states, task lists, streak records). Desires
represent persistent goals (zero unhandled alerts, sustained engagement). Intentions
are concrete executable plans with explicit trigger conditions and failure-handling
paths. The CollectorAgent's alternative plan (refuse → Coordinator retries) and the
ClassificationAgent's fraud detection plan are the most complex demonstrations of
reactive, goal-directed reasoning in the system.

**How the Implementation Maps to the Prometheus Design**

The prototype directly reflects the design: WasteSensorAgent uses PeriodicBehaviour
matching the `monitor_zones` plan. CollectorAgent uses CyclicBehaviour implementing
the `handle_task_assignment` plan exactly as specified. CampusCoordinatorAgent
implements the `assign_pickup_task` plan including the retry-on-refuse logic.
Every FIPA-ACL message type used in Phase 3 interaction diagrams appears in the
implementation as `msg.set_metadata("performative", ...)`. The BDI beliefs from
Phase 4 are represented as agent instance variables (`self.zone_alerts`,
`self.current_tasks`, etc.).

**Challenges and Limitations**

The main challenge is that CollectorAgent location data is not available through the
PlasticKonnect API — collectors are assigned by lowest task count, not proximity,
which is a simplification of real-world routing. A second limitation is that the
XMPP server must be running locally or in Codespaces; if it goes offline, all
agent communication halts. A third limitation is that the GamificationAgent's
engagement check runs once daily — a more sophisticated implementation would use
a sliding window to detect intraday drops. Finally, the fraud detection threshold
(15 scans per 5 minutes) was set conservatively to avoid false positives, but may
miss slower fraudulent patterns.

Despite these limitations, the system demonstrates all core intelligent agent
properties: autonomous perception of a real environment, goal-directed decision
making, reactive behavior on events (zone overflow, fraud, engagement drops),
and genuine multi-agent coordination with negotiation (accept/refuse/reassign).

---

## Setup Guide (README)

```
Prerequisites:
  - Python 3.9+
  - A running XMPP server (Prosody or ejabberd)
  - PlasticKonnect API accessible at API_BASE in settings

Install dependencies:
  pip install spade requests aiohttp

Create agent accounts on XMPP server:
  sensor@localhost / password
  classifier@localhost / password
  collector_1@localhost / password
  collector_2@localhost / password
  collector_3@localhost / password
  coordinator@localhost / password
  gamification@localhost / password

Run:
  python main.py

To run simulation (all 4 scenarios):
  python tests/simulation_runner.py
```
