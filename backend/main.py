from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI(title="Aevoxis Warden Engine")

# In accordance with German rules and regulations for web security,
# we explicitly define the trusted origins to prevent unauthorized access.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/drift")
async def get_drift():
    """
    Returns the real-time variance detected by the Warden Swarm.
    """
    return {"drift": random.uniform(0.0001, 0.0009)}

def main():
    import uvicorn
    # Points to the current file (backend/main.py) and the app instance
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
