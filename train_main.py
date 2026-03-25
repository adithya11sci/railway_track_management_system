"""
🚆 Train Rescheduling Multi-Agent System
Main entry point — CLI for demonstrating the 5-agent rescheduling pipeline.
"""
import json
import os
import sys
from datetime import datetime

# Add local path to ensure imports work
sys.path.append(os.getcwd())

from orchestrator.train_orchestrator import TrainManagementOrchestrator

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  🚆 Train Rescheduling Multi-Agent System                   ║
    ║  5-Agent Architecture  |  LangGraph Orchestrator            ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Agents:                                                     ║
    ║    1. Data Ingestion Agent      – Reads timetable files      ║
    ║    2. Conflict Detection Agent  – Identifies track overlaps  ║
    ║    3. Priority Evaluation Agent – Assigns priorities         ║
    ║    4. Rescheduling Agent        – Adjusts lower-priority     ║
    ║    5. Validation Agent          – Confirms conflict-free     ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Constraints: No two trains on same track at same time.      ║
    ║               Premium > Peak > Regular > Goods               ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def pp(data):
    """Pretty-print JSON."""
    print(json.dumps(data, indent=2, default=str))

def demo_scenario(orch: TrainManagementOrchestrator):
    """Scenario: Run the full rescheduling pipeline."""
    print("\n" + "=" * 70)
    print("🎬 SCENARIO: Full Timetable Conflict Resolution")
    print("=" * 70)
    print("Reading 'chennai_central_real_dataset.csv' and resolving all track conflicts...")

    result = orch.run({"source": "CLI_DEMO", "action": "reschedule_all"})
    
    print("\n📋 FINAL RESULT:")
    pp(result)
    return result

def main():
    print_banner()
    
    dataset_path = 'chennai_central_real_dataset.csv'
    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found at {dataset_path}")
        return

    print("🧠 Initializing Train Rescheduling Orchestrator…")
    orch = TrainManagementOrchestrator(dataset_path=dataset_path)
    print("✅ Orchestrator ready\n")

    print("Select an option:")
    print("  1. Run Full Timetable Rescheduling")
    print("  2. Exit")

    while True:
        choice = input("\n👉 Enter choice (1-2): ").strip()

        if choice == "1":
            demo_scenario(orch)
        elif choice == "2":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Enter 1 or 2.")

if __name__ == "__main__":
    main()
