"""
Rescheduling Agent - Adjusts timings to resolve conflicts based on priority.
Ensures higher-priority trains keep their slots while shifting lower-priority ones.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReschedulingAgent:
    """
    Adjusts the schedule based on priority and minimum buffer requirements.
    """

    def __init__(self, buffer_minutes: int = 20):
        # Minimum buffer time between trains on the same track
        self.buffer_minutes = buffer_minutes

    def reschedule(self, decisions_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust timing for trains tagged for rescheduling.
        
        Args:
            decisions_data: Decisions from PriorityEvaluationAgent.
            - decisions: List of objects { conflict_id, keep_train, reschedule_train, reason, priority_diff }
        
        Returns:
            Dict containing the updated (rescheduled) train data.
        """
        decisions = decisions_data.get("decisions", [])
        rescheduled_trains = {}

        for decision in decisions:
            keep_train = decision["keep_train"]
            reschedule_train = decision["reschedule_train"]
            
            # Find a safe slot for reschedule_train
            # Logic: Shift reschedule_train until it no longer overlaps with keep_train
            # Including the buffer
            
            # Use original times to calculate shift
            keep_arr = keep_train.get('scheduled_arrival', '--')
            keep_dep = keep_train.get('scheduled_departure', '--')
            if keep_arr == '--': keep_arr = keep_dep
            if keep_dep == '--': keep_dep = keep_arr
            
            res_arr = reschedule_train.get('scheduled_arrival', '--')
            res_dep = reschedule_train.get('scheduled_departure', '--')
            if res_arr == '--': res_arr = res_dep
            if res_dep == '--': res_dep = res_arr
            
            try:
                # keep_dt_end = max arrival/dep + buffer
                keep_arr_dt = datetime.strptime(keep_arr, '%H:%M')
                keep_dep_dt = datetime.strptime(keep_dep, '%H:%M')
                keep_end = max(keep_arr_dt, keep_dep_dt) + timedelta(minutes=self.buffer_minutes)
                
                # res_start = min arrival/dep
                res_arr_dt = datetime.strptime(res_arr, '%H:%M')
                res_dep_dt = datetime.strptime(res_dep, '%H:%M')
                res_start = min(res_arr_dt, res_dep_dt)
                
                # If res_start is before or during keep_end, it needs to move
                if res_start < keep_end:
                   # Shift reschedule_train to start AT keep_end
                   shift_minutes = (keep_end - res_start).total_seconds() / 60
                   
                   new_arr_dt = res_arr_dt + timedelta(minutes=shift_minutes)
                   new_dep_dt = res_dep_dt + timedelta(minutes=shift_minutes)
                   
                   # Update the specific train record
                   # Avoid re-encoding to original string if not needed
                   train_id = reschedule_train["train_id"]
                   rescheduled_trains[train_id] = {
                       "train_id": train_id,
                       "original_arrival": res_arr,
                       "original_departure": res_dep,
                       "new_arrival": new_arr_dt.strftime('%H:%M'),
                       "new_departure": new_dep_dt.strftime('%H:%M'),
                       "delay_minutes": int(shift_minutes),
                       "reason": f"Displaced by higher priority train {keep_train['train_id']} ({decision['reason']})"
                   }
            except ValueError:
                # Handle time parsing issues gracefully
                continue
                
        result = {
            "rescheduled_trains": rescheduled_trains,
            "total_rescheduled": len(rescheduled_trains),
            "summary": f"Rescheduled {len(rescheduled_trains)} trains to resolve track conflicts."
        }
        
        logger.info(f"ReschedulingAgent: Rescheduled {len(rescheduled_trains)} trains.")
        return result
