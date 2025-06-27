import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[RUNNER] Starting FastAPI server at http://{host}:{port}")
    import uvicorn
    uvicorn.run("run_api:app", host=host, port=port, reload=True) 