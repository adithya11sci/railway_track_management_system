"""
Train Management Orchestrator
LangGraph state-machine that coordinates the 4 train agents in sequence:

  User Request → Scheduling → Time Prediction → Monitoring
                                                    ↓
                              (if delayed) → Disaster Recovery → 🔒 APPROVAL → Apply → Re-predict

Maintains global state and enforces system rules:
  1. Always schedule first before prediction
  2. Prediction must complete before monitoring
  3. If delay > threshold → trigger Disaster Recovery
  4. Disaster options require HUMAN APPROVAL before applying
"""
from typing import Dict, Any, List, TypedDict, Annotated, Optional, Callable
import operator
import json
import logging
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    print("❌ LangGraph not found. TrainManagementOrchestrator will fail.")
    pass

from agents.scheduling_agent import SchedulingAgent
from agents.time_prediction_agent import TimePredictionAgent
from agents.arrival_monitoring_agent import ArrivalMonitoringAgent
from agents.disaster_recovery_agent import DisasterRecoveryAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainManagementState(TypedDict):
    """State shared across all train management agents."""
    # Input
    request: Dict[str, Any]

    # Agent results
    schedule_result: Dict[str, Any]
    prediction_result: Dict[str, Any]
    monitoring_result: Dict[str, Any]
    disaster_result: Dict[str, Any]

    # Control
    route_status: str
    iteration: int
    max_iterations: int
    disaster_triggered: bool
    awaiting_approval: bool
    final_response: Dict[str, Any]


