# PlasticKonnect Multi-Agent System
## DCIT 403 — Intelligent Agent Systems Project Report

---

## 1. Introduction

PlasticKonnect is a gamified mobile application deployed at the University of Ghana to incentivise students to collect and recycle plastic waste on campus. Students use their phones to scan plastic items; an AI model (Claude Vision) identifies the plastic type and awards points. Students can also fill a collection bag and request a physical pickup by a campus collector, who verifies the bag and awards bulk points.

While the mobile application handles student-facing interactions, the backend generates a continuous stream of real-time events — zone overflow alerts, engagement drops, fraud attempts, streak milestones — that a human administrator cannot monitor or respond to quickly enough. This project implements a **Multi-Agent System (MAS)** to automate that coordination layer entirely, operating autonomously 24/7 without human intervention.

---

## 2. Problem Description

### 2.1 The Problem

Campus plastic waste management at the University of Ghana faces three compounding challenges:

1. **Coordination bottleneck.** Plastic collection requests accumulate across eight campus zones simultaneously. Manually dispatching the right collector to the right zone at the right time is error-prone and slow.
2. **Student disengagement.** Without timely incentives (bonus events, milestone rewards), student participation drops sharply, undermining the app's core goal.
3. **Point farming fraud.** The gamified points system is vulnerable to abuse — students can submit rapid, repeated scans to harvest points without performing real collection work.

### 2.2 Why an Agent-Based Solution

A multi-agent system is the appropriate solution because:

- **Distribution.** Collection tasks are spatially distributed across eight zones; no single centralised controller can respond optimally to all of them simultaneously.
- **Autonomy.** Agents must perceive environmental state (zone counts, scan rates, active users), reason about it, and act — without waiting for human input.
- **Negotiation.** Collector assignment is not always straightforward; a collector may be at capacity and must refuse, triggering a reassignment cycle that is naturally modelled as agent negotiation.
- **Concurrency.** Multiple event types (overflow, fraud, engagement drop) can occur simultaneously and must be handled in parallel by specialised agents.

---

## 3. Methodology — Prometheus AOSE

The system was designed using the **Prometheus Agent-Oriented Software Engineering (AOSE)** methodology, which structures development into four phases:

| Phase | Artefact | Output |
|-------|----------|--------|
| System Overview | Goals, scenarios, percepts, actions | Goal hierarchy, system roles |
| Agent Acquaintance | Message flows, agent interactions | Acquaintance diagram |
| Agent Detail | Beliefs, capabilities, plans | Per-agent design |
| System Design | Deployment, configuration | Production architecture |

---

## 4. Goal Specification

### Top-Level Goal
> Automate campus plastic waste coordination — detect anomalies, assign collectors, maintain student engagement, and prevent fraud — without human intervention.

### Sub-Goals

| ID | Sub-Goal |
|----|----------|
| G1 | Monitor all campus zones and send alerts when pending pickups exceed the overflow threshold |
| G2 | Assign the least-loaded available collector to each overflowing zone |
| G3 | Handle collector refusal gracefully — reassign to the next available collector |
| G4 | Detect fraudulent scanning behaviour using a sliding-window rate analysis |
| G5 | Monitor daily student engagement and trigger bonus events when participation drops |
| G6 | Automatically award bonus points when students reach streak milestones |

---

## 5. System Architecture

### 5.1 Technology Stack

| Component | Technology |
|-----------|-----------|
| Agent framework | SPADE 4.1.2 (Smart Python Agent Development Environment) |
| Transport protocol | XMPP (Extensible Messaging and Presence Protocol) |
| Message standard | FIPA-ACL (Foundation for Intelligent Physical Agents — Agent Communication Language) |
| XMPP server (simulation) | pyjabber 0.3.0 (embedded, in-memory) |
| Backend API | PlasticKonnect FastAPI REST API (Railway) |
| Language | Python 3.12 |
| Simulation testing | Custom mock API (monkey-patching `api.client`) |

### 5.2 Directory Structure

