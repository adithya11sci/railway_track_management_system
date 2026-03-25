"""
Conflict Detection Agent - Identifies track conflicts (same track, overlapping time slots).
Ensures no two trains can occupy the same track at the same time.
"""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConflictDetectionAgent:
    """
    Identifies conflicts between trains based on track occupancy and platform time slots.
    """

    def __init__(self, buffer_minutes: int = 15):
        # Mandatory minimum buffer time between trains on the same track
        self.buffer_minutes = buffer_minutes

    def detect_conflicts(self, trains: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for track and platform conflicts.
        
        Args:
            trains: List of train data from DataIngestionAgent.
        
        Returns:
            Dict containing found conflicts and a summary.
        """
        conflicts = []
        # Group trains by track/platform to check collisions
        # In this dataset, 'track_number' is often used as platform or segment.
        # Format "track_number:scheduled_arrival:scheduled_departure"
        
        for i in range(len(trains)):
            for j in range(i + 1, len(trains)):
                t1 = trains[i]
                t2 = trains[j]
                
                # If they are on the same track or platform
                if t1['track_number'] == t2['track_number']:
                    # Compare their time windows
                    conflict_found, reason = self._check_time_overlap(t1, t2)
                    
                    if conflict_found:
                        conflicts.append({
                            "conflict_id": f"C{len(conflicts)+1}",
                            "type": "track_overlap",
                            "track": t1['track_number'],
                            "train_a": t1,
                            "train_b": t2,
                            "reason": reason,
                            "severity": "high"
                        })
        
        result = {
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "summary": f"Detected {len(conflicts)} track/platform conflicts."
        }
        
        logger.info(f"ConflictDetectionAgent: Found {len(conflicts)} conflicts.")
        return result

    def _check_time_overlap(self, t1: Dict[str, Any], t2: Dict[str, Any]) -> Tuple[bool, str]:
        """Checks for time overlap between two trains on the same track."""
        # Convert HH:MM to comparison-friendly format
        def get_times(t):
            arr = t.get('scheduled_arrival', '--')
            dep = t.get('scheduled_departure', '--')
            # If '--', use the other if departure is missing, or arbitrary
            if arr == '--': arr = dep
            if dep == '--': dep = arr
            
            try:
                arr_dt = datetime.strptime(arr, '%H:%M')
                dep_dt = datetime.strptime(dep, '%H:%M')
                # Add buffer
                start = arr_dt - timedelta(minutes=self.buffer_minutes)
                end = dep_dt + timedelta(minutes=self.buffer_minutes)
                return start, end
            except ValueError:
                return None, None

        start1, end1 = get_times(t1)
        start2, end2 = get_times(t2)
        
        if start1 and start2:
            # Check overlap: (StartA < EndB) and (EndA > StartB)
            if start1 < end2 and end1 > start2:
                return True, f"Time overlap detected: {t1['train_id']} ({t1['scheduled_arrival']}-{t1['scheduled_departure']}) and {t2['train_id']} ({t2['scheduled_arrival']}-{t2['scheduled_departure']}) on track {t1['track_number']}"
        
        return False, ""
