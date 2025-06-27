# import h3
# import folium

# def draw_boundary(map_obj, coordinates, color='blue', weight=2):
#     """
#     Draw a boundary on the map
#     Args:
#         map_obj: Folium map object
#         coordinates: List of (lat, lon) tuples
#         color: Color of the boundary
#         weight: Line weight
#     """
#     folium.Polygon(
#         locations=coordinates,
#         color=color,
#         weight=weight,
#         fill=False
#     ).add_to(map_obj)

# def fill_polygon(map_obj, coordinates, color='blue', opacity=0.1):
#     """
#     Fill a polygon on the map
#     Args:
#         map_obj: Folium map object
#         coordinates: List of (lat, lon) tuples
#         color: Fill color
#         opacity: Fill opacity
#     """
#     folium.Polygon(
#         locations=coordinates,
#         color=color,
#         weight=1,
#         fill=True,
#         fill_color=color,
#         fill_opacity=opacity
#     ).add_to(map_obj)

# def create_h3_map(polygon_coords, resolution=8, center_lat=40.7128, center_lon=-73.9352, zoom=10):
#     """
#     Create a map with H3 cells and polygon
#     Args:
#         polygon_coords: List of (lat, lon) tuples defining the polygon
#         resolution: H3 resolution
#         center_lat: Map center latitude
#         center_lon: Map center longitude
#         zoom: Initial zoom level
#     """
#     # Create the polygon
#     poly = h3.LatLngPoly(polygon_coords)
    
#     # Get H3 cells
#     h3_cells = h3.h3shape_to_cells(poly, resolution)
    
#     # Create map
#     m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    
#     # Draw NYC boundary
#     draw_boundary(m, polygon_coords, color='blue', weight=2)
#     fill_polygon(m, polygon_coords, color='blue', opacity=0.1)
    
#     # Add H3 cells
#     # for cell in h3_cells:
#     #     cell_boundary = h3.cell_to_boundary(cell)
#     #     draw_boundary(m, cell_boundary, color='red', weight=1)
#     #     fill_polygon(m, cell_boundary, color='red', opacity=0.1)
    
#     return m

# def get_nyc_coordinates():
#     """
#     Returns the coordinates for NYC polygon
#     Returns:
#         List of (lat, lon) tuples
#     """
#     return [
#         (40.706400227558, -74.02178611650699),
#         (40.69381584455656, -73.98858776937341),
#         (40.87106819552763, -73.8881414883026),
#         (40.91804116933191, -73.91878611600116)
#     ]

# def main():
#     """
#     Main function to create and save the NYC H3 map
#     """
#     # Get NYC coordinates
#     nyc_coords = get_nyc_coordinates()
    
#     # Create the map
#     m = create_h3_map(
#         polygon_coords=nyc_coords,
#         resolution=8,
#         center_lat=40.7128,
#         center_lon=-73.9352,
#         zoom=10
#     )
    
#     # Save the map
#     output_file = 'nyc_h3_map.html'
#     m.save(output_file)
#     print(f"Map has been saved as '{output_file}'. Open this file in your web browser to view the interactive map.")

# if __name__ == "__main__":
#     main()





import geopandas
import geodatasets
from h3Helper import plot_df, plot_shape, plot_cells
import matplotlib.pyplot as plt
import h3
import pandas as pd

# Load and prepare data
df = geopandas.read_file(geodatasets.get_path('nybb'))
df = df.to_crs(epsg=4326)
print("\nDataset CRS:", df.crs)

# Analyze cells for each borough
print("\nAnalyzing H3 cells for each borough:")
for idx, row in df.iterrows():
    borough_name = row['BoroName']
    cells = h3.geo_to_cells(row.geometry, res=8)
    print(f"\n{borough_name}:")
    print(f"Number of H3 cells (resolution 8): {len(cells)}")
    print(f"Sample cell: {list(cells)[0]}")

# Create cell column and analyze
cell_column = df.geometry.apply(lambda x: h3.geo_to_cells(x, res=8))
total_cells = cell_column.apply(len).sum()
print(f"\nTotal cells across all boroughs: {total_cells:,}")

# Plot all boroughs together
plt.figure(figsize=(15, 10))
# Create a single plot for all boroughs
for idx, row in df.iterrows():
    cells = h3.geo_to_cells(row.geometry, res=8)
    plot_cells(cells)
plt.title('H3 Cells (Resolution 8) for New York City')
plt.show()