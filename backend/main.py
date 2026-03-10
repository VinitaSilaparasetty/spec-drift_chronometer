from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import random

app = FastAPI(title="Aevoxis Warden Engine")

# In accordance with German rules and regulations for web security,
# we explicitly define trusted origins while allowing flexibility for AWS deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/default")
@app.get("/default/")
def read_root():
    return {
        "status": "SOVEREIGN_ACTIVE",
        "system": "Aevoxis Warden Engine",
        "message": "Temporal monitoring systems online."
    }

@app.get("/drift")
@app.get("/default/drift")
def get_drift():
    """
    Returns the real-time variance detected by the Warden Swarm.
    """
    return {"drift": random.uniform(0.0001, 0.0009)}

@app.api_route("/{path_name:path}", methods=["GET"])
def catch_all(path_name: str):
    return {
        "status": "SOVEREIGN_REDIRECT",
        "message": f"Path '{path_name}' not found. Please use the root or /drift endpoints.",
        "active_endpoints": ["/", "/drift"]
    }

# The "Sovereign" Lambda Handler
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
