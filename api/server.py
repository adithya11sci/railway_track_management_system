"""
FastAPI Server for Train Management Multi-Agent System
Provides REST API endpoints for the 4-agent train management pipeline
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# Lazy imports
train_orchestrator_module = None

def lazy_import_train_orchestrator():
    global train_orchestrator_module
    if train_orchestrator_module is None:
        from orchestrator import TrainManagementOrchestrator
        train_orchestrator_module = TrainManagementOrchestrator
    return train_orchestrator_module

app = FastAPI(
    title="Train Management Multi-Agent System API",
    description="4-Agent train management system: Scheduling, Time Prediction, Arrival Monitoring, Disaster Recovery",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
train_orchestrator: Optional[Any] = None
active_connections: List[WebSocket] = []
scheduled_trains: Dict[str, Any] = {}  # train_id -> full pipeline result
pending_approvals: Dict[str, Any] = {}  # train_id -> { disaster_data, config, partial_result }

# ── Pydantic Models ──

class ResponseModel(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class TrainScheduleRequest(BaseModel):
    train_id: str
    source: str
    destination: str
    departure_time: Optional[str] = "08:00"

class TrainPredictRequest(BaseModel):
    train_id: str
    speed_kmh: Optional[float] = 80.0
    distance_km: Optional[float] = 500.0
    stops: Optional[int] = 4
    halt_duration_minutes: Optional[float] = 5.0
    track_condition: Optional[str] = "good"
    weather: Optional[str] = "clear"
    congestion: Optional[str] = "low"
    departure_time: Optional[str] = "08:00"

class TrainMonitorRequest(BaseModel):
    train_id: str
    predicted_arrival_time: str
    current_speed_kmh: Optional[float] = 75.0
    remaining_distance_km: Optional[float] = None

class TrainDisasterRequest(BaseModel):
    train_id: str
    failure_type: str = "unknown"
    current_location: Optional[str] = None
    available_alternate_tracks: Optional[List[str]] = None

class TrainFullFlowRequest(BaseModel):
    train_id: str
    source: str
    destination: str
    departure_time: Optional[str] = "08:00"
    speed_kmh: Optional[float] = 80.0
    distance_km: Optional[float] = 500.0
    stops: Optional[int] = 4
    weather: Optional[str] = "clear"
    congestion: Optional[str] = "low"
    current_speed_kmh: Optional[float] = 75.0
    remaining_distance_km: Optional[float] = None
    failure_type: Optional[str] = None
    train_type: Optional[str] = "Express"

class TrainBatchFlowRequest(BaseModel):
    trains: List[TrainFullFlowRequest]

class ApproveDisasterRequest(BaseModel):
    train_id: str
    option_id: int

class TrainDelayRequest(BaseModel):
    train_number: str
    delay_minutes: int
    current_location: str
    affected_passengers: Optional[int] = None

class PassengerQueryRequest(BaseModel):
    query: str
    passenger_id: Optional[str] = None

class CrowdPredictionRequest(BaseModel):
    train_number: str
    route: str
    time: Optional[str] = None

class SendAlertRequest(BaseModel):
    message: str
    recipients: List[str]
    channels: List[str]

class OrchestrateRequest(BaseModel):
    request: str
    context: Optional[dict] = {}

# ── Lifecycle ──

async def initialize_components():
    global train_orchestrator
    try:
        print("🚆 Loading Train Management orchestrator...")
        TMO = lazy_import_train_orchestrator()
        if TMO:
            train_orchestrator = TMO()
            print("✅ Train Management Orchestrator initialized")
    except Exception as e:
        print(f"⚠️  Initialization error: {e}")

@app.on_event("startup")
async def startup_event():
    print("🚆 Starting Train Management System API...")
    print("✅ API Server ready on http://localhost:8000")
    asyncio.create_task(initialize_components())

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Shutting down...")
    for conn in active_connections:
        await conn.close()

# ── Health ──

@app.get("/")
async def root():
    """Serve dashboard"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "service": "Train Management Multi-Agent System",
        "version": "2.0.0",
        "dashboard": "Frontend not found. Place index.html in /frontend/",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "orchestrator": train_orchestrator is not None,
        "agents": {
            "scheduling": True,
            "time_prediction": True,
            "arrival_monitoring": True,
            "disaster_recovery": True,
        },
        "timestamp": datetime.now().isoformat()
    }