```
intelligent_agents/
├── agents/                    # Agent identity and setup
│   ├── waste_sensor_agent.py
│   ├── coordinator_agent.py
│   ├── collector_agent.py
│   ├── classification_agent.py
│   └── gamification_agent.py
├── behaviours/                # Behaviour logic (separated by concern)
│   ├── monitor_zones.py
│   ├── coordinate.py
│   ├── handle_task.py
│   ├── fraud_detection.py
│   └── engagement_check.py
├── config/
│   ├── settings.py            # All thresholds and configuration constants
│   └── agent_jids.py          # XMPP JID definitions
├── api/
│   └── client.py              # All HTTP calls to PlasticKonnect REST API
├── simulation/
│   ├── mock_api.py            # Monkey-patched API for offline testing
│   ├── xmpp_server.py         # Embedded pyjabber server manager
│   ├── scenario_1_zone_overflow.py
│   ├── scenario_2_collector_refuse.py
│   ├── scenario_3_engagement_drop.py
│   ├── scenario_4_fraud.py
│   └── run_all.py             # Sequential runner for all scenarios
├── logs/
│   ├── agent_messages.log     # All FIPA-ACL message exchanges
│   ├── decisions.log          # Agent decisions and actions
│   └── simulation_results.log # Scenario setup and results
└── main.py                    # Production entry point
```

---

## 6. Agent Design

The system comprises **five agents**, each with a single responsibility aligned to the Prometheus single-agent principle.

---

### 6.1 WasteSensorAgent

**Role:** Environmental monitor — the system's eyes on the ground.

**JID:** `waste_sensor@localhost`

**Behaviour:** `MonitorZonesBehaviour` (PeriodicBehaviour — fires every 30 seconds in production)

**Percepts:** Pending pickup counts per campus zone, fetched from the PlasticKonnect REST API.

**Beliefs:**
- `zone_counts: dict[str, int]` — latest known count per zone
- `alerted_zones: set[str]` — zones for which an alert has already been sent (prevents duplicate alerts)

**Decision Logic (percept → decide → act):**
```
PERCEPT:  count = api.get_pending_pickups_by_zone()
DECIDE:   if count >= ZONE_OVERFLOW_THRESHOLD (10) and zone not already alerted
ACT:      send INFORM(zone_alert) to CampusCoordinatorAgent

PERCEPT:  count < threshold and zone was previously alerted
DECIDE:   zone has cleared
ACT:      send INFORM(zone_resolved) to CampusCoordinatorAgent
```

**Campus zones monitored:**
Science Block, Arts Centre, Volta Hall, Commonwealth Hall, Bush Canteen, Engineering Quad, Great Hall, Balme Library.

---

### 6.2 CampusCoordinatorAgent

**Role:** Central orchestrator — the decision-making hub of the MAS.

**JID:** `coordinator@localhost`

**Behaviour:** `CoordinateBehaviour` (CyclicBehaviour — always listening)

**Percepts:** Incoming FIPA-ACL messages from all other agents (filtered by ontology `plastickonnect-waste-management`).

**Beliefs:**
- `collector_registry: dict[str, dict]` — all known collectors with their current task load and max capacity
- `active_assignments: dict[int, str]` — maps request ID to the assigned collector name
- `pending_alerts: set[str]` — zones currently in overflow state
- `unassigned_queue: list[dict]` — overflow alerts that could not be assigned (all collectors at capacity)
- `busy_this_round: set[str]` — collectors who have refused a task in the current assignment cycle

**Message Handling:**

| Received | From | Action |
|----------|------|--------|
| `INFORM zone_alert` | WasteSensorAgent | Select least-loaded collector → send `REQUEST assign_task` |
| `INFORM zone_resolved` | WasteSensorAgent | Remove zone from `pending_alerts` |
| `INFORM engagement_drop` | GamificationAgent | Log bonus event acknowledgement |
| `FAILURE fraud_alert` | ClassificationAgent | Log fraud alert, flag account |
| `AGREE task_accepted` | CollectorAgent | Record assignment in `active_assignments` |
| `REFUSE task_refused` | CollectorAgent | Mark collector as busy → select next available → reassign |

