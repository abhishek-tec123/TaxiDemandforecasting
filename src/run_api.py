from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor
import datetime
import fastapi
import os
import json
import logging
import asyncio

# Local imports
from app import Plot_logic, VALID_WEEKDAYS, forcast_logic
from get_loc_from_latlon import reverse_geocode_h3_list

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Matplotlib backend only when needed
import matplotlib
matplotlib.use('Agg')

# Paths
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.environ.get('TAXI_DATA_DIR', os.path.join(SRC_ROOT, 'parquet'))
DEFAULT_PLOT_DIR = os.environ.get('PLOT_DIR', os.path.join(SRC_ROOT, 'plot'))

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (plots/images)
app.mount("/files", StaticFiles(directory=DEFAULT_PLOT_DIR), name="files")

# Thread pool for async execution
executor = ThreadPoolExecutor()

# Input model
class MainRequest(BaseModel):
    weekday: str
    start_time: str
    end_time: str
    date: Optional[str] = None
    data_dir: Optional[str] = DEFAULT_DATA_DIR
    plot_dir: Optional[str] = DEFAULT_PLOT_DIR

    @validator("weekday")
    def validate_weekday(cls, v):
        if v.lower() not in VALID_WEEKDAYS:
            raise ValueError(f"weekday must be one of {VALID_WEEKDAYS}")
        return v.lower()

    @validator("date")
    def validate_date(cls, v):
        if v:
            try:
                datetime.datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date must be in YYYY-MM-DD format")
        return v

def get_forecast_summary() -> dict:
    path = os.path.join(DEFAULT_PLOT_DIR, "pickup_summary_forecasted.json")
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

# Optimize reverse geocode (can add external caching if needed)
def get_location_info_for_hexes(hex_ids: List[str]) -> Dict[str, Dict[str, str]]:
    try:
        location_results = reverse_geocode_h3_list(hex_ids)
        return {
            result['h3_id']: {
                'neighbourhood': result.get('neighbourhood', 'Unknown')
            } for result in location_results if 'h3_id' in result
        }
    except Exception as e:
        logger.error(f"Failed to get location info: {e}")
        return {hex_id: {'neighbourhood': 'Unknown'} for hex_id in hex_ids}

@app.post("/plot-graph")
async def run_main_api(req: MainRequest):
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, lambda: Plot_logic(
            weekday=req.weekday,
            start_time=req.start_time,
            end_time=req.end_time,
            data_dir=req.data_dir,
            plot_dir=req.plot_dir
        ))
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Unexpected error in /plot-graph")
        return {"error": str(e)}

@app.post("/forecast-logic")
async def run_forecast_api(req: MainRequest):
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, lambda: forcast_logic(
            weekday=req.weekday,
            start_time=req.start_time,
            end_time=req.end_time,
            data_dir=req.data_dir,
            plot_dir=req.plot_dir
        ))

        data = get_forecast_summary()
        forecast_next_week_data = []
        for parent in data.values():
            for child in parent.get("children", {}).values():
                hex_id = child.get("hex_id")
                entry = {
                    "hex_id": hex_id,
                    "forecast_next_week": child.get("forecast_next_week"),
                    "forecast_accuracy": child.get("forecast_accuracy"),
                }
                forecast_next_week_data.append(entry)

        valid_mape_hexes = [h for h in forecast_next_week_data if h.get("forecast_accuracy") is not None]
        best_mape_hexes = sorted(valid_mape_hexes, key=lambda x: x["forecast_next_week"], reverse=True)[:10]

        hex_ids = [hex_data["hex_id"] for hex_data in best_mape_hexes]
        location_info = get_location_info_for_hexes(hex_ids)

        for hex_data in best_mape_hexes:
            hex_data.update(location_info.get(hex_data["hex_id"], {'neighbourhood': 'Unknown'}))

        result["best_mape_hexes"] = best_mape_hexes
        return result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Unexpected error in /forecast-logic")
        return {"error": str(e)}

@app.get("/status")
def health_check():
    return {
        "status": "ok",
        "server": {
            "framework": "FastAPI",
            "fastapi_version": fastapi.__version__,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "environment": os.environ.get("ENV", "development")
        },
        "api": {
            "endpoints": [
                {"path": "/status", "method": "GET", "description": "Status check endpoint"},
                {"path": "/plot-graph", "method": "POST", "description": "Generate plots and summary for taxi pickups"},
                {"path": "/forecast-logic", "method": "POST", "description": "Generate forecasted plots and summary for taxi pickups"},
                {"path": "/files/{file_path}", "method": "GET", "description": "Serve static files from plot directory"}
            ]
        }
    }

# import json

# with open("/Users/abhishek/Desktop/Taxi Demand forecasting/src/plot/pickup_summary.json") as f:
#     data = json.load(f)

# total_pickups = sum(parent["total_pickups"] for parent in data.values())
# print("Total pickups from all hexes:", total_pickups)