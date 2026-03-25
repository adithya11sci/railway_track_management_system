# 🚆 Railway Multi-Agent Rescheduling System (RMS)

## 📌 Project Definition
The **Railway Multi-Agent Rescheduling System** is an AI-powered, real-time platform designed to manage and resolve train timetable conflicts. When a train delay occurs, the system automatically redistributes time slots across the network based on train priorities, ensuring safety buffers are maintained while minimizing operational disruptions.

---

## 🏗️ System Architecture

The project follows a **Micro-Service Architecture** distributed across three main layers:

### 1. 🖥️ Frontend (React & Vite)
- **Framework**: React 18 with Vite.
- **Styling**: TailwindCSS with premium, responsive UI components.
- **State Management**: React Hooks & LocalStorage for auth persistence.
- **Features**: Live Timetable view, Train Delay input, AI Response visualization, and Officer Dashboard.

### 2. 🧠 Core Management Engine (FastAPI & LangGraph)
- **Framework**: FastAPI (Python 3.10+).
- **Orchestrator**: **LangGraph** (LangChain) for state-machine coordination of multiple agents.
- **Data Store**: Real-world CSV dataset (`chennai_central_real_dataset.csv`) as the source of truth for scheduling.
- **WebSocket**: Real-time broadcasting of rescheduling updates to all connected clients.

### 3. 🔐 Security & Notification Service (Express & MongoDB)
- **Framework**: Node.js & Express.
- **Database**: **MongoDB (localhost)** for officer account management.
- **Authentication**: JWT (JSON Web Tokens) with Bcrypt password hashing.
- **Notification**: **Nodemailer** integration for sending instant email alerts to all registered officers.

---

## 🤖 AI Agent Pipeline (The 5-Agent Flow)

When a delay is submitted, the system triggers a linear coordination graph managed by the **TrainManagementOrchestrator**:

1.  **📦 Data Ingestion Agent**:
    - Reads the CSV timetable.
    - Normalizes train types (Premium, Express, Regular, Goods).
    - Assigns priority scores (4 to 1).
2.  **🔍 Conflict Detection Agent**:
    - Analyzes track/platform occupancy.
    - Identifies "high-risk" overlaps where safety buffers (e.g., 20m) are violated.
3.  **⚖️ Priority Evaluation Agent**:
    - Evaluates conflicting trains.
    - Uses priority rules and tie-breakers (earlier slot wins) to decide which train must be rescheduled.
4.  **🔄 Rescheduling Agent**:
    - Calculates new arrival and departure offsets.
    - Shifts lower-priority trains to the next available "safety gap."
    - Updates both arrival and departure slots for consistent journey flow.
5.  **✅ Validation Agent**:
    - Runs a final sweep over the updated timetable.
    - Confirms that the final output is 100% collision-free before committing to the database.

---

## 🔄 End-to-End Operational Flow

### Phase 1: Authentication
1.  **Register**: The officer lands on the Register page and creates an account (Stored in MongoDB).
2.  **Login**: Officer authenticates and receives a JWT token, gaining access to the secure dashboard.

### Phase 2: Delay Submission
1.  An officer inputs a train's delay at a specific location.
2.  The **FastAPI server** receives the `POST /api/train-delay` request.
3.  The system identifies the train in the `chennai_central_real_dataset.csv` and applies the initial delay offset.

### Phase 3: AI Rescheduling
1.  The **LangGraph Orchestrator** starts the 5-agent pipeline.
2.  Agents detect if the new delayed time causes a "Track Overlap" with any other train.
3.  Lower-priority trains are pushed forward in time to clear the track for higher-priority ones.
4.  The final, conflict-free timetable is saved back to the CSV.

### Phase 4: Feedback & Alerting
1.  **Webhooks**: The new timetable is instantly pushed to the frontend via WebSockets.
2.  **AI Response**: The user sees a summarized justification (e.g., *"Train 12627 was shifted 20m to accommodate the Premium Express delay"*).
3.  **Notifications**: FastAPI triggers the **Express Notify Service**.
4.  **Emails**: All registered officers receive an official email alert with the rescheduling details.

---

## 🛠️ Technical Stack
- **Languages**: Python, JavaScript, TypeScript.
- **APIs**: FastAPI, Express.
- **Database**: MongoDB, CSV (pandas).
- **AI Frameworks**: LangChain, LangGraph.
- **Email Service**: SMTP (Gmail) via Nodemailer.
- **Frontend**: React, Tailwind, Vite, Axios.

---

## 📂 Project Structure
- `/api`: Core FastAPI backend & Agents.
- `/backend`: Express Auth & Notification service.
- `/frontend`: React Dashboard source code.
- `/orchestrator`: LangGraph coordination logic.
- `/agents`: Local agent implementation files.
- `chennai_central_real_dataset.csv`: Master timetable data.