@app.get("/api/agents/status")
async def get_agents_status():
    return {
        "operations": {"status": "active", "tasks_handled": 15},
        "passenger": {"status": "active", "tasks_handled": 42},
        "crowd": {"status": "active", "tasks_handled": 8},
        "alert": {"status": "active", "tasks_handled": 24}
    }
# ── Train Management Endpoints ──

@app.post("/api/train/schedule", response_model=ResponseModel)
async def schedule_train(req: TrainScheduleRequest):
    """Schedule a train route."""
    try:
        from agents.scheduling_agent import SchedulingAgent
        agent = SchedulingAgent()
        result = agent.schedule_train(
            train_id=req.train_id, source_station=req.source,
            destination_station=req.destination, departure_time=req.departure_time,
        )
        return ResponseModel(success=True, data=result, timestamp=datetime.now().isoformat())
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/predict", response_model=ResponseModel)
async def predict_arrival(req: TrainPredictRequest):
    """Predict train arrival time."""
    try:
        from agents.time_prediction_agent import TimePredictionAgent
        agent = TimePredictionAgent()
        result = agent.predict_arrival(
            train_id=req.train_id, speed_kmh=req.speed_kmh,
            distance_km=req.distance_km, stops=req.stops,
            halt_duration_minutes=req.halt_duration_minutes,
            track_condition=req.track_condition, weather=req.weather,
            congestion=req.congestion, departure_time=req.departure_time,
        )
        return ResponseModel(success=True, data=result, timestamp=datetime.now().isoformat())
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/monitor", response_model=ResponseModel)
async def monitor_train(req: TrainMonitorRequest):
    """Monitor train arrival status."""
    try:
        from agents.arrival_monitoring_agent import ArrivalMonitoringAgent
        agent = ArrivalMonitoringAgent()
        result = agent.monitor_arrival(
            train_id=req.train_id,
            predicted_arrival_time=req.predicted_arrival_time,
            current_speed_kmh=req.current_speed_kmh,
            remaining_distance_km=req.remaining_distance_km,
        )
        return ResponseModel(success=True, data=result, timestamp=datetime.now().isoformat())
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/disaster", response_model=ResponseModel)
async def handle_disaster(req: TrainDisasterRequest):
    """Trigger disaster recovery."""
    try:
        from agents.disaster_recovery_agent import DisasterRecoveryAgent
        agent = DisasterRecoveryAgent()
        result = agent.handle_disaster(
            train_id=req.train_id, failure_type=req.failure_type,
            current_location=req.current_location,
            available_alternate_tracks=req.available_alternate_tracks,
        )
        return ResponseModel(success=True, data=result, timestamp=datetime.now().isoformat())
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/full-flow", response_model=ResponseModel)
async def train_full_flow(req: TrainFullFlowRequest):
    """Run the full 4-agent train management pipeline."""
    try:
        if not train_orchestrator:
            raise HTTPException(status_code=503, detail="Train orchestrator not initialized")
        request_dict = req.model_dump(exclude_none=True)
        result = train_orchestrator.run(request_dict)
        result["train_type"] = req.train_type or "Express"
        scheduled_trains[req.train_id] = result
        return ResponseModel(success=True, data=result, timestamp=datetime.now().isoformat())
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/batch-flow", response_model=ResponseModel)
async def train_batch_flow(req: TrainBatchFlowRequest):
    """Run the full pipeline for multiple trains. Disaster trains pause for approval."""
    try:
        if not train_orchestrator:
            raise HTTPException(status_code=503, detail="Train orchestrator not initialized")
        results = {}
        pending_list = []
        for train_req in req.trains:
            request_dict = train_req.model_dump(exclude_none=True)
            result = train_orchestrator.run(request_dict)
            result["train_type"] = train_req.train_type or "Express"
            scheduled_trains[train_req.train_id] = result
            results[train_req.train_id] = result

            # If disaster was triggered, store for admin approval
            if result.get("disaster_triggered"):
                dr = result.get("results", {}).get("disaster_recovery", {})
                pending_approvals[train_req.train_id] = {
                    "train_id": train_req.train_id,
                    "config": request_dict,
                    "disaster_data": dr,
                    "options": dr.get("options_presented", []),
                    "recommended_option": dr.get("recommended_option"),
                    "root_cause": dr.get("root_cause", {}),
                    "safety_notes": dr.get("safety_notes", ""),
                    "created_at": datetime.now().isoformat(),
                }
                pending_list.append(train_req.train_id)
                # Broadcast via WebSocket
                await broadcast_ws({
                    "type": "disaster_alert",
                    "train_id": train_req.train_id,
                    "root_cause": dr.get("root_cause", {}),
                    "options_count": len(dr.get("options_presented", [])),
                    "timestamp": datetime.now().isoformat(),
                })

        return ResponseModel(
            success=True,
            data={
                "trains": results,
                "count": len(results),
                "pending_approvals": pending_list,
            },
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.get("/api/trains", response_model=ResponseModel)
async def get_all_trains():
    """Get all currently scheduled trains."""
    return ResponseModel(
        success=True,
        data={"trains": scheduled_trains, "count": len(scheduled_trains)},
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/train/pending-approvals", response_model=ResponseModel)
async def get_pending_approvals():
    """Get all disaster events awaiting admin approval."""
    return ResponseModel(
        success=True,
        data={"pending": pending_approvals, "count": len(pending_approvals)},
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/train/approve-disaster", response_model=ResponseModel)
async def approve_disaster(req: ApproveDisasterRequest):
    """Admin approves a reroute option for a disaster train."""
    try:
        pa = pending_approvals.get(req.train_id)
        if not pa:
            return ResponseModel(success=False, error=f"No pending approval for train {req.train_id}", timestamp=datetime.now().isoformat())

        # Apply the chosen option
        from agents.disaster_recovery_agent import DisasterRecoveryAgent
        from agents.time_prediction_agent import TimePredictionAgent
        dr_agent = DisasterRecoveryAgent()
        pred_agent = TimePredictionAgent()

        # Rebuild disaster result for apply
        disaster_result = {
            "options": pa["options"],
            "recommended_option": pa["recommended_option"],
            "root_cause": pa["root_cause"],
            "safety_notes": pa["safety_notes"],
        }
        updated = dr_agent.apply_approved_option(disaster_result, req.option_id)

        # Re-predict with new route
        config = pa["config"]
        new_sched = updated.get("new_schedule", {})
        extra_km = updated.get("alternate_route", {}).get("estimated_detour_km", 0)
        distance = config.get("distance_km", 500.0) + extra_km
        re_pred = pred_agent.predict_arrival(
            train_id=req.train_id,
            speed_kmh=config.get("speed_kmh", 60.0),
            distance_km=distance,
            stops=config.get("stops", 3) + 2,
            halt_duration_minutes=config.get("halt_duration_minutes", 5.0),
            track_condition=config.get("track_condition", "fair"),
            weather=config.get("weather", "clear"),
            congestion="moderate",
            departure_time=new_sched.get("new_departure_time", "08:00"),
        )
        re_pred["is_re_prediction"] = True

        # Build affected trains cascade info
        affected_trains = updated.get("affected_trains", [])
        cascade_updates = []
        for at in affected_trains:
            at_id = at.get("train_id", "unknown")
            if at_id in scheduled_trains:
                # Update the affected train's monitoring status
                st = scheduled_trains[at_id]
                if "results" in st and "monitoring" in st["results"]:
                    st["results"]["monitoring"]["delay_minutes"] = (
                        st["results"]["monitoring"].get("delay_minutes", 0) + at.get("delay_minutes", 0)
                    )
                    st["results"]["monitoring"]["status"] = "Delayed"
                    st["results"]["monitoring"]["risk_level"] = "Medium"
                    st["results"]["monitoring"]["reroute_cascade"] = True
                    st["results"]["monitoring"]["cascade_source"] = req.train_id
            cascade_updates.append({
                "train_id": at_id,
                "impact": at.get("impact", "delayed"),
                "delay_minutes": at.get("delay_minutes", 0),
                "passengers_affected": at.get("passengers_affected", 0),
            })

        # Update main train result
        if req.train_id in scheduled_trains:
            scheduled_trains[req.train_id]["results"]["time_prediction"] = re_pred
            scheduled_trains[req.train_id]["results"]["disaster_recovery"]["approval_status"] = "approved"
            scheduled_trains[req.train_id]["results"]["disaster_recovery"]["approved_option"] = updated.get("approved_option", {})
            scheduled_trains[req.train_id]["results"]["disaster_recovery"]["approved_at"] = datetime.now().isoformat()
            scheduled_trains[req.train_id]["route_status"] = "rerouted"

        # Remove from pending
        del pending_approvals[req.train_id]

        # Broadcast the approval
        await broadcast_ws({
            "type": "disaster_approved",
            "train_id": req.train_id,
            "option_id": req.option_id,
            "cascade_updates": cascade_updates,
            "timestamp": datetime.now().isoformat(),
        })

        return ResponseModel(
            success=True,
            data={
                "train_id": req.train_id,
                "approved_option": updated.get("approved_option", {}),
                "re_prediction": re_pred,
                "cascade_updates": cascade_updates,
                "approval_type": "manual",
                "updated_train": scheduled_trains.get(req.train_id),
            },
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        return ResponseModel(success=False, error=str(e), timestamp=datetime.now().isoformat())

@app.post("/api/train/auto-approve-disaster", response_model=ResponseModel)
async def auto_approve_disaster(req: ApproveDisasterRequest):
    """System auto-approves the recommended option after admin timeout."""
    # Same logic as manual approve, just tagged as auto
    result = await approve_disaster(req)
    if result.data:
        result.data["approval_type"] = "auto"
    return result

# ── WebSocket ──

async def broadcast_ws(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    for conn in active_connections:
        try:
            await conn.send_json(message)
        except Exception:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# ── Demo Scenarios ──

@app.get("/api/demo/scenarios")
async def get_demo_scenarios():
    return {
        "scenarios": [
            {
                "id": "normal_flow",
                "name": "Normal On-Time Flow",
                "description": "Schedule → Predict → Monitor (on-time)",
                "example": {"train_id": "12627", "source": "Bangalore", "destination": "New Delhi"}
            },
            {
                "id": "delay_flow",
                "name": "Delay → Disaster Recovery",
                "description": "Schedule → Predict → Monitor (delayed) → Disaster → Re-predict",
                "example": {"train_id": "12650", "source": "Yesvantpur", "destination": "New Delhi", "weather": "heavy_rain"}
            },
            {
                "id": "disaster_flow",
                "name": "Critical Track Damage",
                "description": "Full disaster recovery with re-routing",
                "example": {"train_id": "22691", "source": "Bangalore", "destination": "Chennai", "failure_type": "track_damage"}
            },
        ]
    }

@app.post("/api/train-delay")
async def handle_train_delay(req: TrainDelayRequest):
    """Integrates with orchestrator to provide intelligent response for train delays"""
    try:
        if not train_orchestrator:
            raise HTTPException(status_code=503, detail="Train orchestrator not initialized")
            
        # Try to find train from the real dataset
        import pandas as pd
        dataset_path = 'chennai_central_real_dataset.csv'
        train_info = {}
        try:
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                df_train = df[df['train_id'].astype(str) == str(req.train_number)]
                if not df_train.empty:
                    row = df_train.iloc[0].fillna("").to_dict()
                    train_info = {
                        "source": row.get("source_station", req.current_location),
                        "destination": row.get("destination_station", "Unknown Destination"),
                        "scheduled_departure": row.get("scheduled_departure", "08:00"),
                        "train_name": row.get("train_name", ""),
                        "platform": row.get("platform", "")
                    }
        except Exception as e:
            print(f"Error reading dataset: {e}")

        # Build a compatible request for the orchestrator
        orchestrator_req = {
            "train_id": req.train_number,
            "train_name": train_info.get("train_name", f"Train {req.train_number}"),
            "source": train_info.get("source", req.current_location),
            "destination": train_info.get("destination", "Unknown Destination"),
            "departure_time": train_info.get("scheduled_departure", "08:00"),
            "platform_availability": {train_info.get("source", req.current_location): [train_info.get("platform", "1")]} if train_info.get("platform") else None,
            "congestion": "high", # Since it's delayed
            "failure_type": "delay",
            "delay_minutes": req.delay_minutes,
            "passengers": req.affected_passengers,
            "timetable_context": "Real Schedule data applied from timetable." if train_info else "No exact timetable match."
        }

        # Run orchestrator
        result = train_orchestrator.run(orchestrator_req)

        rescheduled = False
        original_arrival = None
        new_arrival = None
        conflict_msg = ""
        
        # Reschedule time table in the dataset to reflect dynamically!
        if train_info.get("source") != "Unknown Destination" and req.delay_minutes > 0:
            try:
                df = pd.read_csv(dataset_path)
                # find the correct row
                idx = df.index[df['train_id'].astype(str) == str(req.train_number)].tolist()
                if idx:
                    i = idx[0]
                    original_arrival = str(df.at[i, 'scheduled_arrival'])
                    if ":" in original_arrival:
                        from datetime import datetime, timedelta
                        time_obj = datetime.strptime(original_arrival, '%H:%M')
                        new_time_obj = time_obj + timedelta(minutes=req.delay_minutes)
                        new_arrival = new_time_obj.strftime('%H:%M')
                        df.at[i, 'scheduled_arrival'] = new_arrival
                        rescheduled = True
                        df.to_csv(dataset_path, index=False)
                        
                        # Check collision/platform conflicts
                        platform = str(df.at[i, 'platform'])
                        conflict_trains = df[(df['scheduled_arrival'] == new_arrival) & (df['platform'] == platform) & (df['train_id'].astype(str) != str(req.train_number))]
                        if not conflict_trains.empty:
                            conflict_id = conflict_trains.iloc[0]['train_id']
                            conflict_msg = f"Collision Warning: New arrival {new_arrival} at platform {platform} conflicts with train {conflict_id}! Re-routing required."
            except Exception as ex:
                print(f"Update CSV error: {ex}")

        return {
            "success": True,
            "message": f"Delay of {req.delay_minutes} minutes recorded for train {req.train_number}.",
            "data": {
                "train_number": req.train_number,
                "delay_minutes": req.delay_minutes,
                "current_location": req.current_location,
                "affected_passengers": req.affected_passengers,
                "results": result,
                "plan": result,
                "timetable_updated": rescheduled,
                "original_arrival": original_arrival,
                "new_arrival": new_arrival,
                "conflict_msg": conflict_msg
            }
        }
    except Exception as e:
         return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/passenger-query")
async def handle_passenger_query(req: PassengerQueryRequest):
    return {
        "success": True,
        "answer": f"Processed query: {req.query}",
        "passenger_id": req.passenger_id
    }

@app.post("/api/crowd-prediction")
async def handle_crowd_prediction(req: CrowdPredictionRequest):
    return {
        "success": True,
        "train_number": req.train_number,
        "route": req.route,
        "prediction": {"crowd_level": "moderate", "capacity": "75%"}
    }

@app.post("/api/send-alert")
async def handle_send_alert(req: SendAlertRequest):
    return {
        "success": True,
        "message": "Alerts sent successfully",
        "recipients_count": len(req.recipients),
        "channels": req.channels
    }

@app.get("/api/rag/query")
async def handle_rag_query(query: str):
    return {
        "success": True,
        "query": query,
        "answer": "This is a placeholder response for the RAG query."
    }

@app.post("/api/orchestrate")
async def handle_orchestrate(req: OrchestrateRequest):
    return {
        "success": True,
        "message": "Orchestration successful",
        "request": req.request,
        "context": req.context
    }

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


@app.get('/api/timetable')
async def get_timetable():
    import pandas as pd
    try:
        df = pd.read_csv('chennai_central_real_dataset.csv')
        df = df.fillna("")
        return {'success': True, 'data': df.to_dict(orient='records')}
    except Exception as e:
        return {'success': False, 'message': str(e)}