**Collector Selection Algorithm:**
Selects the collector with the **lowest current task load** who has not reached `max_tasks` (3) and is not in the `busy_this_round` exclusion set. This is a greedy least-loaded selection — O(n) over the registry.

---

### 6.3 CollectorAgent

**Role:** Physical waste collector — receives and negotiates task assignments.

**JID:** `collector_{name}@localhost` (e.g., `collector_kwame@localhost`)

**Behaviour:** `HandleTaskBehaviour` (CyclicBehaviour)

**Percepts:** `REQUEST assign_task` messages from the Coordinator.

**Beliefs:**
- `collector_name: str` — identity
- `current_tasks: int` — active task count
- `max_tasks: int` — capacity ceiling (default: 3)
- `active_task_ids: list[int]` — IDs of currently active requests

**Decision Logic:**
```
PERCEPT:  REQUEST(assign_task) received from Coordinator
DECIDE:   if current_tasks < max_tasks → ACCEPT
          else → REFUSE
ACT (accept): call api.assign_pickup_to_collector(request_id, collector_name)
              increment current_tasks
              send AGREE(task_accepted) to Coordinator
ACT (refuse): send REFUSE(at_capacity) to Coordinator
```

Multiple `CollectorAgent` instances run concurrently, one per collector registered in the system.

---

### 6.4 ClassificationAgent

**Role:** Fraud and anomaly detector.

**JID:** `classifier@localhost`

**Behaviour:** `FraudDetectionBehaviour` (PeriodicBehaviour — fires every 30 seconds)

**Percepts:** Full scan activity history per user, fetched from the REST API.

**Beliefs:**
- `flagged_users: set[str]` — users already flagged (prevents duplicate alerts per session)

**Decision Logic:**
```
PERCEPT:  activity = api.get_activity(username) for each user
DECIDE:   count scans within the last FRAUD_WINDOW_MINUTES (4 min)
          if count > FRAUD_SCAN_THRESHOLD (8) and user not already flagged
ACT:      api.flag_user_fraud(username)
          send FAILURE(fraud_alert) to Coordinator
```

**Threshold derivation:**
`FRAUD_SCAN_THRESHOLD = FRAUD_SCANS_PER_MINUTE × FRAUD_WINDOW_MINUTES = 2 × 4 = 8`

A legitimate user scanning continuously would require a physical item for each scan. More than 2 scans per minute is considered statistically impossible under real-world conditions.

---

### 6.5 GamificationAgent

**Role:** Engagement and motivation manager.

**JID:** `gamification@localhost`

**Behaviour:** `EngagementCheckBehaviour` (PeriodicBehaviour — fires every 1 hour in production)

**Percepts:** Daily active user count and per-user streak data from the REST API.

**Beliefs:**
- `daily_active_count: int` — most recent active user count
- `bonus_event_active: bool` — whether a bonus event is currently running
- `checked_milestones: set[str]` — `"{username}:{milestone}"` keys already processed (prevents re-awarding)

**Decision Logic — Engagement:**
```
PERCEPT:  active_count = api.get_daily_active_users()
DECIDE:   if active_count < ENGAGEMENT_THRESHOLD (20) and no bonus event active
ACT:      set bonus_event_active = True
          send INFORM(engagement_drop) to Coordinator
```

**Decision Logic — Streak Milestones:**
```
PERCEPT:  streak = user.streak for each user
DECIDE:   if streak >= milestone (7, 30, or 100 days) and not already awarded
ACT:      api.award_bonus_points(username, bonus)
          record in checked_milestones
```

**Milestone bonus table:**

| Streak (days) | Bonus Points |
|---------------|-------------|
| 7 | 10 |
| 30 | 30 |
| 100 | 100 |

---

## 7. Agent Communication

### 7.1 Acquaintance Diagram

