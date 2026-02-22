# 🚆 Train Management Multi-Agent System — Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                               │
│              (CLI / API / Dashboard)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               TRAIN MANAGEMENT ORCHESTRATOR                      │
│                  (LangGraph State Machine)                        │
│                                                                  │
│  • Sequential pipeline control                                   │
│  • Conditional disaster routing                                  │
│  • Global state management                                       │
│  • Re-prediction after reroute                                   │
└──────┬──────────┬──────────────┬──────────────┬─────────────────┘
       │          │              │              │
       ▼          ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│Scheduling│ │  Time    │ │ Arrival  │ │  Disaster    │
│  Agent   │ │Prediction│ │Monitoring│ │  Recovery    │
│          │ │  Agent   │ │  Agent   │ │  Agent       │
│ Route &  │ │ ETA calc │ │ Real-time│ │ Re-routing & │
│ Platform │ │ Math+LLM │ │ tracking │ │ Recovery     │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## Pipeline Flow

```
User Request
    ↓
┌──────────────────────┐
│ 1. Scheduling Agent  │  Assigns route, platform, stops
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 2. Time Prediction   │  Calculates ETA (distance/speed + halts
│    Agent             │  + weather + congestion adjustments)
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 3. Arrival Monitoring│  Compares predicted vs actual position
│    Agent             │
└──────────┬───────────┘
           ↓
      ┌─── Delay > Threshold? ───┐
      │ YES                      │ NO
      ↓                          ↓
┌──────────────────────┐    ┌────────┐
│ 4. Disaster Recovery │    │  END   │
│    Agent             │    │ (Done) │
└──────────┬───────────┘    └────────┘
           ↓
┌──────────────────────┐
│ Re-Predict (Agent 2) │  Updated ETA after reroute
└──────────┬───────────┘
           ↓
      ┌────────┐
      │  END   │
      └────────┘
```

## Agent Details

### 1. Scheduling Agent (`scheduling_agent.py`)
- **Inputs**: Train ID, source/destination, track & platform availability, maintenance status
- **Outputs**: Assigned route, platform number, departure time, stops & halt durations
- **Constraints**: No track conflicts, no platform clashes, maintenance clearance

### 2. Time Prediction Agent (`time_prediction_agent.py`)
- **Formula**: `(distance/speed) × weather × congestion × track_condition + halt_times`
- **Outputs**: Predicted arrival time, delay probability %, confidence score
- **Factors**: Weather (clear→storm), congestion (low→very_high), track condition (excellent→poor)

### 3. Arrival Monitoring Agent (`arrival_monitoring_agent.py`)
- **Inputs**: Predicted arrival, GPS location, current speed, timestamp
- **Outputs**: Status (On-Time/Delayed/Not Arrived), delay minutes, risk level
- **Trigger**: Flags disaster recovery if delay > 30min threshold

### 4. Disaster Recovery Agent (`disaster_recovery_agent.py`)
- **Triggered by**: Breakdown, track damage, flood, weather, major delay
- **Outputs**: Root cause, alternate route, new schedule, affected trains, recovery ETA
- **Priority**: Safety over speed — never hallucinate reasons

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT                                       │
│  train_id, source, destination, speed, distance, weather, etc.  │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR STATE                               │
│  schedule_result → prediction_result → monitoring_result         │
│                                    → disaster_result (if needed) │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT                                      │
│  Structured JSON with all agent results + route_status           │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/train/schedule` | POST | Schedule a train |
| `/api/train/predict` | POST | Predict arrival time |
| `/api/train/monitor` | POST | Monitor arrival |
| `/api/train/disaster` | POST | Trigger disaster recovery |
| `/api/train/full-flow` | POST | Full 4-agent pipeline |
| `/api/health` | GET | System health check |
| `/api/demo/scenarios` | GET | Available demo scenarios |