class TrainManagementOrchestrator:
    """
    Central Orchestrator of the Multi-Agent Train Management System.

    When disaster recovery is triggered, the pipeline PAUSES to present
    multiple reroute options with impact analysis. Higher officials must
    approve an option before the pipeline continues with re-prediction.
    """

    def __init__(self, delay_threshold: int = 30, approval_callback: Optional[Callable] = None):
        """
        Args:
            delay_threshold: Minutes of delay to trigger disaster recovery.
            approval_callback: Optional function(disaster_result) -> int
                               that returns the chosen option_id.
                               If None, the recommended option is auto-approved.
        """
        self.scheduling = SchedulingAgent()
        self.prediction = TimePredictionAgent()
        self.monitoring = ArrivalMonitoringAgent(delay_threshold=delay_threshold)
        self.disaster = DisasterRecoveryAgent()
        self.delay_threshold = delay_threshold
        self.approval_callback = approval_callback

        self.workflow = self._build_workflow()

    # ================================================================== #
    #  Workflow graph                                                      #
    # ================================================================== #

    def _build_workflow(self) -> Any:
        wf = StateGraph(TrainManagementState)

        # Nodes
        wf.add_node("schedule", self._schedule_node)
        wf.add_node("predict", self._predict_node)
        wf.add_node("monitor", self._monitor_node)
        wf.add_node("disaster", self._disaster_node)
        wf.add_node("approval", self._approval_node)
        wf.add_node("re_predict", self._re_predict_node)
        wf.add_node("synthesize", self._synthesize_node)

        # Entry
        wf.set_entry_point("schedule")

        # Edges: schedule → predict → monitor → (conditional)
        wf.add_edge("schedule", "predict")
        wf.add_edge("predict", "monitor")

        wf.add_conditional_edges(
            "monitor",
            self._route_after_monitor,
            {
                "disaster": "disaster",
                "synthesize": "synthesize",
            },
        )

        # disaster → approval → re_predict → synthesize
        wf.add_edge("disaster", "approval")
        wf.add_edge("approval", "re_predict")
        wf.add_edge("re_predict", "synthesize")

        wf.add_edge("synthesize", END)

        return wf.compile()

    # ================================================================== #
    #  Nodes                                                               #
    # ================================================================== #

    def _schedule_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("🚆 [1/4] Scheduling Agent running…")
        req = state["request"]

        result = self.scheduling.schedule_train(
            train_id=req.get("train_id", "UNKNOWN"),
            source_station=req.get("source", "Station-A"),
            destination_station=req.get("destination", "Station-Z"),
            departure_time=req.get("departure_time", "08:00"),
            available_trains=req.get("available_trains"),
            track_availability=req.get("track_availability"),
            platform_availability=req.get("platform_availability"),
            maintenance_status=req.get("maintenance_status"),
        )

        state["schedule_result"] = result
        state["route_status"] = "scheduled"
        return state

    def _predict_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("⏱️  [2/4] Time Prediction Agent running…")
        req = state["request"]
        schedule = state["schedule_result"]

        speed = req.get("speed_kmh", 80.0)
        distance = req.get("distance_km", 500.0)
        stops_list = schedule.get("stops", [])
        num_stops = len(stops_list) - 2 if len(stops_list) > 2 else req.get("stops", 3)
        halt = req.get("halt_duration_minutes", 5.0)
        dep_time = schedule.get("departure_time", req.get("departure_time", "08:00"))

        result = self.prediction.predict_arrival(
            train_id=req.get("train_id", "UNKNOWN"),
            speed_kmh=speed,
            distance_km=distance,
            stops=max(num_stops, 0),
            halt_duration_minutes=halt,
            track_condition=req.get("track_condition", "good"),
            weather=req.get("weather", "clear"),
            congestion=req.get("congestion", "low"),
            departure_time=dep_time,
        )

        state["prediction_result"] = result
        state["route_status"] = "predicted"
        return state

    def _monitor_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("📡 [3/4] Arrival Monitoring Agent running…")
        req = state["request"]
        prediction = state["prediction_result"]

        predicted_arrival = prediction.get("predicted_arrival_time", "20:00")

        result = self.monitoring.monitor_arrival(
            train_id=req.get("train_id", "UNKNOWN"),
            predicted_arrival_time=predicted_arrival,
            current_gps=req.get("current_gps"),
            current_speed_kmh=req.get("current_speed_kmh", 75.0),
            current_timestamp=req.get("current_timestamp"),
            remaining_distance_km=req.get("remaining_distance_km"),
        )

        state["monitoring_result"] = result
        state["route_status"] = result.get("status", "On-Time").lower().replace("-", "_").replace(" ", "_")
        return state

    def _disaster_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("🚨 [D] Disaster Recovery Agent — generating reroute options…")
        req = state["request"]

        result = self.disaster.handle_disaster(
            train_id=req.get("train_id", "UNKNOWN"),
            failure_type=req.get("failure_type", "major_delay"),
            available_alternate_tracks=req.get("available_alternate_tracks"),
            nearby_trains=req.get("nearby_trains"),
            congestion_map=req.get("congestion_map"),
            current_location=req.get("current_location"),
            original_route=state.get("schedule_result"),
        )

        state["disaster_result"] = result
        state["disaster_triggered"] = True
        state["awaiting_approval"] = True
        return state

    def _approval_node(self, state: TrainManagementState) -> TrainManagementState:
        """
        HUMAN-IN-THE-LOOP: Present options and get approval.
        If approval_callback is set, use it. Otherwise auto-approve recommended.
        """
        disaster = state["disaster_result"]
        options = disaster.get("options", [])
        recommended = disaster.get("recommended_option", 1)

        if self.approval_callback and options:
            logger.info("🔒 Awaiting official approval for reroute option…")
            try:
                chosen_id = self.approval_callback(disaster)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
                chosen_id = recommended
        else:
            logger.info(f"✅ Auto-approving recommended option {recommended}")
            chosen_id = recommended

        # Apply the approved option
        updated = self.disaster.apply_approved_option(disaster, chosen_id)
        state["disaster_result"] = updated
        state["awaiting_approval"] = False
        state["route_status"] = "rerouted"

        logger.info(f"✅ Option {chosen_id} approved — applying reroute")
        return state

    def _re_predict_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("⏱️  [R] Re-predicting arrival after approved re-route…")
        req = state["request"]
        disaster = state["disaster_result"]

        new_sched = disaster.get("new_schedule", {})
        dep_time = new_sched.get("new_departure_time", "08:00")
        extra_km = disaster.get("alternate_route", {}).get("estimated_detour_km", 0)
        distance = req.get("distance_km", 500.0) + extra_km

        result = self.prediction.predict_arrival(
            train_id=req.get("train_id", "UNKNOWN"),
            speed_kmh=req.get("speed_kmh", 60.0),
            distance_km=distance,
            stops=req.get("stops", 3) + 2,
            halt_duration_minutes=req.get("halt_duration_minutes", 5.0),
            track_condition=req.get("track_condition", "fair"),
            weather=req.get("weather", "clear"),
            congestion="moderate",
            departure_time=dep_time,
        )
        result["is_re_prediction"] = True

        state["prediction_result"] = result
        return state

    def _synthesize_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("📋 Synthesizing final response…")

        final = {
            "train_id": state["request"].get("train_id", "UNKNOWN"),
            "route_status": state.get("route_status", "unknown"),
            "disaster_triggered": state.get("disaster_triggered", False),
            "results": {
                "scheduling": state.get("schedule_result", {}),
                "time_prediction": state.get("prediction_result", {}),
                "monitoring": state.get("monitoring_result", {}),
            },
            "completed_at": datetime.now().isoformat(),
        }

        if state.get("disaster_triggered"):
            dr = state.get("disaster_result", {})
            final["results"]["disaster_recovery"] = {
                "root_cause": dr.get("root_cause", {}),
                "options_presented": dr.get("options", []),
                "recommended_option": dr.get("recommended_option"),
                "approved_option": dr.get("approved_option", {}),
                "approval_status": dr.get("approval_status", "unknown"),
                "safety_notes": dr.get("safety_notes", ""),
            }

        state["final_response"] = final
        return state

    # ================================================================== #
    #  Routing                                                             #
    # ================================================================== #

    def _route_after_monitor(self, state: TrainManagementState) -> str:
        monitoring = state.get("monitoring_result", {})
        if monitoring.get("flag_disaster_recovery", False):
            return "disaster"
        return "synthesize"

    # ================================================================== #
    #  Public API                                                          #
    # ================================================================== #

    def run(self, request: Dict[str, Any], max_iterations: int = 2) -> Dict[str, Any]:
        """
        Run the full train management pipeline.

        If disaster recovery is triggered and approval_callback is set,
        the pipeline will call that function with the options and wait
        for the official's choice before continuing.
        """
        initial_state: TrainManagementState = {
            "request": request,
            "schedule_result": {},
            "prediction_result": {},
            "monitoring_result": {},
            "disaster_result": {},
            "route_status": "pending",
            "iteration": 0,
            "max_iterations": max_iterations,
            "disaster_triggered": False,
            "awaiting_approval": False,
            "final_response": {},
        }

        logger.info(f"🚆 Starting Train Management Pipeline for train {request.get('train_id', '?')}")
        final_state = self.workflow.invoke(initial_state)
        return final_state.get("final_response", {})
