import pandas as pd
import geopandas as gpd
import geodatasets
import folium
import h3
from shapely.geometry import Point
from collections import defaultdict
import json
import os

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))

class H3HexMap:
    def __init__(self, resolution=8, borough_index=3):
        print(f"[DEBUG] Initializing H3HexMap with resolution={resolution}, borough_index={borough_index}")
        self.resolution = resolution
        self.parent_resolution = resolution - 1
        self.borough_index = borough_index
        self.borough_name = None
        self.borough_geo = None
        self.hex_cells = []
        self.filtered_points = pd.DataFrame()
        self.pickup_data = {}
        self.summary = {}

    def load_borough(self):
        print(f"[DEBUG] Loading borough with index {self.borough_index}")
        df = gpd.read_file(geodatasets.get_path('nybb'))
        df = df.to_crs(epsg=4326)
        self.borough_geo = df.geometry[self.borough_index]
        self.borough_name = df.BoroName[self.borough_index]
        print(f"[DEBUG] Loaded borough: {self.borough_name}")
        return self.borough_geo

    def filter_pickups_in_borough(self, df):
        print(f"[DEBUG] Filtering pickups in borough...")
        self.load_borough()
        geometry = gpd.GeoSeries([Point(xy) for xy in zip(df.pickup_longitude, df.pickup_latitude)], crs='EPSG:4326')
        df['geometry'] = geometry
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        self.filtered_points = gdf[gdf.geometry.within(self.borough_geo)]
        print(f"[DEBUG] Selected Borough: {self.borough_name}")
        print(f"[DEBUG] Filtered {len(self.filtered_points)} pickup points within {self.borough_name}")
        return self.filtered_points

    def generate_hexagons(self):
        print(f"[DEBUG] Generating hexagons for borough...")
        self.hex_cells = list(h3.geo_to_cells(self.borough_geo, res=self.resolution))
        print(f"[DEBUG] Generated {len(self.hex_cells)} hex cells.")
        return self.hex_cells

    def assign_hex_ids_to_points(self):
        print(f"[DEBUG] Assigning hex IDs to points...")
        self.filtered_points['hex_id'] = self.filtered_points.apply(
            lambda row: h3.latlng_to_cell(row.pickup_latitude, row.pickup_longitude, self.resolution), axis=1
        )
        self.filtered_points['date'] = pd.to_datetime(self.filtered_points['tpep_pickup_datetime']).dt.date
        print(f"[DEBUG] Assigned hex IDs and extracted dates.")
        return self.filtered_points

    def build_pickup_summary(self):
        print(f"[DEBUG] Building pickup summary...")
        parent_child_data = defaultdict(lambda: {
            "parent_id": None,
            "children": {},
            "total_pickups": 0,
            "total_area_km2": 0,
        })

        for hex_id in self.hex_cells:
            centroid = h3.cell_to_latlng(hex_id)
            area_km2 = h3.cell_area(hex_id, unit='km^2')
            parent_id = h3.cell_to_parent(hex_id, self.parent_resolution)

            df_hex = self.filtered_points[self.filtered_points['hex_id'] == hex_id]
            pickup_count = len(df_hex)
            date_counts = df_hex.groupby('date').size().to_dict()

            parent_data = parent_child_data[parent_id]
            parent_data['parent_id'] = parent_id
            parent_data['total_pickups'] += pickup_count
            parent_data['total_area_km2'] = round(h3.cell_area(parent_id, unit='km^2'), 4)
            parent_data['children'][hex_id] = {
                "centroid": list(centroid),
                "area_km2": round(area_km2, 4),
                "pickup_count": pickup_count,
                "pickups_by_date": {str(k): int(v) for k, v in date_counts.items()}
            }

        self.pickup_data = parent_child_data
        print(f"[DEBUG] Built pickup summary for {len(parent_child_data)} parent hexes.")
        return self.pickup_data

    def restructure_json_output(self):
        print(f"[DEBUG] Restructuring JSON output...")
        output = {}
        for i, (parent_id, pdata) in enumerate(self.pickup_data.items(), 1):
            children = {}
            for j, (hex_id, cdata) in enumerate(pdata["children"].items(), 1):
                children[f"child_{j}"] = {
                    "hex_id": hex_id,
                    **cdata
                }

            output[f"parent_{i}"] = {
                "parent_id": parent_id,
                "total_pickups": pdata["total_pickups"],
                "total_area_km2": round(pdata["total_area_km2"], 4),
                "children": children
            }

        print(f"[DEBUG] Restructured JSON output with {len(output)} parents.")
        return output

    def generate_map(self):
        print(f"[DEBUG] Generating folium map...")
        m = folium.Map(location=[self.borough_geo.centroid.y, self.borough_geo.centroid.x], zoom_start=12)

        for parent_id, pdata in self.pickup_data.items():
            parent_centroid = h3.cell_to_latlng(parent_id)

            # Parent Marker
            popup_html = f"""
            <b>Parent Hex ID:</b> {parent_id}<br>
            <b>Total Pickups:</b> {pdata['total_pickups']}<br>
            <b>Area (km²):</b> {pdata['total_area_km2']}
            """
            folium.Marker(
                location=parent_centroid,
                icon=folium.Icon(color='green', icon='cloud'),
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

            # Parent Hex Outline
            folium.Polygon(
                locations=h3.cell_to_boundary(parent_id),
                color='green',
                fill=False,
                weight=2
            ).add_to(m)

            for hex_id, cdata in pdata['children'].items():
                # Child Hex Fill
                folium.Polygon(
                    locations=h3.cell_to_boundary(hex_id),
                    color='blue',
                    fill=True,
                    fill_opacity=0.2,
                    weight=1
                ).add_to(m)

                # Child Popup
                child_popup = f"""
                <b>Child Hex ID:</b> {hex_id}<br>
                <b>Area (km²):</b> {cdata['area_km2']}<br>
                <b>Pickup Count:</b> {cdata['pickup_count']}<br>
                <b>Pickups by Date:</b><br>
                """
                if cdata['pickups_by_date']:
                    for date, count in cdata['pickups_by_date'].items():
                        child_popup += f"&nbsp;&nbsp;• {date}: {count}<br>"
                else:
                    child_popup += "None<br>"

                folium.Marker(
                    location=cdata['centroid'],
                    icon=folium.Icon(color='blue', icon='info-sign'),
                    popup=folium.Popup(child_popup, max_width=300)
                ).add_to(m)

        return m

    def save_map(self, map_object, output_path='h3_hex_map.html'):
        print(f"Attempting to save map to: {os.path.relpath(output_path, SRC_ROOT)}")
        try:
            map_object.save(output_path)
            print(f"Map successfully saved to {os.path.relpath(output_path, SRC_ROOT)}")
        except Exception as e:
            print(f"Failed to save map: {e}")
        self.summary = {
            "borough": self.borough_name,
            "total_hexes": len(self.hex_cells),
            "output_map": os.path.relpath(output_path, SRC_ROOT)
        }

    def export_json(self, filepath='pickup_summary.json'):
        print(f"[DEBUG] Exporting JSON to {os.path.relpath(filepath, SRC_ROOT)}")
        structured_output = self.restructure_json_output()
        try:
            with open(filepath, 'w') as f:
                json.dump(structured_output, f, indent=2)
            print(f"JSON result saved to {os.path.relpath(filepath, SRC_ROOT)}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")

    def run_pipeline(self, df, output_dir='plot', map_filename='h3_hex_map.html', json_filename='pickup_summary.json'):
        print(f"[DEBUG] Running H3HexMap pipeline...")
        os.makedirs(output_dir, exist_ok=True)
        map_path = os.path.join(output_dir, map_filename)
        json_path = os.path.join(output_dir, json_filename)
        self.filter_pickups_in_borough(df)
        self.generate_hexagons()
        self.assign_hex_ids_to_points()
        self.build_pickup_summary()
        m = self.generate_map()
        self.save_map(m, output_path=map_path)
        self.export_json(filepath=json_path)
        print(f"[DEBUG] Pipeline complete. Returning structured JSON output.")
        return self.restructure_json_output()

    def get_demand_dataframe(self):
        print(f"[DEBUG] Creating demand DataFrame from pickup data...")
        records = []
        for parent_id, pdata in self.pickup_data.items():
            for hex_id, cdata in pdata["children"].items():
                for date, count in cdata["pickups_by_date"].items():
                    records.append({
                        "parent_id": parent_id,
                        "hex_id": hex_id,
                        "date": date,
                        "pickup_count": count,
                        "centroid_lat": cdata["centroid"][0],
                        "centroid_lng": cdata["centroid"][1],
                        "area_km2": cdata["area_km2"]
                    })
        df = pd.DataFrame(records)
        print(f"[DEBUG] Created demand DataFrame with {len(df)} rows.")
        return df

# # Load taxi data
# df = pd.read_csv("/Users/abhishek/Desktop/Taxi Demand forecasting/src/plot/filtered_df.csv")

# # Initialize and run
# hex_map = H3HexMap(resolution=8, borough_index=3)  # Manhattan
# json_result = hex_map.run_pipeline(df)

# # View final structured JSON
# print(json.dumps(json_result, indent=2))

# # Create and show demand DataFrame

# # demand_df = hex_map.get_demand_dataframe()
# print(demand_df.head())

# # demand_df.to_csv('demand_by_hex_and_time.csv', index=False)
# print('Demand DataFrame saved to demand_by_hex_and_time.csv')



import folium
import h3
import json

def generate_map_from_json_with_forcast(json_data):
    print(f"[DEBUG] Generating map from JSON with forecast...")
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
            locations=h3.cell_to_boundary(parent_hex),
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
                locations=h3.cell_to_boundary(hex_id),
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
