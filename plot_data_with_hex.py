# import pandas as pd
# import geopandas as gpd
# import geodatasets
# import folium
# import h3
# from shapely.geometry import Point
# from collections import defaultdict
# from datetime import datetime


# def load_pickup_points_within_borough(csv_path, borough_geom):
#     """
#     Load pickup points from CSV and return a GeoDataFrame of points within the borough geometry.
#     """
#     df = pd.read_csv(csv_path, parse_dates=['tpep_pickup_datetime'])
#     df = df.dropna(subset=['pickup_latitude', 'pickup_longitude'])

#     gdf = gpd.GeoDataFrame(
#         df,
#         geometry=gpd.points_from_xy(df['pickup_longitude'], df['pickup_latitude']),
#         crs='EPSG:4326'
#     )

#     # Filter points within borough
#     gdf_filtered = gdf[gdf.within(borough_geom)].copy()
#     print(f"Filtered {len(gdf_filtered)} pickup points within borough.")
#     return gdf_filtered


# def generate_hex_map_with_details(
#     resolution=8,
#     output_path='h3_hex_with_pickup_details.html',
#     borough_index=3,
#     pickup_csv_path=None
# ):
#     # Load borough geometry
#     boroughs = gpd.read_file(geodatasets.get_path('nybb')).to_crs(epsg=4326)
#     borough_geom = boroughs.geometry[borough_index]
#     borough_name = boroughs.BoroName[borough_index]

#     # Get all H3 child cells covering the borough
#     child_cells = h3.geo_to_cells(borough_geom, res=resolution)
#     parent_cells = set()
#     parent_child_map = defaultdict(list)
#     hex_pickup_map = defaultdict(list)

#     for child in child_cells:
#         parent = h3.cell_to_parent(child, resolution - 1)
#         parent_cells.add(parent)
#         parent_child_map[parent].append(child)

#     # Load pickup data within borough
#     if pickup_csv_path:
#         pickups = load_pickup_points_within_borough(pickup_csv_path, borough_geom)
#         # Assign each pickup to a child hex
#         for idx, row in pickups.iterrows():
#             lat, lon = row['pickup_latitude'], row['pickup_longitude']
#             pickup_time = row['tpep_pickup_datetime']
#             h3_cell = h3.latlng_to_cell(lat, lon, resolution)
#             if h3_cell in child_cells:
#                 hex_pickup_map[h3_cell].append(pickup_time)

#     # Create Folium map
#     center = [borough_geom.centroid.y, borough_geom.centroid.x]
#     m = folium.Map(location=center, zoom_start=12)

#     print(f"\n--- Hexagon Details for Borough: {borough_name} ---")
#     for i, child in enumerate(child_cells, 1):
#         centroid = h3.cell_to_latlng(child)
#         area = h3.cell_area(child, unit='km^2')
#         parent = h3.cell_to_parent(child, resolution - 1)
#         child_count = len(parent_child_map[parent])
#         pickups_in_cell = hex_pickup_map.get(child, [])
#         pickup_count = len(pickups_in_cell)
#         pickup_dates = sorted(set([dt.date() for dt in pickups_in_cell]))

#         # Print detailed info
#         print(f"\nHexagon {i}:")
#         print(f"  H3 Child Index: {child}")
#         print(f"  Parent Index:   {parent}")
#         print(f"  Area (km²):     {area:.4f}")
#         print(f"  Num Pickups:    {pickup_count}")
#         if pickup_count:
#             print(f"  Pickup Dates:   {', '.join(str(d) for d in pickup_dates)}")
#         else:
#             print("  Pickup Dates:   None")

#         # Add to map
#         hex_boundary = h3.cell_to_boundary(child)
#         popup_text = f"""
#         <b>Child H3:</b> {child}<br>
#         <b>Parent:</b> {parent}<br>
#         <b>Area:</b> {area:.4f} km²<br>
#         <b>Pickups:</b> {pickup_count}<br>
#         <b>Dates:</b> {'; '.join(str(d) for d in pickup_dates) if pickup_dates else 'None'}
#         """

#         folium.Polygon(
#             locations=hex_boundary,
#             color='blue',
#             fill=True,
#             fill_color='blue',
#             fill_opacity=0.3,
#             weight=0.5,
#             popup=folium.Popup(popup_text, max_width=300)
#         ).add_to(m)

