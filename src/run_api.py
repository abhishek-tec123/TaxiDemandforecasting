from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from typing import Optional
import datetime
from app import Plot_logic, VALID_WEEKDAYS, forcast_logic
import matplotlib
import os
import fastapi

matplotlib.use('Agg')

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_DATA_DIR = os.environ.get('TAXI_DATA_DIR', os.path.join(SRC_ROOT, 'parquet'))
DEFAULT_PLOT_DIR = os.environ.get('PLOT_DIR', os.path.join(SRC_ROOT, 'plot'))

app = FastAPI()
app.mount("/files", StaticFiles(directory=DEFAULT_PLOT_DIR), name="files")

class MainRequest(BaseModel):
    weekday: str
    start_time: str
    end_time: str
    date: Optional[str] = None
    data_dir: Optional[str] = DEFAULT_DATA_DIR
    plot_dir: Optional[str] = DEFAULT_PLOT_DIR

    @validator("weekday")
    def validate_weekday(cls, v):
        print(f"[DEBUG] Validating weekday: {v}")
        if v.lower() not in VALID_WEEKDAYS:
            print(f"[ERROR] Invalid weekday: {v}")
            raise ValueError(f"weekday must be one of {VALID_WEEKDAYS}")
        return v.lower()

    @validator("date")
    def validate_date(cls, v):
        print(f"[DEBUG] Validating date: {v}")
        if v is not None:
            try:
                datetime.datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                print(f"[ERROR] Invalid date format: {v}")
                raise ValueError("date must be in YYYY-MM-DD format")
        return v

@app.post("/plot-graph")
def run_main_api(req: MainRequest):
    print(f"[DEBUG] /plot-graph called with: weekday='{req.weekday}' start_time='{req.start_time}' end_time='{req.end_time}' date={req.date} data_dir='{os.path.relpath(req.data_dir, SRC_ROOT)}' plot_dir='{os.path.relpath(req.plot_dir, SRC_ROOT)}'")
    try:
        result = Plot_logic(
            weekday=req.weekday,
            start_time=req.start_time,
            end_time=req.end_time,
            data_dir=req.data_dir,
            plot_dir=req.plot_dir
        )
        print(f"[DEBUG] /plot-graph result: {result}")
        return result
    except ValueError as ve:
        print(f"[ERROR] /plot-graph ValueError: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] /plot-graph Exception: {e}")
        return {"error": str(e)}

@app.post("/forecast-logic")
def run_forecast_api(req: MainRequest):
    print(f"[DEBUG] /forecast-logic called with: weekday='{req.weekday}' start_time='{req.start_time}' end_time='{req.end_time}' date={req.date} data_dir='{os.path.relpath(req.data_dir, SRC_ROOT)}' plot_dir='{os.path.relpath(req.plot_dir, SRC_ROOT)}'")
    try:
        result = forcast_logic(
            weekday=req.weekday,
            start_time=req.start_time,
            end_time=req.end_time,
            data_dir=req.data_dir,
            plot_dir=req.plot_dir
        )
        print(f"[DEBUG] /forecast-logic result: {result}")
        return result
    except ValueError as ve:
        print(f"[ERROR] /forecast-logic ValueError: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"[ERROR] /forecast-logic Exception: {e}")
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
                {"path": "/health", "method": "GET", "description": "Health check endpoint"},
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