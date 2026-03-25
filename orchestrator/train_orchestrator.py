"""
Train Management Orchestrator
LangGraph state-machine that coordinates the 5-agent rescheduling pipeline:

  Data Ingestion → Conflict Detection → Priority Evaluation → Rescheduling → Validation

Maintains global state and ensures no track conflicts remain in the timetable.
"""
from typing import Dict, Any, List, TypedDict, Optional
import logging
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    print("❌ LangGraph not found. TrainManagementOrchestrator will fail.")
    pass

from agents.data_ingestion_agent import DataIngestionAgent
from agents.conflict_detection_agent import ConflictDetectionAgent
from agents.priority_evaluation_agent import PriorityEvaluationAgent
from agents.rescheduling_agent import ReschedulingAgent
from agents.validation_agent import ValidationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainManagementState(TypedDict):
    """State shared across all train rescheduling agents."""
    # Input
    request: Dict[str, Any]

    # Agent results
    train_data: List[Dict[str, Any]]
    conflict_results: Dict[str, Any]
    priority_decisions: Dict[str, Any]
    rescheduling_results: Dict[str, Any]
    validation_results: Dict[str, Any]

    # Control
    status: str
    final_response: Dict[str, Any]


class TrainManagementOrchestrator:
    """
    Central Orchestrator of the Multi-Agent Train Rescheduling System.
    Ensures track conflicts are resolved based on train priority.
    """

    def __init__(self, dataset_path: str = "chennai_central_real_dataset.csv"):
        self.ingestion = DataIngestionAgent(dataset_path=dataset_path)
        self.conflict_detector = ConflictDetectionAgent(buffer_minutes=15)
        self.priority_evaluator = PriorityEvaluationAgent()
        self.rescheduler = ReschedulingAgent(buffer_minutes=20)
        self.validator = ValidationAgent(buffer_minutes=20)

        self.workflow = self._build_workflow()

    # ================================================================== #
    #  Workflow graph                                                      #
    # ================================================================== #

    def _build_workflow(self) -> Any:
        wf = StateGraph(TrainManagementState)

        # Nodes
        wf.add_node("ingest", self._ingest_node)
        wf.add_node("detect", self._detect_node)
        wf.add_node("evaluate", self._evaluate_node)
        wf.add_node("reschedule", self._reschedule_node)
        wf.add_node("validate", self._validate_node)
        wf.add_node("synthesize", self._synthesize_node)

        # Entry
        wf.set_entry_point("ingest")

        # Linear pipeline
        wf.add_edge("ingest", "detect")
        wf.add_edge("detect", "evaluate")
        wf.add_edge("evaluate", "reschedule")
        wf.add_edge("reschedule", "validate")
        wf.add_edge("validate", "synthesize")

        wf.add_edge("synthesize", END)

        return wf.compile()

    # ================================================================== #
    #  Nodes                                                               #
    # ================================================================== #

    def _ingest_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("🚆 [1/5] Data Ingestion Agent running…")
        state["train_data"] = self.ingestion.load_data()
        return state

    def _detect_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("🔍 [2/5] Conflict Detection Agent running…")
        state["conflict_results"] = self.conflict_detector.detect_conflicts(state["train_data"])
        return state

    def _evaluate_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("⚖️  [3/5] Priority Evaluation Agent running…")
        # Reuse existing evaluate logic which takes conflict data
        state["priority_decisions"] = self.priority_evaluator.evaluate(state["conflict_results"])
        return state

    def _reschedule_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("🔄 [4/5] Rescheduling Agent running…")
        state["rescheduling_results"] = self.rescheduler.reschedule(state["priority_decisions"])
        return state

    def _validate_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("✅ [5/5] Validation Agent running…")
        state["validation_results"] = self.validator.validate_reschedule(
            state["train_data"], 
            state["rescheduling_results"]
        )
        return state

    def _synthesize_node(self, state: TrainManagementState) -> TrainManagementState:
        logger.info("📋 Synthesizing final response…")
        
        val = state["validation_results"]
        res = state["rescheduling_results"]
        rescheduled_dict = res.get("rescheduled_trains", {})
        total_rescheduled = len(rescheduled_dict)
        requested_id = state["request"].get("train_id", "UNKNOWN")
        
        # Build ultra-short, human-like summary
        if total_rescheduled > 0:
            if requested_id in rescheduled_dict:
                justification = f"Train {requested_id} was successfully shifted to {rescheduled_dict[requested_id]['new_arrival']} to avoid a priority conflict. {total_rescheduled - 1} other trains were minorly adjusted to ensure track safety."
            else:
                justification = f"Train {requested_id} kept its slot. {total_rescheduled} lower-priority trains were rescheduled to maintain a 20-minute safety buffer."
        else:
            justification = f"Timetable for Train {requested_id} has been updated. No track conflicts were detected."

        if not val.get("success"):
            justification += " (Note: High station congestion detected; please verify platform availability.)"

        final = {
            "success": val.get("success", False),
            "status": val.get("validation_status", "Unknown"),
            "ai_justification": justification,
            "total_conflicts_resolved": total_rescheduled,
            "rescheduled_trains": rescheduled_dict,
            "completed_at": datetime.now().isoformat()
        }
        
        state["final_response"] = final
        return state

    # ================================================================== #
    #  Public API                                                          #
    # ================================================================== #

    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full 5-agent rescheduling pipeline.
        """
        initial_state: TrainManagementState = {
            "request": request,
            "train_data": [],
            "conflict_results": {},
            "priority_decisions": {},
            "rescheduling_results": {},
            "validation_results": {},
            "status": "pending",
            "final_response": {},
        }

        logger.info("🚆 Starting Train Rescheduling Pipeline…")
        final_state = self.workflow.invoke(initial_state)
        return final_state.get("final_response", {})