#     # Add parent hex boundaries
#     for parent in parent_cells:
#         parent_boundary = h3.cell_to_boundary(parent)
#         folium.Polygon(
#             locations=parent_boundary,
#             color='green',
#             fill=False,
#             weight=2,
#         ).add_to(m)

#     m.save(output_path)
#     print(f"\nMap saved to: {output_path}")


# # Example usage
# if __name__ == "__main__":
#     generate_hex_map_with_details(
#         resolution=8,
#         output_path='h3_hex_with_pickup_details.html',
#         borough_index=3,  # Manhattan
#         pickup_csv_path='/Users/abhishek/Desktop/Taxi Demand forecasting/src/filtered_taxi_data.csv'  # Replace with your actual CSV path
#     )


# pick counts for saprate dates

# import pandas as pd
# import geopandas as gpd
# import geodatasets
# import folium
# import h3
# from collections import defaultdict
# from shapely.geometry import Point

# def generate_hex_map_with_pickups(pickup_csv, resolution=8, output_path='h3_pickup_map.html', borough_index=3):
#     # Load NYC borough geometry
#     df = gpd.read_file(geodatasets.get_path('nybb')).to_crs(epsg=4326)
#     borough_geom = df.geometry[borough_index]
#     borough_name = df.BoroName[borough_index]
#     print(f"Selected Borough: {borough_name}")

#     # Load pickup data
#     data = pd.read_csv(pickup_csv, parse_dates=['tpep_pickup_datetime'])
#     data = data.rename(columns={'pickup_latitude': 'lat', 'pickup_longitude': 'lon'})
#     data.dropna(subset=['lat', 'lon'], inplace=True)

#     # Convert to GeoDataFrame and filter points within borough
#     gdf_points = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.lon, data.lat), crs="EPSG:4326")
#     gdf_points = gdf_points[gdf_points.geometry.within(borough_geom)]
#     print(f"Filtered {len(gdf_points)} pickup points within {borough_name}")

#     # Generate H3 hexagons for borough
#     h3_cells = h3.geo_to_cells(borough_geom.__geo_interface__, res=resolution)
#     parent_child_map = defaultdict(list)
#     parent_counts = defaultdict(int)

#     # Group pickup points into hexagons
#     hex_pickup_data = defaultdict(list)  # {hex_id: [(datetime), ...]}

#     for _, row in gdf_points.iterrows():
#         hex_id = h3.latlng_to_cell(row['lat'], row['lon'], resolution)
#         hex_pickup_data[hex_id].append(row['tpep_pickup_datetime'])

#     # Folium map
#     m = folium.Map(location=[borough_geom.centroid.y, borough_geom.centroid.x], zoom_start=12)

#     print("\nHexagon Details:")

#     for i, hex_id in enumerate(h3_cells, 1):
#         centroid = h3.cell_to_latlng(hex_id)
#         area = h3.cell_area(hex_id, unit='km^2')
#         parent_id = h3.cell_to_parent(hex_id, resolution - 1)
#         parent_centroid = h3.cell_to_latlng(parent_id)
#         parent_area = h3.cell_area(parent_id, unit='km^2')
#         parent_counts[parent_id] += 1
#         parent_child_map[parent_id].append(hex_id)

#         pickups = hex_pickup_data.get(hex_id, [])
#         pickup_count = len(pickups)
#         pickup_by_date = defaultdict(int)
#         for dt in pickups:
#             pickup_by_date[dt.date()] += 1

#         print(f"\nHexagon {i}:")
#         print(f"  Hex ID:           {hex_id}")
#         print(f"  Parent ID:        {parent_id}")
#         print(f"  Centroid:         {centroid}")
#         print(f"  Area (km²):       {area:.4f}")
#         print(f"  Pickup Count:     {pickup_count}")
#         print(f"  Pickups by Date:")
#         for date in sorted(pickup_by_date):
#             print(f"    {date}: {pickup_by_date[date]}")

#         # Add child hexagon
#         folium.Polygon(
#             locations=h3.cell_to_boundary(hex_id),
#             color='blue',
#             fill=True,
#             fill_opacity=0.3,
#             weight=0.5
#         ).add_to(m)

