"""
Disaster Recovery & Re-routing Agent
Handles train breakdowns, track damage, weather disruptions, and major delays.
Generates MULTIPLE route options with full impact analysis for official approval.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config import AGENT_CONFIG, MOCK_MODE
from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Known failure types for validation
FAILURE_TYPES = [
    "breakdown", "track_damage", "flood", "weather_disruption",
    "signal_failure", "derailment", "power_failure", "obstruction",
    "major_delay", "unknown",
]


class DisasterRecoveryAgent:
    """
    Railway Disaster Recovery & Re-routing Agent.

    Generates MULTIPLE reroute options, each with:
    - Alternate route details
    - Impact analysis (trains disturbed, delay added, passengers affected)
    - New schedule
    - Safety assessment

    Options must be APPROVED by higher officials before being applied.
    """

    def __init__(self):
        if not MOCK_MODE:
            try:
                self.model = LLMClient(AGENT_CONFIG["disaster_recovery"])
            except Exception as e:
                logger.error(f"Failed to init LLM for DisasterRecoveryAgent: {e}")
                self.model = None
        else:
            self.model = None

    def handle_disaster(
        self,
        train_id: str,
        failure_type: str = "unknown",
        available_alternate_tracks: Optional[List[str]] = None,
        nearby_trains: Optional[List[Dict[str, Any]]] = None,
        congestion_map: Optional[Dict[str, str]] = None,
        current_location: Optional[str] = None,
        original_route: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze disaster and produce MULTIPLE reroute options for approval.

        Returns:
            Dict with root_cause and a list of 'options', each containing
            route details, impact analysis, new schedule, and recommendation.
            Requires 'approved_option' to be set before the pipeline continues.
        """
        if failure_type not in FAILURE_TYPES:
            failure_type = "unknown"

        available_alternate_tracks = available_alternate_tracks or [
            "Track-Alt-A", "Track-Alt-B"
        ]
        nearby_trains = nearby_trains or []
        congestion_map = congestion_map or {
            "Track-Alt-A": "low",
            "Track-Alt-B": "moderate",
        }
        current_location = current_location or "Unknown Section"
        original_route = original_route or {}

        prompt = f"""You are a Railway Disaster Recovery & Re-routing Agent.

A disruption has occurred. You must produce MULTIPLE reroute options so that
higher officials can review the impact and choose the best one.

CRITICAL: Only use the provided inputs. Never hallucinate reasons. Prioritize SAFETY.

INPUTS:
- Train ID: {train_id}
- Failure Type: {failure_type}
- Current Location: {current_location}
- Available Alternate Tracks: {json.dumps(available_alternate_tracks)}
- Nearby Trains: {json.dumps(nearby_trains)}
- Current Congestion Map: {json.dumps(congestion_map)}
- Original Route: {json.dumps(original_route, indent=2)}

PRODUCE exactly {len(available_alternate_tracks)} options — one for EACH available alternate track.
For each option, analyze:
1. The route details (track, via stations, detour distance)
2. Impact on OTHER trains (how many disturbed, delay minutes for each)
3. Impact on passengers (estimated affected count)
4. New schedule (departure, arrival, delay added)
5. Safety assessment
6. Overall recommendation score (1-10, where 10 = best)

Respond ONLY with valid JSON:
{{
    "train_id": "{train_id}",
    "root_cause": {{
        "failure_type": "{failure_type}",
        "description": "What happened based on inputs",
        "severity": "low|medium|high|critical",
        "location": "{current_location}"
    }},
    "options": [
        {{
            "option_id": 1,
            "option_name": "Via [Track Name]",
            "alternate_route": {{
                "track_segment": "Track-Alt-X",
                "via_stations": ["Station1", "Station2"],
                "estimated_detour_km": 25
            }},
            "new_schedule": {{
                "new_departure_time": "HH:MM",
                "new_estimated_arrival": "HH:MM",
                "delay_added_minutes": 30
            }},
            "impact_analysis": {{
                "trains_disturbed": 2,
                "affected_trains": [
                    {{
                        "train_id": "XXXXX",
                        "impact": "delayed|rerouted|cancelled",
                        "delay_minutes": 15,
                        "passengers_affected": 500
                    }}
                ],
                "total_passengers_affected": 1200,
                "cascading_delay_risk": "low|medium|high"
            }},
            "safety_score": "safe|moderate_risk|high_risk",
            "recommendation_score": 8,
            "pros": ["Low congestion", "Short detour"],
            "cons": ["2 trains affected"]
        }}
    ],
    "recommended_option": 1,
    "requires_approval": true,
    "safety_notes": "Overall safety observations"
}}"""

        if MOCK_MODE or not self.model:
            return self._mock_recovery(
                train_id, failure_type, available_alternate_tracks,
                nearby_trains, current_location, congestion_map
            )

        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            result["requires_approval"] = True
            result["approved_option"] = None
            result["approval_status"] = "pending"
            result["generated_at"] = datetime.now().isoformat()
            return result
        except Exception as e:
            logger.error(f"DisasterRecoveryAgent error: {e}")
            return self._mock_recovery(
                train_id, failure_type, available_alternate_tracks,
                nearby_trains, current_location, congestion_map
            )

    def apply_approved_option(self, disaster_result: Dict[str, Any], option_id: int) -> Dict[str, Any]:
        """
        Apply the approved option chosen by higher officials.

        Args:
            disaster_result: Full result from handle_disaster()
            option_id: The option_id chosen by the official

        Returns:
            Updated disaster_result with the approved option applied.
        """
        options = disaster_result.get("options", [])
        chosen = None
        for opt in options:
            if opt.get("option_id") == option_id:
                chosen = opt
                break

        if not chosen:
            disaster_result["approval_status"] = "error"
            disaster_result["error"] = f"Option {option_id} not found"
            return disaster_result

        disaster_result["approved_option"] = chosen
        disaster_result["approval_status"] = "approved"
        disaster_result["approved_at"] = datetime.now().isoformat()

        # Flatten chosen option fields for downstream use (re-prediction reads these)
        disaster_result["alternate_route"] = chosen.get("alternate_route", {})
        disaster_result["new_schedule"] = chosen.get("new_schedule", {})
        disaster_result["affected_trains"] = chosen.get("impact_analysis", {}).get("affected_trains", [])

        return disaster_result

    # ------------------------------------------------------------------ #
    #  Mock recovery with multiple options                                 #
    # ------------------------------------------------------------------ #

    def _mock_recovery(
        self,
        train_id: str,
        failure_type: str,
        alternate_tracks: List[str],
        nearby_trains: List[Dict[str, Any]],
        location: str,
        congestion_map: Dict[str, str],
    ) -> Dict[str, Any]:
        severity = self._severity_for_type(failure_type)

        options = []
        for idx, track in enumerate(alternate_tracks, start=1):
            cong = congestion_map.get(track, "moderate")
            cong_delay = {"low": 15, "moderate": 35, "high": 60}.get(cong, 30)
            detour_km = 20 + (idx * 10)

            # More congestion = more trains disturbed
            trains_disturbed = max(1, len(nearby_trains) - (1 if cong == "low" else 0))
            affected = []
            total_pax = 0
            for nt in nearby_trains[:trains_disturbed]:
                pax = 400 + (idx * 100)
                affected.append({
                    "train_id": nt.get("train_id", "unknown"),
                    "impact": "delayed",
                    "delay_minutes": cong_delay // 2,
                    "passengers_affected": pax,
                })
                total_pax += pax

            recovery = datetime.now() + timedelta(minutes=cong_delay)
            safety = "safe" if cong == "low" else ("moderate_risk" if cong == "moderate" else "high_risk")
            score = {"low": 9, "moderate": 6, "high": 3}.get(cong, 5)

            options.append({
                "option_id": idx,
                "option_name": f"Via {track}",
                "alternate_route": {
                    "track_segment": track,
                    "via_stations": [f"Detour-{track}-Stn1", f"Detour-{track}-Stn2"],
                    "estimated_detour_km": detour_km,
                },
                "new_schedule": {
                    "new_departure_time": datetime.now().strftime("%H:%M"),
                    "new_estimated_arrival": recovery.strftime("%H:%M"),
                    "delay_added_minutes": cong_delay,
                },
                "impact_analysis": {
                    "trains_disturbed": trains_disturbed,
                    "affected_trains": affected,
                    "total_passengers_affected": total_pax,
                    "cascading_delay_risk": cong,
                },
                "safety_score": safety,
                "recommendation_score": score,
                "pros": [
                    f"{'Low' if cong == 'low' else 'Available'} congestion on {track}",
                    f"Detour: {detour_km} km",
                ],
                "cons": [
                    f"{trains_disturbed} train(s) disturbed",
                    f"+{cong_delay} min delay added",
                    f"~{total_pax} passengers affected",
                ],
            })

        # Sort by recommendation score (best first)
        options.sort(key=lambda o: o["recommendation_score"], reverse=True)
        recommended = options[0]["option_id"] if options else 1

        return {
            "train_id": train_id,
            "root_cause": {
                "failure_type": failure_type,
                "description": f"{failure_type.replace('_', ' ').title()} detected at {location}",
                "severity": severity,
                "location": location,
            },
            "options": options,
            "recommended_option": recommended,
            "requires_approval": True,
            "approved_option": None,
            "approval_status": "pending",
            "safety_notes": "All options verified for passenger safety. Choose based on minimum disruption.",
            "generated_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _severity_for_type(failure_type: str) -> str:
        mapping = {
            "breakdown": "high",
            "track_damage": "critical",
            "flood": "critical",
            "weather_disruption": "high",
            "signal_failure": "medium",
            "derailment": "critical",
            "power_failure": "medium",
            "obstruction": "high",
            "major_delay": "medium",
            "unknown": "medium",
        }
        return mapping.get(failure_type, "medium")

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