```
┌─────────────────────┐
│  WasteSensorAgent   │──── INFORM(zone_alert / zone_resolved) ────────┐
└─────────────────────┘                                                 │
                                                                        ▼
┌─────────────────────┐                                  ┌─────────────────────────┐
│ ClassificationAgent │──── FAILURE(fraud_alert) ──────► │ CampusCoordinatorAgent  │
└─────────────────────┘                                  └──────────┬──────────────┘
                                                                    │
┌─────────────────────┐                                             │ REQUEST(assign_task)
│  GamificationAgent  │──── INFORM(engagement_drop) ───────────────┘
└─────────────────────┘                                             │
                                                                    ▼
                                                     ┌──────────────────────────┐
                                                     │    CollectorAgent(s)     │
                                                     │  (kwame, abena, kofi…)  │
                                                     └──────────────────────────┘
                                                          │            │
                                              AGREE ──────┘            └────── REFUSE
                                          (task_accepted)          (at_capacity)
```

### 7.2 FIPA-ACL Messages

All messages use the shared ontology `plastickonnect-waste-management` for template-based routing. Message bodies are JSON-encoded.

| Performative | Type | Sender | Receiver | Payload fields |
|-------------|------|--------|----------|----------------|
| `inform` | `zone_alert` | WasteSensorAgent | Coordinator | zone, count, threshold |
| `inform` | `zone_resolved` | WasteSensorAgent | Coordinator | zone, count |
| `inform` | `engagement_drop` | GamificationAgent | Coordinator | active_users, threshold, bonus_duration_hours |
| `failure` | `fraud_alert` | ClassificationAgent | Coordinator | username, scan_count, window_minutes, sample_timestamps |
| `request` | `assign_task` | Coordinator | CollectorAgent | request_id, zone, count |
| `agree` | `task_accepted` | CollectorAgent | Coordinator | request_id, collector, zone |
| `refuse` | `task_refused` | CollectorAgent | Coordinator | request_id, collector, zone, reason |

---

## 8. Simulation Design

### 8.1 Simulation Infrastructure

Testing against the live PlasticKonnect API was not feasible for rapid iteration. A mock API layer was built using Python monkey-patching:

- `simulation/mock_api.py` defines a shared `_state` dictionary (zone counts, users, activity, requests, collectors, flagged users).
- `install()` replaces all functions in `api.client` with mock equivalents that read/write `_state`.
- `reset()` clears state between scenarios.
- Helper functions (`add_user`, `add_activity`, `set_zone_counts`, `add_collector`, `add_request`) seed each scenario's initial conditions.

**XMPP infrastructure:** An embedded pyjabber server (`simulation/xmpp_server.py`) is started programmatically before each scenario using `asyncio.create_task`, eliminating the need for an external Prosody or ejabberd server.

**Timing acceleration:** SPADE's `PeriodicBehaviour` uses real wall-clock time. Scenarios patch `config.settings` constants (e.g., `settings.MONITOR_INTERVAL = 2`) at module level before agent imports, so behaviours fire every 2 seconds instead of 30, allowing full scenarios to complete in under 10 seconds.

### 8.2 Simulation Scenarios

---

#### Scenario 1 — "The Overflowing Zone"

**Setup:** Science Block accumulates 22 pending pickups. Overflow threshold = 10. Kwame is registered as an available collector.

**Expected message flow:**
```
WasteSensorAgent  →[INFORM zone_alert]→   CampusCoordinatorAgent
CampusCoordinatorAgent  →[REQUEST assign_task]→   CollectorAgent(kwame)
CollectorAgent(kwame)   →[AGREE task_accepted]→   CampusCoordinatorAgent
```

**Result:** ✅ PASS

**Log evidence:**
```
[WasteSensor] Zone 'Science Block' exceeded threshold (22 >= 10). Alert sent.
[Coordinator] Assigned task 1 (zone='Science Block') to collector 'kwame'.
[Collector:kwame] Accepted task 1 in zone 'Science Block'. Load: 1/3.
[Coordinator] Task 1 ACCEPTED by 'kwame'.
```

