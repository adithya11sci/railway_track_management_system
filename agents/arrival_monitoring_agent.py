"""
Arrival Monitoring Agent - Real-Time Train Monitoring
Compares predicted arrival time with real-time position to detect delays
and flag trains for disaster recovery.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from config import AGENT_CONFIG, MOCK_MODE
from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default threshold in minutes — if delay exceeds this, flag for disaster recovery
DEFAULT_DELAY_THRESHOLD = 30


class ArrivalMonitoringAgent:
    """
    Real-Time Train Monitoring Agent.

    Compares predicted arrival with current position & speed to determine:
    - On-Time / Delayed / Not Arrived status
    - Delay magnitude in minutes
    - Risk level (Low / Medium / High)

    Flags trains whose delay exceeds the threshold for the Disaster Recovery Agent.
    """

    def __init__(self, delay_threshold: int = DEFAULT_DELAY_THRESHOLD):
        self.delay_threshold = delay_threshold
        if not MOCK_MODE:
            try:
                self.model = LLMClient(AGENT_CONFIG["arrival_monitoring"])
            except Exception as e:
                logger.error(f"Failed to init LLM for ArrivalMonitoringAgent: {e}")
                self.model = None
        else:
            self.model = None

    def monitor_arrival(
        self,
        train_id: str,
        predicted_arrival_time: str,
        current_gps: Optional[Dict[str, float]] = None,
        current_speed_kmh: float = 0.0,
        current_timestamp: Optional[str] = None,
        remaining_distance_km: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Monitor a train's arrival status.

        Args:
            train_id: Train identifier
            predicted_arrival_time: Predicted ETA as HH:MM string
            current_gps: {"lat": float, "lon": float}
            current_speed_kmh: Current speed of the train
            current_timestamp: ISO-format timestamp of the GPS reading
            remaining_distance_km: Distance still to cover (optional, used for estimate)

        Returns:
            Monitoring result with status, delay, risk level, and flag for disaster agent.
        """
        current_gps = current_gps or {"lat": 13.0827, "lon": 80.2707}
        now = datetime.now()
        current_timestamp = current_timestamp or now.isoformat()

        # Parse predicted arrival
        try:
            pred_time = datetime.strptime(predicted_arrival_time, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            # If predicted time is earlier today, assume next day
            from datetime import timedelta as _td
            if pred_time < now - _td(hours=12):
                pred_time += _td(days=1)
        except ValueError:
            pred_time = now

        # Estimate new arrival based on remaining distance & current speed
        if remaining_distance_km and current_speed_kmh > 0:
            from datetime import timedelta as _td2
            est_remaining_hours = remaining_distance_km / current_speed_kmh
            estimated_arrival = now + _td2(hours=est_remaining_hours)
        else:
            estimated_arrival = pred_time  # fall back to prediction

        delay_minutes = max(0, round((estimated_arrival - pred_time).total_seconds() / 60))

        # Status determination
        if delay_minutes == 0:
            status = "On-Time"
        elif delay_minutes > 0:
            status = "Delayed"
        else:
            status = "On-Time"

        if current_speed_kmh == 0 and remaining_distance_km and remaining_distance_km > 5:
            status = "Not Arrived"

        risk_level = self._assess_risk(delay_minutes)
        flag_disaster = delay_minutes > self.delay_threshold

        result = {
            "train_id": train_id,
            "predicted_arrival_time": predicted_arrival_time,
            "estimated_arrival_time": estimated_arrival.strftime("%H:%M"),
            "current_timestamp": current_timestamp,
            "current_gps": current_gps,
            "current_speed_kmh": current_speed_kmh,
            "status": status,
            "delay_minutes": delay_minutes,
            "risk_level": risk_level,
            "flag_disaster_recovery": flag_disaster,
            "delay_threshold_minutes": self.delay_threshold,
            "monitored_at": datetime.now().isoformat(),
        }

        # If LLM is available and there's notable delay, get expert assessment
        if not MOCK_MODE and self.model and delay_minutes > 5:
            try:
                enriched = self._llm_assess(result)
                result.update(enriched)
            except Exception as e:
                logger.error(f"ArrivalMonitoringAgent LLM error: {e}")

        return result

    # ------------------------------------------------------------------ #
    #  LLM assessment                                                      #
    # ------------------------------------------------------------------ #

    def _llm_assess(self, monitoring_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are a Real-Time Train Monitoring Agent.

Current monitoring data:
{json.dumps(monitoring_data, indent=2)}

Assess the situation and provide:
1. Root cause guess (if delay exists)
2. Updated risk level
3. Recommended immediate actions

Respond ONLY with valid JSON:
{{
    "risk_assessment": "detailed risk note",
    "possible_cause": "signal failure / congestion / weather / unknown",
    "recommended_actions": ["action1", "action2"],
    "risk_level": "Low|Medium|High"
}}"""
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _assess_risk(delay_minutes: int) -> str:
        if delay_minutes <= 10:
            return "Low"
        elif delay_minutes <= 30:
            return "Medium"
        return "High"

    @staticmethod
    def _parse_response(text: str) -> Dict[str, Any]:
        try:
            if "```json" in text:
                s = text.find("```json") + 7
                e = text.find("```", s)
                return json.loads(text[s:e].strip())
            elif "```" in text:
                s = text.find("```") + 3
                e = text.find("```", s)
                return json.loads(text[s:e].strip())
            return json.loads(text.strip())
        except json.JSONDecodeError:
            try:
                return json.loads(text)
            except Exception:
                return {"error": "Failed to parse response", "raw": text}
