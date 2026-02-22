"""
Train Scheduling Agent - Route & Platform Assignment
Assigns optimal routes based on train availability, track/platform constraints,
and maintenance status.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config import AGENT_CONFIG, MOCK_MODE
from utils.llm_client import LLMClient
from tools.train_schedule_tool import TrainScheduleTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulingAgent:
    """
    Train Scheduling Optimization Agent.

    Responsible for:
    - Assigning routes based on train availability
    - Allocating platforms avoiding conflicts
    - Ensuring maintenance clearance
    - Minimizing congestion
    """

    def __init__(self):
        if not MOCK_MODE:
            try:
                self.model = LLMClient(AGENT_CONFIG["scheduling"])
            except Exception as e:
                logger.error(f"Failed to init LLM for SchedulingAgent: {e}")
                self.model = None
        else:
            self.model = None
        self.schedule_tool = TrainScheduleTool()

    def schedule_train(
        self,
        train_id: str,
        source_station: str,
        destination_station: str,
        departure_time: str = "08:00",
        available_trains: Optional[List[str]] = None,
        track_availability: Optional[Dict[str, bool]] = None,
        platform_availability: Optional[Dict[str, List[int]]] = None,
        maintenance_status: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a train route.

        Args:
            train_id: Unique identifier for the train
            source_station: Origin station name
            destination_station: Final destination station name
            departure_time: Desired departure time (HH:MM)
            available_trains: List of available train IDs
            track_availability: Track segment -> available (bool)
            platform_availability: Station -> list of free platform numbers
            maintenance_status: Track/train -> maintenance status

        Returns:
            Scheduling result with route, platform, stops, and timings (JSON dict).
        """
        available_trains = available_trains or [train_id]
        track_availability = track_availability or {
            f"{source_station}-{destination_station}": True
        }
        platform_availability = platform_availability or {
            source_station: [1, 2, 3],
            destination_station: [1, 2, 3, 4],
        }
        maintenance_status = maintenance_status or {"all_clear": True}

        # Pull any existing schedule info for context
        existing_schedule = self.schedule_tool.get_train_schedule(train_id)

        prompt = f"""You are a Train Scheduling Optimization Agent.

Your task: Schedule the optimal route for a train.

INPUTS:
- Train ID: {train_id}
- Available Trains: {json.dumps(available_trains)}
- Source Station: {source_station}
- Destination Station: {destination_station}
- Departure Time: {departure_time}
- Track Availability: {json.dumps(track_availability)}
- Platform Availability: {json.dumps(platform_availability)}
- Maintenance Status: {json.dumps(maintenance_status)}
- Existing Schedule Data: {json.dumps(existing_schedule, indent=2)}

Constraints:
- Avoid track conflicts
- Avoid platform clashes
- Ensure maintenance clearance
- Minimize congestion

Respond ONLY with valid JSON in this exact format:
{{
    "train_id": "{train_id}",
    "assigned_route": {{
        "source": "{source_station}",
        "destination": "{destination_station}",
        "via_stations": ["Station1", "Station2"]
    }},
    "platform_number": 1,
    "departure_time": "{departure_time}",
    "estimated_base_travel_time_hours": 12.5,
    "stops": [
        {{
            "station": "Station Name",
            "arrival_time": "HH:MM",
            "departure_time": "HH:MM",
            "halt_duration_minutes": 5,
            "platform": 1
        }}
    ],
    "track_segment": "{source_station}-{destination_station}",
    "maintenance_clearance": true,
    "scheduling_notes": "Any important notes"
}}"""

        if MOCK_MODE or not self.model:
            return self._mock_schedule(
                train_id, source_station, destination_station, departure_time
            )

        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            result["scheduled_at"] = datetime.now().isoformat()
            return result
        except Exception as e:
            logger.error(f"SchedulingAgent error: {e}")
            return self._mock_schedule(
                train_id, source_station, destination_station, departure_time
            )

    # ------------------------------------------------------------------ #
    #  Mock / Helpers                                                      #
    # ------------------------------------------------------------------ #

    def _mock_schedule(
        self, train_id: str, source: str, destination: str, departure: str
    ) -> Dict[str, Any]:
        """Return a deterministic mock schedule."""
        stops = [
            {"station": source, "arrival_time": None, "departure_time": departure,
             "halt_duration_minutes": 0, "platform": 1},
            {"station": "Intermediate-A", "arrival_time": "11:30",
             "departure_time": "11:35", "halt_duration_minutes": 5, "platform": 2},
            {"station": "Intermediate-B", "arrival_time": "15:00",
             "departure_time": "15:10", "halt_duration_minutes": 10, "platform": 1},
            {"station": destination, "arrival_time": "20:30",
             "departure_time": None, "halt_duration_minutes": 0, "platform": 3},
        ]
        return {
            "train_id": train_id,
            "assigned_route": {
                "source": source,
                "destination": destination,
                "via_stations": ["Intermediate-A", "Intermediate-B"],
            },
            "platform_number": 1,
            "departure_time": departure,
            "estimated_base_travel_time_hours": 12.5,
            "stops": stops,
            "track_segment": f"{source}-{destination}",
            "maintenance_clearance": True,
            "scheduling_notes": "Mock schedule — all tracks clear",
            "scheduled_at": datetime.now().isoformat(),
        }

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        try:
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                return json.loads(response_text)
            except Exception:
                return {"error": "Failed to parse response", "raw": response_text}
