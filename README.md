# Aevoxis Warden Engine: Spec-Drift Chronometer

## Project Overview
The **Aevoxis Warden Engine** is a sovereign monitoring system designed to detect and visualize temporal variance (Spec-Drift) in real-time. Built with a focus on security, transparency, and high-performance serverless architecture.

### Tech Stack
* **Frontend:** Next.js (React) with Tailwind CSS
* **Backend:** FastAPI (Python) with Mangum
* **Infrastructure:** AWS Lambda (Frankfurt - eu-central-1)
* **Governance:** Kiro-compliant steering and policy ledger

### Architecture
The system utilizes a "Heartbeat" mechanism where the frontend polls a sovereign AWS Lambda endpoint every 3 seconds to retrieve live drift variance.

---
*Developed for the 2026 Spec-Drift Competition.*
