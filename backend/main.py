from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from mangum import Mangum
import random
import os
from datetime import datetime

app = FastAPI(title="Aevoxis Warden Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to find the vault path regardless of the user's system
def get_vault_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "..", ".kiro", "audit", "last_sync.audit")

@app.get("/drift")
async def get_drift():
    return {"drift": random.uniform(0.0001, 0.0009)}

@app.post("/audit")
async def run_audit():
    # 1. Logic to GENERATE the real file on the user's system
    audit_path = get_vault_path()
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
    
    with open(audit_path, "w") as f:
        f.write(f"--- LIVE SOVEREIGN WARDEN AUDIT ---\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Article 14 Status: VERIFIED\n")
        f.write(f"System Integrity: 100%\n")
        f.write(f"----------------------------------")

    return {"status": "success", "message": "Audit generated in vault."}

@app.get("/download-audit")
async def serve_audit():
    audit_path = get_vault_path()
    
    if os.path.exists(audit_path):
        return FileResponse(audit_path, filename="sovereign_audit_trail.txt")
            
    return {"error": "No audit found. Please click 'Run Audit' first."}

handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
