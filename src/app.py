import os
import pandas as pd
import json
import glob
from plotONmapH3 import H3HexMap, generate_map_from_json_with_forcast
from get_df_and_plot import extract_pickup_dataframe
from forcast import add_forecast_to_json
from dotenv import load_dotenv
load_dotenv()

DEFAULT_DATA_DIR = os.environ.get('TAXI_DATA_DIR', os.path.join(os.path.dirname(__file__), 'parquet'))
DEFAULT_PLOT_DIR = os.environ.get('PLOT_DIR', os.path.join(os.path.dirname(__file__), 'plot'))
SRC_ROOT = os.path.dirname(os.path.abspath(__file__))

VALID_WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
BASE_URL = os.environ.get('BASE_URL')

def filter_taxi_data_by_time(weekday, start_time_str, end_time_str, data_dir):
    parquet_file = os.path.join(data_dir, f"nyc_taxi_2016_Q1_{weekday}.parquet")
    input_file = os.path.join(data_dir, f"nyc_taxi_2016_Q1_{weekday}.csv")
    print(f"[DEBUG] Looking for Parquet: {os.path.relpath(parquet_file, SRC_ROOT)}")
    print(f"[DEBUG] Looking for CSV: {os.path.relpath(input_file, SRC_ROOT)}")
    if os.path.exists(parquet_file):
        print(f"[DEBUG] Reading Parquet file: {os.path.relpath(parquet_file, SRC_ROOT)}")
        df = pd.read_parquet(parquet_file)
    elif os.path.exists(input_file):
        print(f"[DEBUG] Reading CSV file: {os.path.relpath(input_file, SRC_ROOT)}")
        df = pd.read_csv(input_file, parse_dates=['tpep_pickup_datetime'])
    else:
        raise FileNotFoundError(f"File not found: {os.path.relpath(parquet_file, SRC_ROOT)} or {os.path.relpath(input_file, SRC_ROOT)}")
    # Ensure datetime type
    if 'tpep_pickup_datetime' in df.columns:
        print(f"[DEBUG] Converting 'tpep_pickup_datetime' to datetime")
        df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    start_time = pd.to_datetime(start_time_str).time()
    end_time = pd.to_datetime(end_time_str).time()
    print(f"[DEBUG] Filtering between {start_time} and {end_time}")
    df['pickup_time'] = df['tpep_pickup_datetime'].dt.time
    filtered_df = df[df['pickup_time'].between(start_time, end_time)].copy()
    print(f"[DEBUG] Filtered rows: {len(filtered_df)}")
    filtered_df.drop(columns=['pickup_time'], inplace=True)
    return filtered_df

def save_dataframe_to_csv(df, path):
    df.to_csv(path, index=False)

def load_dataframe_from_csv(path):
    parquet_path = path.replace('.csv', '.parquet')
    print(f"[DEBUG] Attempting to load Parquet: {os.path.relpath(parquet_path, SRC_ROOT)}")
    if os.path.exists(parquet_path):
        print(f"[DEBUG] Reading Parquet file: {os.path.relpath(parquet_path, SRC_ROOT)}")
        df = pd.read_parquet(parquet_path)
        if 'tpep_pickup_datetime' in df.columns:
            print(f"[DEBUG] Converting 'tpep_pickup_datetime' to datetime")
            df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
        return df
    print(f"[DEBUG] Reading CSV file: {os.path.relpath(path, SRC_ROOT)}")
    return pd.read_csv(path, parse_dates=['tpep_pickup_datetime'])

def run_h3_pipeline(df, map_path, json_path, resolution=8, borough_index=3):
    h3_map = H3HexMap(resolution=resolution, borough_index=borough_index)
    return h3_map.run_pipeline(df, output_dir=os.path.dirname(map_path), map_filename=os.path.basename(map_path), json_filename=os.path.basename(json_path))

def get_plot_file_urls(plot_dir, base_url=BASE_URL):
    plots_dir_path = os.path.join(plot_dir, "plots")
    if not os.path.exists(plots_dir_path):
        return []
    return [
        f"{base_url}/plots/{os.path.basename(f)}"
        for f in glob.glob(os.path.join(plots_dir_path, "*"))
    ]

def Plot_logic(weekday, start_time, end_time, data_dir, plot_dir):
    os.makedirs(plot_dir, exist_ok=True)
    filtered_csv_path = os.path.join(plot_dir, "filtered_df.csv")
    map_path = os.path.join(plot_dir, "h3_hex_map.html")
    json_path = os.path.join(plot_dir, "pickup_summary.json")

    filtered_df = filter_taxi_data_by_time(weekday, start_time, end_time, data_dir)
    save_dataframe_to_csv(filtered_df, filtered_csv_path)

    reloaded_df = load_dataframe_from_csv(filtered_csv_path)
    run_h3_pipeline(reloaded_df, map_path, json_path)

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    extract_pickup_dataframe(json_data, plot=True, save_dir=os.path.relpath(plot_dir, SRC_ROOT))

    plot_files = get_plot_file_urls(plot_dir)

    return {
        "filtered_csv": f"{BASE_URL}/filtered_df.csv",
        "map_html": f"{BASE_URL}/h3_hex_map.html",
        "json_summary": f"{BASE_URL}/pickup_summary.json",
        "plots": plot_files
    }

def forcast_logic(weekday, start_time, end_time, data_dir, plot_dir):
    os.makedirs(plot_dir, exist_ok=True)
    filtered_csv_path = os.path.join(plot_dir, "filtered_df.csv")
    map_path = os.path.join(plot_dir, "h3_hex_map.html")
    json_path = os.path.join(plot_dir, "pickup_summary.json")

    filtered_df = filter_taxi_data_by_time(weekday, start_time, end_time, data_dir)
    save_dataframe_to_csv(filtered_df, filtered_csv_path)

    reloaded_df = load_dataframe_from_csv(filtered_csv_path)
    run_h3_pipeline(reloaded_df, map_path, json_path)

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    extract_pickup_dataframe(json_data, plot=True, save_dir=os.path.relpath(plot_dir, SRC_ROOT))

    # Add forecasted values to JSON and save as new file
    forecasted_json_path = add_forecast_to_json(json_path, weekday=weekday)
    with open(forecasted_json_path, 'r') as f:
        forecasted_json_data = json.load(f)

    forcastedH3ap = generate_map_from_json_with_forcast(forecasted_json_data)
    
    forecasted_map_path = os.path.join(plot_dir, "h3_hex_map_forecasted.html")
    forcastedH3ap.save(forecasted_map_path)

    plot_files = get_plot_file_urls(plot_dir)

    return {
        "filtered_csv": f"{BASE_URL}/filtered_df.csv",
        "map_html": f"{BASE_URL}/h3_hex_map.html",
        "json_summary": f"{BASE_URL}/pickup_summary.json",
        "json_forecasted": f"{BASE_URL}/{os.path.basename(forecasted_json_path)}",
        "map_html_forecasted": f"{BASE_URL}/h3_hex_map_forecasted.html",
        "plots": plot_files
    }