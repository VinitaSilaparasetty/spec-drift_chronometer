# Aevoxis Warden Engine: Spec-Drift Chronometer

*Note: This project is currently under active development.*

## Project Overview
The **Aevoxis Warden Engine** is a sovereign monitoring system designed to detect and visualize temporal variance (Spec-Drift) in real-time. Built with a focus on security, transparency, and high-performance serverless architecture.

### Tech Stack
* **Frontend:** Next.js (React) with Tailwind CSS
* **Backend:** FastAPI (Python) with Mangum
* **Infrastructure:** AWS Lambda (Frankfurt - eu-central-1)
* **Governance:** Kiro-compliant steering and policy ledger

### Architecture
The system utilizes a "Heartbeat" mechanism where the frontend polls a sovereign AWS Lambda endpoint every 3 seconds to retrieve live drift variance.

Quick Start: Running the Demo
To experience the Spec-Drift Chronometer in action, follow these steps to initialize the governance layer and visualize architectural integrity.

1. Backend Initialization (The Warden Engine)
The backend is built with FastAPI and hosted on AWS Lambda via Mangum.

Navigate to the backend directory: cd backend

Install dependencies: pip install -r requirements.txt

Local Emulation: Use the SAM CLI or run the FastAPI server directly for testing:

Bash
uvicorn main:app --reload
Kiro Steering: Ensure your .kiro/steering vault is populated with your human-intent specifications. The engine will automatically bind these to the execution context.

2. Frontend Visualization (The Chronometer Dashboard)
The dashboard provides the real-time Drift Coefficient and the Justification Gate interface.

Navigate to the frontend directory: cd frontend

Install dependencies: npm install

Launch the Dashboard:

Bash
npm run dev
Access the UI: Open http://localhost:3000 in your browser.

3. Executing a Drift Audit
Once both layers are running:

Trigger a "Console Creep" event: Manually alter a resource in your AWS Sandbox (e.g., change an S3 bucket policy or an EC2 security group).

Run Audit: Click the "Run Audit" button on the dashboard. The Kiro Logic Engine will perform millisecond-latency reconciliation against the .kiro/steering vault.

The Justification Gate: If drift is detected, the AWS Bedrock-powered Gate will trigger. You must provide a business justification, which is then evaluated against EU AI Act Article 14 guardrails.

Download Trail: Click "Download Audit Trail" to export a deterministic record of the drift, the justification, and the governance decision for compliance reporting.

---
*Developed for the 2026 Spec-Drift Competition.*
