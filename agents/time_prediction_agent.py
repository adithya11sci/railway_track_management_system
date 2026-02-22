"""
Time Prediction Agent - Arrival Time Calculator
Predicts accurate arrival time incorporating speed, distance, stops,
weather, and congestion factors.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config import AGENT_CONFIG, MOCK_MODE
from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weather delay multipliers
WEATHER_FACTORS = {
    "clear": 1.0,
    "rain": 1.15,
    "heavy_rain": 1.30,
    "fog": 1.25,
    "storm": 1.50,
    "snow": 1.40,
}

# Congestion multipliers
CONGESTION_FACTORS = {
    "low": 1.0,
    "moderate": 1.10,
    "high": 1.25,
    "very_high": 1.40,
}

# Track condition multipliers
TRACK_CONDITION_FACTORS = {
    "excellent": 1.0,
    "good": 1.05,
    "fair": 1.15,
    "poor": 1.30,
}


class TimePredictionAgent:
    """
    Train Arrival Time Prediction Agent.

    Predicts accurate arrival time using:
    - Distance / Speed base calculation
    - Halt times at intermediate stops
    - Weather delay factor
    - Congestion multiplier
    - Track condition adjustment
    """

    def __init__(self):
        if not MOCK_MODE:
            try:
                self.model = LLMClient(AGENT_CONFIG["time_prediction"])
            except Exception as e:
                logger.error(f"Failed to init LLM for TimePredictionAgent: {e}")
                self.model = None
        else:
            self.model = None

    def predict_arrival(
        self,
        train_id: str,
        speed_kmh: float = 80.0,
        distance_km: float = 500.0,
        stops: int = 5,
        halt_duration_minutes: float = 5.0,
        track_condition: str = "good",
        weather: str = "clear",
        congestion: str = "low",
        departure_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Predict arrival time.

        Args:
            train_id: Train identifier
            speed_kmh: Average operating speed in km/h
            distance_km: Total distance in km
            stops: Number of intermediate stops
            halt_duration_minutes: Average halt per stop in minutes
            track_condition: excellent / good / fair / poor
            weather: clear / rain / heavy_rain / fog / storm / snow
            congestion: low / moderate / high / very_high
            departure_time: Departure time string (HH:MM), defaults to now

        Returns:
            Prediction result with ETA, delay probability, and confidence score.
        """
        # ── Mathematical calculation (always done, even in LLM mode) ──
        base_travel_hours = distance_km / speed_kmh
        total_halt_hours = (stops * halt_duration_minutes) / 60.0

        weather_mult = WEATHER_FACTORS.get(weather, 1.0)
        congestion_mult = CONGESTION_FACTORS.get(congestion, 1.0)
        track_mult = TRACK_CONDITION_FACTORS.get(track_condition, 1.0)

        adjusted_travel_hours = base_travel_hours * weather_mult * congestion_mult * track_mult
        total_hours = adjusted_travel_hours + total_halt_hours

        # Departure handling
        if departure_time:
            try:
                dep = datetime.strptime(departure_time, "%H:%M")
                dep = dep.replace(year=datetime.now().year,
                                  month=datetime.now().month,
                                  day=datetime.now().day)
            except ValueError:
                dep = datetime.now()
        else:
            dep = datetime.now()

        predicted_arrival = dep + timedelta(hours=total_hours)

        # Delay probability heuristic
        delay_probability = self._calc_delay_probability(
            weather, congestion, track_condition
        )
        confidence = self._calc_confidence(
            weather, congestion, track_condition, distance_km
        )

        math_result = {
            "train_id": train_id,
            "departure_time": dep.strftime("%H:%M"),
            "predicted_arrival_time": predicted_arrival.strftime("%H:%M"),
            "total_travel_hours": round(total_hours, 2),
            "base_travel_hours": round(base_travel_hours, 2),
            "halt_time_hours": round(total_halt_hours, 2),
            "adjustments": {
                "weather_factor": weather_mult,
                "congestion_factor": congestion_mult,
                "track_condition_factor": track_mult,
            },
            "delay_probability_percent": delay_probability,
            "confidence_score": confidence,
            "parameters": {
                "speed_kmh": speed_kmh,
                "distance_km": distance_km,
                "stops": stops,
                "halt_duration_minutes": halt_duration_minutes,
                "track_condition": track_condition,
                "weather": weather,
                "congestion": congestion,
            },
            "predicted_at": datetime.now().isoformat(),
        }

        if MOCK_MODE or not self.model:
            return math_result

        # ── LLM enrichment ──
        try:
            prompt = f"""You are a Train Arrival Time Prediction Agent.

I have already computed the mathematical estimates:
{json.dumps(math_result, indent=2)}

Review these numbers and provide your expert assessment. Adjust the prediction
if you see any factor that the math may have missed (e.g. cumulative fatigue at
many stops, nighttime speed restrictions, etc.).

Respond ONLY with valid JSON in this format:
{{
    "train_id": "{train_id}",
    "departure_time": "{dep.strftime('%H:%M')}",
    "predicted_arrival_time": "HH:MM",
    "total_travel_hours": <float>,
    "delay_probability_percent": <float 0-100>,
    "confidence_score": <float 0-1>,
    "adjustments_applied": ["list of extra adjustments"],
    "notes": "any expert commentary"
}}"""
            response = self.model.generate_content(prompt)
            enriched = self._parse_response(response.text)
            # Merge enriched into math_result so we keep all fields
            math_result.update(enriched)
            return math_result
        except Exception as e:
            logger.error(f"TimePredictionAgent LLM error: {e}")
            return math_result

    # ------------------------------------------------------------------ #
    #  Heuristics                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _calc_delay_probability(weather: str, congestion: str, track: str) -> float:
        base = 5.0  # 5% base
        weather_add = {"clear": 0, "rain": 10, "heavy_rain": 25,
                       "fog": 20, "storm": 40, "snow": 35}.get(weather, 5)
        congestion_add = {"low": 0, "moderate": 8, "high": 18,
                          "very_high": 30}.get(congestion, 5)
        track_add = {"excellent": 0, "good": 3, "fair": 12,
                     "poor": 25}.get(track, 5)
        return min(round(base + weather_add + congestion_add + track_add, 1), 99.0)

    @staticmethod
    def _calc_confidence(weather: str, congestion: str, track: str,
                         distance: float) -> float:
        base = 0.95
        if weather not in ("clear",):
            base -= 0.1
        if congestion not in ("low",):
            base -= 0.08
        if track not in ("excellent", "good"):
            base -= 0.07
        if distance > 1000:
            base -= 0.05
        return round(max(base, 0.30), 2)

    # ------------------------------------------------------------------ #
    #  Response parsing                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_response(response_text: str) -> Dict[str, Any]:
        try:
            if "```json" in response_text:
                s = response_text.find("```json") + 7
                e = response_text.find("```", s)
                return json.loads(response_text[s:e].strip())
            elif "```" in response_text:
                s = response_text.find("```") + 3
                e = response_text.find("```", s)
                return json.loads(response_text[s:e].strip())
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            try:
                return json.loads(response_text)
            except Exception:
                return {"error": "Failed to parse response", "raw": response_text}
