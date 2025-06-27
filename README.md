# Taxi Demand Forecasting

This project forecasts taxi demand in New York City using spatial hexagonal binning (H3) and time series forecasting. It provides an API and visualization tools for analyzing and predicting taxi pickup demand by location and time.

## Features
- Spatial binning of NYC taxi data using H3 hexagons
- Time-based filtering and aggregation
- Forecasting with Holt-Winters Exponential Smoothing
- Interactive map visualizations
- FastAPI-based API for integration and deployment

## Directory Structure
```
├── h3/                # H3 utilities and visualization helpers
├── src/
│   ├── app.py         # Main application logic
│   ├── forcast.py     # Forecasting functions
│   ├── get_df_and_plot.py # Data extraction and plotting
│   ├── plotONmapH3.py # H3 hex map generation
│   ├── run_api.py     # FastAPI server
│   ├── data/          # (gitignored) Raw taxi data CSVs
│   └── plot/          # (gitignored) Output plots and results
├── requirements.txt   # Python dependencies
├── .gitignore         # Git ignore rules
└── README.md          # Project documentation
```

## Setup
1. **Clone the repository:**
   ```bash
git clone <your-repo-url>
cd Taxi-Demand-forecasting
```
2. **Create a virtual environment and install dependencies:**
   ```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. **Add NYC taxi data:**
   - Place the required CSV files in `src/data/` (these are gitignored due to size).

## Usage
- **Run the API server:**
  ```bash
  cd src
  uvicorn run_api:app --reload
  ```
- **Access the API:**
  - Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

- **Generate visualizations:**
  - Use the scripts in `src/` or the API endpoints to generate maps and forecasts. Output will be saved in `src/plot/`.

## Deployment
- Ensure only code and configuration files are committed (data and outputs are gitignored).
- Deploy using any platform that supports FastAPI (e.g., Heroku, AWS, Azure, etc.).

## Notes
- Large data files and generated outputs are excluded from git for performance and storage reasons.
- For any issues, please open an issue or contact the maintainer. 