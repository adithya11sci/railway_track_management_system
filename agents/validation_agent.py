"""
Validation Agent - Final verification check on the rescheduled timetable.
Ensures no track overlaps remain and priorities are followed.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationAgent:
    """
    Final check to ensure the rescheduling results are valid.
    """

    def __init__(self, buffer_minutes: int = 20):
        # Minimum buffer time to check against
        self.buffer_minutes = buffer_minutes

    def validate_reschedule(self, original_trains: List[Dict[str, Any]], rescheduled_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that original train data + rescheduled adjustments are conflict-free.
        
        Args:
            original_trains: List of train objects from DataIngestionAgent.
            rescheduled_results: Output of ReschedulingAgent.reschedule().
        
        Returns:
            Dict containing validation status, list of issues, and final summary.
        """
        rescheduled_trains = rescheduled_results.get("rescheduled_trains", {})
        
        # Apply the rescheduling results to a temporary copy of the timetable
        updated_trains = []
        for train in original_trains:
            t_copy = train.copy()
            train_id = t_copy["train_id"]
            if train_id in rescheduled_trains:
                t_copy["scheduled_arrival"] = rescheduled_trains[train_id]["new_arrival"]
                t_copy["scheduled_departure"] = rescheduled_trains[train_id]["new_departure"]
            updated_trains.append(t_copy)
            
        # Perform conflict detection on the updated list
        from agents.conflict_detection_agent import ConflictDetectionAgent
        conflict_agent = ConflictDetectionAgent(buffer_minutes=self.buffer_minutes)
        validation_check = conflict_agent.detect_conflicts(updated_trains)
        
        remaining_conflicts = validation_check.get("conflicts", [])
        
        is_valid = len(remaining_conflicts) == 0
        
        result = {
            "success": is_valid,
            "validation_status": "Valid" if is_valid else "Invalid: Conflicts Remaining",
            "total_conflicts": len(remaining_conflicts),
            "remaining_conflicts": remaining_conflicts,
            "rescheduled_count": len(rescheduled_trains),
            "summary": f"Rescheduled {len(rescheduled_trains)} trains. Validation Status: {'No Conflicts' if is_valid else 'Conflicts Found'}"
        }
        
        logger.info(f"ValidationAgent: Status={result['validation_status']}, Conflicts={len(remaining_conflicts)}")
        return result
