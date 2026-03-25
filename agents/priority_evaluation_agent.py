"""
Priority Evaluation Agent — Assigns and compares priorities for conflicting trains.

Priority Hierarchy (highest to lowest):
  1. Premium trains      (Rajdhani, Shatabdi, Vande Bharat, Duronto) — score 4
  2. Peak-hour passenger (Superfast, Mail Express in peak hours)     — score 3
  3. Regular passenger   (Express, Garib Rath, general passenger)    — score 2
  4. Goods trains        (freight, parcel)                           — score 1

Tie-breaking rules:
  - Higher priority keeps its slot.
  - Equal priority → earlier scheduled train keeps its slot.
  - If still tied → train with more intermediate stops (longer route) keeps its slot.

Part of the Multi-Agent Rescheduling Pipeline:
  DataIngestion → ConflictDetection → PriorityEvaluation → Rescheduling → Validation
"""
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from config import AGENT_CONFIG, MOCK_MODE
from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRIORITY_LABELS = {4: "Premium", 3: "Peak-Hour Passenger", 2: "Regular Passenger", 1: "Goods"}


class PriorityEvaluationAgent:
    """
    For each conflict, determines which train should KEEP its slot and
    which train must be RESCHEDULED.

    Output schema (shared state key: 'priority_decisions'):
    {
        "decisions": [
            {
                "conflict_id": "C001",
                "keep_train": { ...train summary },
                "reschedule_train": { ...train summary },
                "reason": "Premium > Regular Passenger",
                "priority_diff": 2
            }
        ],
        "trains_to_reschedule": ["train_id_1", "train_id_2"],
        "summary": "..."
    }
    """

    def __init__(self):
        if not MOCK_MODE:
            try:
                self.model = LLMClient(AGENT_CONFIG["scheduling"])
            except Exception as e:
                logger.error(f"Failed to init LLM for PriorityEvaluationAgent: {e}")
                self.model = None
        else:
            self.model = None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def evaluate(self, conflicts_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        For every conflict, decide which train keeps its slot.

        Args:
            conflicts_data: Output of ConflictDetectionAgent.detect()

        Returns:
            Priority decisions with keep/reschedule assignments.
        """
        conflicts = conflicts_data.get("conflicts", [])
        decisions: List[Dict[str, Any]] = []
        trains_to_reschedule: set = set()

        for conflict in conflicts:
            a = conflict["train_a"]
            b = conflict["train_b"]

            keep, reschedule, reason = self._compare(a, b)

            decisions.append({
                "conflict_id": conflict["conflict_id"],
                "track": conflict.get("track"),
                "conflict_type": conflict.get("type"),
                "conflict_severity": conflict.get("severity"),
                "keep_train": keep,
                "reschedule_train": reschedule,
                "reason": reason,
                "priority_diff": abs(keep.get("priority_score", 2) - reschedule.get("priority_score", 2)),
            })

            trains_to_reschedule.add(reschedule["train_id"])

        result = {
            "decisions": decisions,
            "trains_to_reschedule": sorted(trains_to_reschedule),
            "total_decisions": len(decisions),
            "summary": self._build_summary(decisions),
            "evaluated_at": datetime.now().isoformat(),
        }

        logger.info(f"⚖️  PriorityEvaluationAgent: {len(decisions)} decisions, "
                     f"{len(trains_to_reschedule)} trains need rescheduling")
        return result

    # ------------------------------------------------------------------ #
    #  Comparison logic                                                    #
    # ------------------------------------------------------------------ #

    def _compare(self, a: Dict[str, Any], b: Dict[str, Any]):
        """
        Compare two trains and return (keep, reschedule, reason).
        """
        a_score = a.get("priority_score", 2)
        b_score = b.get("priority_score", 2)

        a_label = PRIORITY_LABELS.get(a_score, "Unknown")
        b_label = PRIORITY_LABELS.get(b_score, "Unknown")

        # Rule 1: Higher priority wins
        if a_score > b_score:
            return a, b, f"{a_label} (score {a_score}) > {b_label} (score {b_score})"
        elif b_score > a_score:
            return b, a, f"{b_label} (score {b_score}) > {a_label} (score {a_score})"

        # Rule 2: Equal priority → earlier scheduled train wins
        a_time = a.get("scheduled_arrival", "99:99")
        b_time = b.get("scheduled_arrival", "99:99")

        if a_time < b_time:
            return a, b, f"Equal priority ({a_label}); earlier slot {a_time} < {b_time}"
        elif b_time < a_time:
            return b, a, f"Equal priority ({b_label}); earlier slot {b_time} < {a_time}"

        # Rule 3: Same time → keep train A by default (stable ordering)
        return a, b, f"Equal priority and slot; keeping {a.get('train_id')} by stable order"

    # ------------------------------------------------------------------ #
    #  Summary                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_summary(decisions: List[Dict[str, Any]]) -> str:
        if not decisions:
            return "No priority decisions needed — no conflicts."
        premium_kept = sum(1 for d in decisions if d["keep_train"].get("priority_score", 0) == 4)
        goods_rescheduled = sum(1 for d in decisions if d["reschedule_train"].get("priority_score", 0) == 1)
        return (
            f"{len(decisions)} conflicts resolved. "
            f"Premium trains kept: {premium_kept}. "
            f"Goods trains rescheduled: {goods_rescheduled}."
        )