#         # Add parent hexagon (only once)
#         if parent_id not in parent_child_map:
#             folium.Polygon(
#                 locations=h3.cell_to_boundary(parent_id),
#                 color='green',
#                 fill=False,
#                 weight=1.5
#             ).add_to(m)

#         # Marker with popup
#         popup_html = f"""
#         <b>Child H3:</b> {hex_id}<br>
#         <b>Parent:</b> {parent_id}<br>
#         <b>Area:</b> {area:.4f} km²<br>
#         <b>Pickups:</b> {pickup_count}<br>
#         <b>Pickups by Date:</b><br>
#         """ + "<br>".join(f"{d}: {pickup_by_date[d]}" for d in sorted(pickup_by_date))

#         folium.Marker(
#             location=centroid,
#             popup=popup_html,
#             icon=folium.Icon(color='red', icon='info-sign')
#         ).add_to(m)

#     # Save map
#     m.save(output_path)
#     print(f"\nMap saved to: {output_path}")

# # Example usage
# if __name__ == "__main__":
#     generate_hex_map_with_pickups(
#         pickup_csv='/Users/abhishek/Desktop/Taxi Demand forecasting/src/filtered_taxi_data.csv',  # Replace with your file path
#         resolution=8,
#         output_path='h3_pickup_map.html',
#         borough_index=3
#     )

# with oops concept and json format


import pandas as pd
import geopandas as gpd
import geodatasets
import folium
import h3
from shapely.geometry import Point
from collections import defaultdict
import json

class H3HexMap:
    def __init__(self, resolution=8, borough_index=3):
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
        df = gpd.read_file(geodatasets.get_path('nybb'))
        df = df.to_crs(epsg=4326)
        self.borough_geo = df.geometry[self.borough_index]
        self.borough_name = df.BoroName[self.borough_index]
        return self.borough_geo

    def filter_pickups_in_borough(self, df):
        self.load_borough()
        geometry = gpd.GeoSeries([Point(xy) for xy in zip(df.pickup_longitude, df.pickup_latitude)], crs='EPSG:4326')
        df['geometry'] = geometry
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        self.filtered_points = gdf[gdf.geometry.within(self.borough_geo)]
        print(f"Selected Borough: {self.borough_name}")
        print(f"Filtered {len(self.filtered_points)} pickup points within {self.borough_name}")
        return self.filtered_points

    def generate_hexagons(self):
        self.hex_cells = list(h3.geo_to_cells(self.borough_geo, res=self.resolution))
        return self.hex_cells

    def assign_hex_ids_to_points(self):
        self.filtered_points['hex_id'] = self.filtered_points.apply(
            lambda row: h3.latlng_to_cell(row.pickup_latitude, row.pickup_longitude, self.resolution), axis=1
        )
        self.filtered_points['date'] = pd.to_datetime(self.filtered_points['tpep_pickup_datetime']).dt.date
        return self.filtered_points

    def build_pickup_summary(self):
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
        return self.pickup_data

    def restructure_json_output(self):
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

        return output

    def generate_map(self):
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
        map_object.save(output_path)
        print(f"Map saved to {output_path}")
        self.summary = {
            "borough": self.borough_name,
            "total_hexes": len(self.hex_cells),
            "output_map": output_path
        }

    def export_json(self, filepath='pickup_summary.json'):
        structured_output = self.restructure_json_output()
        with open(filepath, 'w') as f:
            json.dump(structured_output, f, indent=2)
        print(f"JSON result saved to {filepath}")

    def run_pipeline(self, df, output_map='h3_hex_map.html', output_json='pickup_summary.json'):
        self.filter_pickups_in_borough(df)
        self.generate_hexagons()
        self.assign_hex_ids_to_points()
        self.build_pickup_summary()
        m = self.generate_map()
        self.save_map(m, output_path=output_map)
        self.export_json(filepath=output_json)
        return self.restructure_json_output()

# Load taxi data
df = pd.read_csv("/Users/abhishek/Desktop/Taxi Demand forecasting/src/filtered_taxi_data.csv")

# Initialize and run
hex_map = H3HexMap(resolution=8, borough_index=3)  # Manhattan
json_result = hex_map.run_pipeline(df)

# View final structured JSON
print(json.dumps(json_result, indent=2))