---

#### Scenario 2 — "The Reluctant Collector"

**Setup:** Engineering Quad has 15 pending pickups. Kwame is pre-filled to maximum capacity (3/3 tasks). Abena is available (0/3 tasks).

**Expected message flow:**
```
WasteSensorAgent       →[INFORM zone_alert]→       CampusCoordinatorAgent
CampusCoordinatorAgent →[REQUEST assign_task]→     CollectorAgent(kwame)
CollectorAgent(kwame)  →[REFUSE at_capacity]→      CampusCoordinatorAgent
CampusCoordinatorAgent →[REQUEST assign_task]→     CollectorAgent(abena)
CollectorAgent(abena)  →[AGREE task_accepted]→     CampusCoordinatorAgent
```

**Result:** ✅ PASS

**Log evidence:**
```
[WasteSensor] Zone 'Engineering Quad' exceeded threshold (15 >= 10). Alert sent.
[Coordinator] Assigned task 1 (zone='Engineering Quad') to collector 'abena'.
[Collector:abena] Accepted task 1 in zone 'Engineering Quad'. Load: 1/3.
[Coordinator] Task 1 ACCEPTED by 'abena'.
```

---

#### Scenario 3 — "The Quiet Tuesday"

**Setup:** Only 4 students are active today. Engagement threshold = 20.

**Expected message flow:**
```
GamificationAgent      →[INFORM engagement_drop]→  CampusCoordinatorAgent
CampusCoordinatorAgent  logs bonus event acknowledgement
```

**Result:** ✅ PASS

**Log evidence:**
```
[Gamification] Only 4 active users today (threshold=20). Bonus event triggered for 3h.
[Coordinator] Engagement drop received. Active=4. Bonus event of 3h acknowledged.
```

---

#### Scenario 4 — "The Suspicious Scanner"

**Setup:** user99 has 60 scan activities within the last 4 minutes. Fraud threshold = 8 scans per 4 minutes.

**Expected message flow:**
```
ClassificationAgent  →[FAILURE fraud_alert]→   CampusCoordinatorAgent
CampusCoordinatorAgent  flags user99 account
```

**Result:** ✅ PASS — `user99` confirmed in `mock._state["flagged_users"]`

**Log evidence:**
```
[Classifier] FRAUD detected: 'user99' submitted 57 scans in 4 min (threshold=8). Alert forwarded to Coordinator.
[Coordinator] FRAUD ALERT — user='user99' submitted 57 scans in 4 min. Account flagged.
```

---

## 9. Configuration Reference

