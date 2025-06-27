# # # import geopandas
# # # import geodatasets
# # # from h3Helper import plot_df, plot_shape, plot_cells
# # # import matplotlib.pyplot as plt
# # # import h3

# # # # Load and prepare the dataset
# # # df = geopandas.read_file(geodatasets.get_path('nybb'))
# # # df = df.to_crs(epsg=4326)

# # # # Plot the fourth borough's H3 cells
# # # geo = df.geometry[3]
# # # cells = h3.geo_to_cells(geo, res=8)  # Generates all 564 cells at resolution 9
# # # plot_cells(cells)  # Plots all cells
# # # plt.title("Fourth Borough's H3 Cells (Total: 564)")
# # # plt.show()
# # # print("Total H3 cells for the fourth borough:", len(cells))
# # # # Generate and count H3 cells for all boroughs
# # # cell_column = df.geometry.apply(lambda x: h3.geo_to_cells(x, res=8))
# # # print("H3 cells for all boroughs:", cell_column)
# # # print("Total H3 cells:", cell_column.count())

# # # # Plot all boroughs with names
# # # # plot_df(df, column='BoroName')
# # # # plt.title('New York Boroughs')
# # # # plt.show()



# # import geopandas
# # import geodatasets
# # from h3.h3Helper import plot_df, plot_shape, plot_cells
# # import folium
# # import h3

# # # Load and prepare the dataset
# # df = geopandas.read_file(geodatasets.get_path('nybb'))
# # df = df.to_crs(epsg=4326)

# # # Plot the fourth borough's H3 cells
# # geo = df.geometry[3]
# # cells = h3.geo_to_cells(geo, res=8)  # Generates all 564 cells at resolution 9

# # # Create a Folium map centered on the fourth borough
# # m = folium.Map(location=[geo.centroid.y, geo.centroid.x], zoom_start=12)

# # # Add H3 cells to the map
# # for cell in cells:
# #     hexagon = h3.cell_to_boundary(cell)
# #     folium.Polygon(
# #         locations=hexagon,
# #         color='blue',
# #         fill=True,
# #         fill_color='blue',
# #         fill_opacity=0.2,
# #         weight=0.5,
# #     ).add_to(m)

# # # Save the map to an HTML file
# # m.save('h3_cells_map.html')
# # print("Total H3 cells for the fourth borough:", len(cells))
# # print("Map saved to 'h3_cells_map.html'")

# # # Generate and count H3 cells for all boroughs
# # # cell_column = df.geometry.apply(lambda x: h3.geo_to_cells(x, res=8))
# # # print("H3 cells for all boroughs:", cell_column)
# # # print("Total H3 cells:", cell_column.count())

# import pandas as pd
# df = pd.read_csv("plot/filtered_df.csv", parse_dates=['tpep_pickup_datetime'])
# print(df['tpep_pickup_datetime'].dt.date.value_counts())
# print(df['tpep_pickup_datetime'].dt.date.unique())




# fast api code 

# import pandas as pd
# import os
# import json
# from plotONmapH3 import H3HexMap
# import sys
# from get_df_and_plot import extract_pickup_dataframe
# from fastapi import FastAPI, Query, HTTPException
# from pydantic import BaseModel, validator
# from typing import Optional
# import matplotlib
# matplotlib.use('Agg')
# from fastapi.staticfiles import StaticFiles
# import glob
# import datetime

# app = FastAPI()

# # Mount the plot directory to serve static files
# app.mount("/files", StaticFiles(directory="plot"), name="files")

# VALID_WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# class MainRequest(BaseModel):
#     weekday: str
#     start_time: str
#     end_time: str
#     date: Optional[str] = None  # Optional, for future extension
#     data_dir: Optional[str] = "/Users/abhishek/Desktop/Taxi Demand forecasting/src/data"
#     plot_dir: Optional[str] = "plot"

#     @validator("weekday")
#     def validate_weekday(cls, v):
#         if v.lower() not in VALID_WEEKDAYS:
#             raise ValueError(f"weekday must be one of {VALID_WEEKDAYS}")
#         return v.lower()

#     @validator("date")
#     def validate_date(cls, v):
#         if v is not None:
#             try:
#                 datetime.datetime.strptime(v, "%Y-%m-%d")
#             except ValueError:
#                 raise ValueError("date must be in YYYY-MM-DD format")
#         return v

# def run_main_logic(req: MainRequest):
#     main(
#         weekday=req.weekday,
#         start_time=req.start_time,
#         end_time=req.end_time,
#         data_dir=req.data_dir,
#         plot_dir=req.plot_dir
#     )
#     base_url = "http://localhost:8000/files"
#     # List all files in the plots directory
#     plots_dir_path = os.path.join(req.plot_dir, "plots")
#     plot_files = []
#     if os.path.exists(plots_dir_path):
#         for file_path in glob.glob(os.path.join(plots_dir_path, "*")):
#             filename = os.path.basename(file_path)
#             plot_files.append(f"{base_url}/plots/{filename}")
#     return {
#         "filtered_csv": f"{base_url}/filtered_df.csv",
#         "map_html": f"{base_url}/h3_hex_map.html",
#         "json_summary": f"{base_url}/pickup_summary.json",
#         "plots": plot_files
#     }

# @app.post("/run-main")
# def run_main_api(req: MainRequest):
#     try:
#         return run_main_logic(req)
#     except ValueError as ve:
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         return {"error": str(e)}

