from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import random

app = FastAPI(title="Aevoxis Warden Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"drift": random.uniform(0.0001, 0.0009)}

@app.api_route("/{path_name:path}", methods=["GET"])
def catch_all(path_name: str):
    return {
        "status": "SOVEREIGN_REDIRECT",
        "message": f"Path '{path_name}' not found.",
        "active_endpoints": ["/", "/drift"]
    }

# This MUST be at the base level of the file
handler = Mangum(app)
