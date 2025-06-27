import folium
import h3
import json

def generate_map_from_json_with_forcast(json_data):
    # Estimate a center from the first parent hex
    first_parent_id = next(iter(json_data))
    center_latlng = h3.cell_to_latlng(json_data[first_parent_id]["parent_id"])

    # Initialize map
    m = folium.Map(location=center_latlng, zoom_start=12)

    for parent_id, pdata in json_data.items():
        parent_hex = pdata["parent_id"]
        parent_centroid = h3.cell_to_latlng(parent_hex)

        # Parent Marker
        popup_html = f"""
        <b>Parent Hex ID:</b> {parent_hex}<br>
        <b>Total Pickups:</b> {pdata['total_pickups']}<br>
        <b>Total Area (km²):</b> {pdata['total_area_km2']}
        """
        folium.Marker(
            location=parent_centroid,
            icon=folium.Icon(color='green', icon='cloud'),
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

        # Parent Hex Polygon
        folium.Polygon(
            locations=[[lat, lng] for lng, lat in h3.cell_to_boundary(parent_hex)],
            color='green',
            fill=False,
            weight=2
        ).add_to(m)

        # Children hexes
        for _, child in pdata["children"].items():
            hex_id = child["hex_id"]
            centroid = child["centroid"]
            forecast = child.get("forecast_next_week", "N/A")

            # Child Polygon
            folium.Polygon(
                locations=[[lat, lng] for lng, lat in h3.cell_to_boundary(hex_id)],
                color='blue',
                fill=True,
                fill_opacity=0.2,
                weight=1
            ).add_to(m)

            # Child Popup
            popup = f"""
            <b>Child Hex ID:</b> {hex_id}<br>
            <b>Area (km²):</b> {child['area_km2']}<br>
            <b>Pickup Count:</b> {child['pickup_count']}<br>
            <b>Forecast Next Week:</b> {forecast}<br>
            <b>Pickups by Date:</b><br>
            """

            if child["pickups_by_date"]:
                for date, count in child["pickups_by_date"].items():
                    popup += f"&nbsp;&nbsp;• {date}: {count}<br>"
            else:
                popup += "None<br>"

            folium.Marker(
                location=centroid,
                icon=folium.Icon(color='blue', icon='info-sign'),
                popup=folium.Popup(popup, max_width=300)
            ).add_to(m)

    return m


# with open("/Users/abhishek/Desktop/Taxi Demand forecasting/src/plot/pickup_summary_forecasted.json") as f:
#     data = json.load(f)

# map_ = generate_map_from_json_with_forcast(data)
# map_.save("/Users/abhishek/Desktop/Taxi Demand forecasting/h3/pickup_forecast_map.html")


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def extract_pickup_dataframe_with_forecast(json_data, plot=True, save_dir="plot"):
    rows = []

    for parent in json_data.values():
        for child in parent.get("children", {}).values():
            hex_id = child.get("hex_id")
            pickups = child.get("pickups_by_date", {})
            forecast = child.get("forecast_next_week")

            # Add actual pickups
            for date, count in pickups.items():
                rows.append({
                    "child_hex": hex_id,
                    "pickup_date": date,
                    "pickup_count": count,
                    "is_forecast": False
                })

            # Add forecast if available
            if forecast is not None and pickups:
                latest_date = pd.to_datetime(max(pickups.keys()))
                forecast_date = latest_date + pd.Timedelta(days=7)  # Assume weekly frequency
                rows.append({
                    "child_hex": hex_id,
                    "pickup_date": forecast_date.strftime("%Y-%m-%d"),
                    "pickup_count": forecast,
                    "is_forecast": True
                })

    df = pd.DataFrame(rows)
    df["pickup_date"] = pd.to_datetime(df["pickup_date"])
    pivot_df = df.pivot(index='child_hex', columns='pickup_date', values='pickup_count')
    pivot_df = pivot_df.fillna(0).astype(int)

    if plot:
        plots_subdir = os.path.join(save_dir, "plots")
        os.makedirs(plots_subdir, exist_ok=True)

        # Plot: Pickup trend for top 3 busiest hexes including forecast
        top_hexes = pivot_df.sum(axis=1).sort_values(ascending=False).head(3).index
        plt.figure(figsize=(12, 6))
        for hex_id in top_hexes:
            series = pivot_df.loc[hex_id]
            series.plot(label=hex_id)

            # Highlight forecast point
            forecast_point = df[(df["child_hex"] == hex_id) & (df["is_forecast"])]
            if not forecast_point.empty:
                f_date = forecast_point["pickup_date"].values[0]
                f_count = forecast_point["pickup_count"].values[0]
                plt.scatter(f_date, f_count, color='red', label=f"{hex_id} Forecast", zorder=5)

        plt.title("Pickup Trend Over Time (Top 3 Hexes with Forecast)")
        plt.ylabel("Pickup Count")
        plt.xlabel("Date")
        plt.xticks(rotation=45)
        plt.legend(title="Child Hex")
        plt.tight_layout()
        plt.savefig(f"{plots_subdir}/pickup_trend_top3_hexes_with_forecast.png", dpi=300)
        plt.close()

        # # Plot: Heatmap of all hexes
        # plt.figure(figsize=(20, 12))
        # sns.heatmap(pivot_df, cmap="YlGnBu", cbar_kws={'label': 'Pickup Count'})
        # plt.title("Heatmap of Pickups by Child Hex and Date (with Forecast)")
        # plt.ylabel("Child Hex")
        # plt.xlabel("Pickup Date")
        # plt.tight_layout()
        # plt.savefig(f"{plots_subdir}/heatmap_all_hexes_with_forecast.png", dpi=300)
        # plt.close()

    return pivot_df

import json
# Path to your forecasted JSON
json_path = "/Users/abhishek/Desktop/Taxi Demand forecasting/src/plot/pickup_summary_forecasted.json"

# Load JSON
with open(json_path, 'r') as f:
    data = json.load(f)

# Call the function and generate plots
pivot_df = extract_pickup_dataframe_with_forecast(data, plot=True, save_dir="/Users/abhishek/Desktop/Taxi Demand forecasting/h3")