# def filter_taxi_data_by_time(
#     weekday: str,
#     start_time_str: str,
#     end_time_str: str,
#     data_dir: str = "/Users/abhishek/Desktop/Taxi Demand forecasting/src/data"
# ) -> pd.DataFrame:
#     input_file = os.path.join(data_dir, f"nyc_taxi_2016_Q1_{weekday}.csv")
#     if not os.path.exists(input_file):
#         raise FileNotFoundError(f"File not found: {input_file}")
#     print(f"Loading data from: {input_file}...")
#     df = pd.read_csv(input_file, parse_dates=['tpep_pickup_datetime'])
#     print(f"Loaded {len(df)} rows.")
#     start_time = pd.to_datetime(start_time_str).time()
#     end_time = pd.to_datetime(end_time_str).time()
#     df['pickup_time'] = df['tpep_pickup_datetime'].dt.time
#     filtered_df = df[df['pickup_time'].between(start_time, end_time)].copy()
#     print(f"Filtered {len(filtered_df)} rows between {start_time_str} and {end_time_str}.")
#     filtered_df.drop(columns=['pickup_time'], inplace=True)
#     del df
#     return filtered_df

# def save_dataframe_to_csv(df: pd.DataFrame, path: str):
#     df.to_csv(path, index=False)
#     print(f"DataFrame saved to {path}")

# def load_dataframe_from_csv(path: str) -> pd.DataFrame:
#     df = pd.read_csv(path, parse_dates=['tpep_pickup_datetime'])
#     print(f"DataFrame loaded from {path} ({len(df)} rows)")
#     return df

# def run_h3_pipeline(df: pd.DataFrame, map_path: str, json_path: str, resolution=8, borough_index=3):
#     h3_map = H3HexMap(resolution=resolution, borough_index=borough_index)
#     # Extract directory and filenames from the full paths
#     output_dir = os.path.dirname(map_path) if os.path.dirname(map_path) else '.'
#     map_filename = os.path.basename(map_path)
#     json_filename = os.path.basename(json_path)
    
#     json_result = h3_map.run_pipeline(df, output_dir=output_dir, map_filename=map_filename, json_filename=json_filename)
#     print(f"Map saved to {map_path}, JSON saved to {json_path}")
#     return json_result

# def cleanup_file(path: str):
#     try:
#         os.remove(path)
#         print(f"Deleted temporary file: {path}")
#     except Exception as e:
#         print(f"Could not delete {path}: {e}")
    
# def main(weekday="sat", start_time="13:30", end_time="14:00", data_dir="/Users/abhishek/Desktop/Taxi Demand forecasting/src/data", plot_dir="plot"):
#     try:
#         # Create plot directory if it doesn't exist
#         os.makedirs(plot_dir, exist_ok=True)
        
#         # Define file paths in the plot directory
#         filtered_csv_path = os.path.join(plot_dir, "filtered_df.csv")
#         map_path = os.path.join(plot_dir, "h3_hex_map.html")
#         json_path = os.path.join(plot_dir, "pickup_summary.json")
        
#         # Step 1: Filter and save the CSV file
#         print(f"Filtering data for {weekday} between {start_time} and {end_time}...")
#         filtered_df = filter_taxi_data_by_time(weekday, start_time, end_time, data_dir)
        
#         # Step 2: Save the filtered CSV file in plot directory
#         save_dataframe_to_csv(filtered_df, filtered_csv_path)
#         print(f"Filtered CSV file saved as: {filtered_csv_path}")
        
#         # Step 3: Use the saved CSV file for further processing
#         reloaded_df = load_dataframe_from_csv(filtered_csv_path)
#         run_h3_pipeline(reloaded_df, map_path, json_path)
#         del reloaded_df

#         # Step 4: Generate DataFrame and plots from the JSON result
#         with open(json_path, 'r') as f:
#             json_data = json.load(f)
#         df_pickup = extract_pickup_dataframe(json_data, plot=True, save_dir=plot_dir)
#         print("Plots generated and saved in the 'plots' subdirectory.")
#         print(f"All files saved in the '{plot_dir}' directory:")
#         print(f"  - Filtered CSV: {filtered_csv_path}")
#         print(f"  - Map HTML: {map_path}")
#         print(f"  - JSON summary: {json_path}")
#         print(f"  - Plots: {os.path.join(plot_dir, 'plots')}/")
        
#     except Exception as e:
#         print(f"Error: {e}", file=sys.stderr)
#         sys.exit(1)

# # if __name__ == "__main__":
# #     main()



import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt

# Input data
data = {
    "2016-01-01": 49,
    "2016-01-08": 111,
    "2016-01-15": 51,
    "2016-01-22": 52,
    "2016-01-29": 71,
    "2016-02-05": 41,
    "2016-02-12": 70,
    "2016-02-19": 47,
    "2016-02-26": 33,
    "2016-03-04": 49,
    "2016-03-11": 45,
    "2016-03-18": 49,
    "2016-03-25": 87
}

# Convert to time series
ts = pd.Series(data)
ts.index = pd.to_datetime(ts.index)

# Fit Holt-Winters (without seasonality)
model = ExponentialSmoothing(ts, trend="add", seasonal=None)
fit = model.fit()

# Forecast next value
forecast = fit.forecast(1)
print("Next week's forecast:", forecast.iloc[0])

# Optional: Plot the forecast
ts.plot(label="Observed", marker='o')
fit.fittedvalues.plot(label="Fitted", linestyle="--")
forecast.plot(label="Forecast", marker='X', color='red')
plt.legend()
plt.title("Holt Linear Trend Forecast")
plt.show()