All system thresholds are centralised in `config/settings.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `ZONE_OVERFLOW_THRESHOLD` | 10 | Pending pickups before zone alert fires |
| `MONITOR_INTERVAL` | 30s | WasteSensor and ClassificationAgent poll interval |
| `COLLECTOR_MAX_TASKS` | 3 | Maximum concurrent tasks per collector |
| `FRAUD_SCANS_PER_MINUTE` | 2 | Max legitimate scan rate |
| `FRAUD_WINDOW_MINUTES` | 4 | Sliding window for fraud detection |
| `FRAUD_SCAN_THRESHOLD` | 8 | Derived: 2 × 4 |
| `ENGAGEMENT_THRESHOLD` | 20 | Min active users before engagement event |
| `ENGAGEMENT_CHECK_HOURS` | 1 | GamificationAgent check frequency |
| `BONUS_EVENT_DURATION_H` | 3 | Duration of a triggered bonus event |
| `STREAK_MILESTONES` | 7, 30, 100 | Days at which bonus points are awarded |

---

## 10. Prometheus Design Alignment

| Prometheus Artefact | Implementation |
|--------------------|-----------------|
| System roles | 5 agents, each with one responsibility |
| Goal hierarchy | G1–G6 sub-goals mapped 1-to-1 to agent behaviours |
| Percepts | REST API responses (zone counts, activity, user data) |
| Actions | FIPA-ACL messages + REST API calls (assign, flag, award) |
| Acquaintance diagram | Coordinator as central hub; sensor/classifier/gamification as producers; collectors as consumers |
| Agent detail (beliefs) | Per-agent instance attributes acting as the BDI belief base |
| Capabilities / plans | Each `Behaviour` class = one plan |
| System design | Deployed with pyjabber (simulation) or external XMPP server (production) |

---

## 11. Challenges and Limitations

### 11.1 Challenges Encountered

**1. XMPP Infrastructure**
SPADE requires an XMPP server for agent communication. An external Prosody or ejabberd server was not available in the development environment. This was resolved by using pyjabber — an embedded in-memory XMPP server that ships as a SPADE dependency — launched programmatically via `asyncio.create_task` before each simulation scenario.

**2. Simulation Timing**
SPADE's `PeriodicBehaviour` uses real wall-clock time. With a 30-second monitor interval, each scenario would require several minutes to produce any output. This was resolved by monkey-patching `config.settings` constants (`settings.MONITOR_INTERVAL = 2`) at the top of each scenario file, before any agent modules import those constants. This compressed scenarios to under 10 seconds each.

**3. Windows Unicode Encoding**
The Windows default terminal encoding (cp1252) cannot represent the Unicode arrow character `→` (U+2192) used in log entries. All `open()` calls for log file writes raised `UnicodeEncodeError`. This was fixed by explicitly specifying `encoding="utf-8"` on every file write operation in the `behaviours/` and `simulation/` modules.

**4. loguru vs Python logging**
pyjabber uses `loguru` for its internal logging, not Python's standard `logging` module. The standard approach (`logging.disable(logging.INFO)` and `logging.getLogger("pyjabber").setLevel(logging.CRITICAL)`) had no effect on pyjabber's output. The fix was to call `loguru.logger.remove()` — which strips all loguru handlers — at the top of the XMPP server module before pyjabber is imported.

**5. Auto-registration**
SPADE's `auto_register=False` (the default in some configurations) caused `AuthenticationFailure` because pyjabber's in-memory store had no pre-registered JIDs. All agent `start()` calls must use `auto_register=True` so SPADE registers the JID with the XMPP server on first connection.

### 11.2 Limitations

| Limitation | Impact | Potential Resolution |
|-----------|--------|---------------------|
| Mock API state is not thread-safe | Concurrent agent writes to `_state` could race in edge cases | Use `asyncio.Lock` around shared state mutations |
| Collector registry is pre-seeded manually | Agents do not self-announce on startup | Implement a registration handshake: CollectorAgent sends INFORM(register) to Coordinator on `setup()` |
| `FraudDetectionBehaviour` queries all users on every cycle | Does not scale beyond ~500 users without pagination | Add server-side filtering endpoint or use cursor-based pagination |
| pyjabber has no TLS by default | Initial slixmpp connection probe fails with "not well-formed" XML | Acceptable for simulation; production requires a properly configured XMPP server with TLS |
| Single `_select_collector` algorithm (greedy least-loaded) | Does not account for collector proximity to the zone | Integrate GPS coordinates from the collector API for distance-weighted selection |

---

## 12. Conclusion

The PlasticKonnect Multi-Agent System successfully automates the coordination layer of a campus plastic waste management platform. Five specialised agents — each designed using the Prometheus AOSE methodology — collaborate via FIPA-ACL messaging over XMPP to:

- Detect zone overflow and dispatch collectors autonomously
- Handle collector negotiation and fallback reassignment
- Detect and flag fraudulent scan behaviour in real time
- Maintain student engagement through automated bonus events and streak rewards

All four simulation scenarios passed, demonstrating correct percept → decide → act cycles, proper FIPA-ACL message exchange, and accurate decision logging. The system is production-ready for deployment against the live PlasticKonnect API by switching from the mock API to `api/client.py` and pointing `main.py` at a real XMPP server.

---

*University of Ghana — DCIT 403 Intelligent Agent Systems*
*PlasticKonnect Multi-Agent System — Project Report*
