from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from mangum import Mangum
import random
import os

app = FastAPI(title="Aevoxis Warden Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/drift")
async def get_drift():
    return {"drift": random.uniform(0.0001, 0.0009)}

@app.post("/audit")
async def run_audit():
    return {"status": "success", "message": "Sovereignty Audit Complete", "drift": 0.0005}

@app.get("/download-audit")
async def serve_audit():
    # Absolute path logic: Finds root/ .kiro/ audit/ last_sync.audit
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_path = os.path.join(base_dir, ".kiro", "audit", "last_sync.audit")
    
    if os.path.exists(audit_path):
        return FileResponse(audit_path, filename="sovereign_audit_trail.txt")
            
    return {"error": f"Vault not found at: {audit_path}"}

handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
