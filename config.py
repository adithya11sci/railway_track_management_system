"""
Configuration for Train Management Multi-Agent System
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_PROVIDER = "groq" if GROQ_API_KEY else "gemini"

# Models
GEMINI_MODEL = "gemini-pro"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///railway_intelligence.db")

# Mock Mode Configuration
MOCK_MODE = os.getenv("MOCK_MODE", "False").lower() == "true"
if not GEMINI_API_KEY and not GROQ_API_KEY:
    MOCK_MODE = True
    print("\n⚠️  No API Keys found. Running in MOCK MODE.")
else:
    if os.getenv("MOCK_MODE") is None:
        MOCK_MODE = False

# System Configuration
MAX_RETRY_ATTEMPTS = 3
AGENT_TIMEOUT = 30  # seconds
LOG_LEVEL = "INFO"

# Train Management Settings
DELAY_THRESHOLD_MINUTES = 30  # Delay threshold to trigger Disaster Recovery Agent

# Agent Configuration
AGENT_CONFIG = {
    "scheduling": {
        "model": GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL,
        "temperature": 0.3,
        "max_tokens": 2048
    },
    "time_prediction": {
        "model": GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL,
        "temperature": 0.2,
        "max_tokens": 1500
    },
    "arrival_monitoring": {
        "model": GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL,
        "temperature": 0.3,
        "max_tokens": 1500
    },
    "disaster_recovery": {
        "model": GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL,
        "temperature": 0.4,
        "max_tokens": 2048
    },
}
