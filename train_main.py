"""
🚆 Train Management Multi-Agent System
Main entry point — CLI with demo scenarios and interactive mode
Includes human-in-the-loop approval for disaster rerouting
"""
import json
import sys
from datetime import datetime

from orchestrator.train_orchestrator import TrainManagementOrchestrator


def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  🚆 Train Management Multi-Agent System                     ║
    ║  4-Agent Architecture  |  LangGraph Orchestrator            ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Agents:                                                     ║
    ║    1. Scheduling Agent        – Route & platform assignment  ║
    ║    2. Time Prediction Agent   – ETA calculation              ║
    ║    3. Arrival Monitoring Agent – Real-time tracking           ║
    ║    4. Disaster Recovery Agent  – Re-routing & recovery        ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  ⚠️  Rerouting requires OFFICIAL APPROVAL before applying     ║
    ╚══════════════════════════════════════════════════════════════╝
    """)


def pp(data):
    """Pretty-print JSON."""
    print(json.dumps(data, indent=2, default=str))


# ====================================================================== #
#  Human-in-the-loop Approval Callback                                    #
# ====================================================================== #

def approval_callback(disaster_result: dict) -> int:
    """
    Present reroute options to the official and collect their choice.
    This is called by the orchestrator when disaster recovery triggers.
    """
    options = disaster_result.get("options", [])
    root_cause = disaster_result.get("root_cause", {})
    recommended = disaster_result.get("recommended_option", 1)

    print("\n" + "=" * 70)
    print("🔒 REROUTE APPROVAL REQUIRED — Official Decision Needed")
    print("=" * 70)

    print(f"\n🚨 Incident: {root_cause.get('failure_type', 'unknown').replace('_', ' ').upper()}")
    print(f"   Location: {root_cause.get('location', 'Unknown')}")
    print(f"   Severity: {root_cause.get('severity', 'unknown').upper()}")
    print(f"   Details:  {root_cause.get('description', 'N/A')}")

    print(f"\n📋 {len(options)} Reroute Options Available:")
    print("-" * 70)

    for opt in options:
        oid = opt["option_id"]
        name = opt.get("option_name", f"Option {oid}")
        route = opt.get("alternate_route", {})
        sched = opt.get("new_schedule", {})
        impact = opt.get("impact_analysis", {})
        safety = opt.get("safety_score", "unknown")
        score = opt.get("recommendation_score", "?")
        is_rec = " ⭐ RECOMMENDED" if oid == recommended else ""

        print(f"\n  ┌─ Option {oid}: {name}{is_rec}")
        print(f"  │  Route:       {route.get('track_segment', '?')} (detour: +{route.get('estimated_detour_km', 0)} km)")
        print(f"  │  Via:         {', '.join(route.get('via_stations', []))}")
        print(f"  │  New Depart:  {sched.get('new_departure_time', '?')}")
        print(f"  │  New Arrival: {sched.get('new_estimated_arrival', '?')}")
        print(f"  │  Delay Added: +{sched.get('delay_added_minutes', 0)} min")
        print(f"  │")
        print(f"  │  📊 IMPACT ANALYSIS:")
        print(f"  │    Trains Disturbed:     {impact.get('trains_disturbed', 0)}")
        total_pax = impact.get("total_passengers_affected", 0)
        print(f"  │    Passengers Affected:  ~{total_pax}")
        print(f"  │    Cascading Risk:       {impact.get('cascading_delay_risk', '?')}")

        affected = impact.get("affected_trains", [])
        if affected:
            print(f"  │    Affected Trains:")
            for at in affected:
                print(f"  │      • {at.get('train_id', '?')}: {at.get('impact', '?')} "
                      f"(+{at.get('delay_minutes', 0)} min, ~{at.get('passengers_affected', 0)} pax)")

        print(f"  │")
        print(f"  │  Safety: {safety.upper()}  |  Score: {score}/10")

        pros = opt.get("pros", [])
        cons = opt.get("cons", [])
        if pros:
            print(f"  │  ✅ Pros: {', '.join(pros)}")
        if cons:
            print(f"  │  ❌ Cons: {', '.join(cons)}")
        print(f"  └{'─' * 60}")

    print(f"\n{disaster_result.get('safety_notes', '')}")
    print("-" * 70)

    # Collect decision
    while True:
        try:
            choice = input(
                f"\n👮 Enter option number to APPROVE (1-{len(options)}) "
                f"[recommended: {recommended}]: "
            ).strip()

            if not choice:
                chosen_id = recommended
            else:
                chosen_id = int(choice)

            valid_ids = [o["option_id"] for o in options]
            if chosen_id in valid_ids:
                # Confirm
                chosen_opt = [o for o in options if o["option_id"] == chosen_id][0]
                print(f"\n⚠️  You selected: Option {chosen_id} — {chosen_opt.get('option_name', '')}")
                print(f"   Impact: {chosen_opt.get('impact_analysis', {}).get('trains_disturbed', 0)} trains disturbed, "
                      f"+{chosen_opt.get('new_schedule', {}).get('delay_added_minutes', 0)} min delay")

                confirm = input("   Confirm approval? (y/n) [y]: ").strip().lower()
                if confirm in ("", "y", "yes"):
                    print(f"\n✅ Option {chosen_id} APPROVED by official")
                    return chosen_id
                else:
                    print("   ↩️  Re-select an option.\n")
            else:
                print(f"❌ Invalid. Choose from: {valid_ids}")
        except ValueError:
            print("❌ Please enter a valid number.")
        except EOFError:
            print(f"\n⚡ Auto-approving recommended option {recommended}")
            return recommended


# ====================================================================== #
#  Demo Scenarios                                                         #
# ====================================================================== #

def demo_normal_flow(orch: TrainManagementOrchestrator):
    """Scenario 1: Normal on-time flow — Schedule → Predict → Monitor (on-time)."""
    print("\n" + "=" * 70)
    print("🎬 DEMO 1: Normal On-Time Flow")
    print("=" * 70)

    request = {
        "train_id": "12627",
        "source": "Bangalore",
        "destination": "New Delhi",
        "departure_time": "08:00",
        "speed_kmh": 85,
        "distance_km": 600,
        "stops": 4,
        "halt_duration_minutes": 5,
        "track_condition": "good",
        "weather": "clear",
        "congestion": "low",
        "current_speed_kmh": 80,
        "remaining_distance_km": 10,
    }

    print(f"\n📦 Request: {json.dumps(request, indent=2)}\n")
    result = orch.run(request)
    print("\n📋 RESULT:")
    pp(result)
    return result


def demo_delay_flow(orch: TrainManagementOrchestrator):
    """Scenario 2: Delay detected — triggers Disaster Recovery with APPROVAL."""
    print("\n" + "=" * 70)
    print("🎬 DEMO 2: Delay Detected → Disaster Recovery → APPROVAL REQUIRED")
    print("=" * 70)

    request = {
        "train_id": "12650",
        "source": "Yesvantpur",
        "destination": "New Delhi",
        "departure_time": "18:45",
        "speed_kmh": 70,
        "distance_km": 800,
        "stops": 5,
        "halt_duration_minutes": 8,
        "track_condition": "fair",
        "weather": "heavy_rain",
        "congestion": "high",
        "current_speed_kmh": 20,
        "remaining_distance_km": 400,
        "failure_type": "weather_disruption",
        "current_location": "Katpadi Junction",
        "available_alternate_tracks": ["Track-Via-Vijayawada", "Track-Via-Secunderabad"],
        "nearby_trains": [
            {"train_id": "12627", "location": "Chennai"},
            {"train_id": "16526", "location": "Jolarpettai"},
        ],
        "congestion_map": {
            "Track-Via-Vijayawada": "moderate",
            "Track-Via-Secunderabad": "low",
        },
    }

    print(f"\n📦 Request: {json.dumps(request, indent=2)}\n")
    result = orch.run(request)
    print("\n📋 FINAL RESULT:")
    pp(result)
    return result


def demo_disaster_flow(orch: TrainManagementOrchestrator):
    """Scenario 3: Track damage — 3 options presented for official approval."""
    print("\n" + "=" * 70)
    print("🎬 DEMO 3: Critical Track Damage → 3 Options → APPROVAL REQUIRED")
    print("=" * 70)

    request = {
        "train_id": "22691",
        "source": "Bangalore",
        "destination": "Chennai",
        "departure_time": "06:00",
        "speed_kmh": 90,
        "distance_km": 350,
        "stops": 3,
        "halt_duration_minutes": 5,
        "track_condition": "poor",
        "weather": "storm",
        "congestion": "very_high",
        "current_speed_kmh": 0,
        "remaining_distance_km": 200,
        "failure_type": "track_damage",
        "current_location": "Jolarpettai Section",
        "available_alternate_tracks": [
            "Track-Via-Salem",
            "Track-Via-Vellore",
            "Track-Emergency-Bypass",
        ],
        "nearby_trains": [
            {"train_id": "12627", "location": "Katpadi"},
            {"train_id": "12650", "location": "Arakkonam"},
            {"train_id": "16526", "location": "Jolarpettai"},
        ],
        "congestion_map": {
            "Track-Via-Salem": "low",
            "Track-Via-Vellore": "high",
            "Track-Emergency-Bypass": "low",
        },
    }

    print(f"\n📦 Request: {json.dumps(request, indent=2)}\n")
    result = orch.run(request)
    print("\n📋 FINAL RESULT:")
    pp(result)
    return result


# ====================================================================== #
#  Interactive Mode                                                       #
# ====================================================================== #

def interactive_mode(orch: TrainManagementOrchestrator):
    print("\n" + "=" * 70)
    print("🎯 INTERACTIVE MODE")
    print("=" * 70)
    print("\nProvide train request details (or 'quit' to exit):")
    print("Required: train_id, source, destination")
    print("Optional: departure_time, speed_kmh, distance_km, weather, etc.\n")

    while True:
        train_id = input("🚆 Train ID (or 'quit'): ").strip()
        if train_id.lower() in ("quit", "exit", "q"):
            print("👋 Goodbye!")
            break

        source = input("📍 Source station: ").strip() or "Station-A"
        dest = input("📍 Destination station: ").strip() or "Station-Z"
        weather = input("🌦️  Weather (clear/rain/heavy_rain/fog/storm/snow) [clear]: ").strip() or "clear"
        speed = input("💨 Speed km/h [80]: ").strip()
        distance = input("📏 Distance km [500]: ").strip()

        request = {
            "train_id": train_id,
            "source": source,
            "destination": dest,
            "departure_time": "08:00",
            "speed_kmh": float(speed) if speed else 80.0,
            "distance_km": float(distance) if distance else 500.0,
            "stops": 4,
            "halt_duration_minutes": 5,
            "track_condition": "good",
            "weather": weather,
            "congestion": "low",
            "current_speed_kmh": 75,
            "remaining_distance_km": 50,
        }

        print("\n🤖 Processing through all 4 agents…\n")
        result = orch.run(request)
        print("\n📋 RESULT:")
        pp(result)


# ====================================================================== #
#  Main                                                                   #
# ====================================================================== #

def main():
    print_banner()

    print("🧠 Initializing Train Management Orchestrator…")
    orch = TrainManagementOrchestrator(approval_callback=approval_callback)
    print("✅ Orchestrator ready\n")

    print("Select an option:")
    print("  1. Demo 1 — Normal on-time flow")
    print("  2. Demo 2 — Delay → Disaster Recovery (2 options, approval required)")
    print("  3. Demo 3 — Track damage (3 options, approval required)")
    print("  4. Run ALL demos")
    print("  5. Interactive mode")
    print("  6. Exit")

    while True:
        choice = input("\n👉 Enter choice (1-6): ").strip()

        if choice == "1":
            demo_normal_flow(orch)
        elif choice == "2":
            demo_delay_flow(orch)
        elif choice == "3":
            demo_disaster_flow(orch)
        elif choice == "4":
            demo_normal_flow(orch)
            demo_delay_flow(orch)
            demo_disaster_flow(orch)
        elif choice == "5":
            interactive_mode(orch)
        elif choice == "6":
            print("\n👋 Thank you for using Train Management System!")
            break
        else:
            print("❌ Invalid choice. Enter 1-6.")


if __name__ == "__main__":
    main()
