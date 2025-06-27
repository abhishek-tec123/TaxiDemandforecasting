# import geopandas
# import geodatasets
# import folium
# import h3

# def generate_hex_map(resolution=8, output_path='h3_cells_map.html', borough_index=3):
#     """
#     Generates a Folium map with H3 hexagons for a specified borough and prints hexagon details.

#     Args:
#         resolution (int): H3 resolution level (default: 8).
#         output_path (str): Path to save the HTML map (default: 'h3_cells_map.html').
#         borough_index (int): Index of the borough to plot (default: 3).

#     Returns:
#         dict: A dictionary containing hexagon details (count, average area, etc.).
#     """
#     # Load and prepare the dataset
#     df = geopandas.read_file(geodatasets.get_path('nybb'))
#     df = df.to_crs(epsg=4326)

#     # Plot the specified borough's H3 cells
#     geo = df.geometry[borough_index]
#     cells = h3.geo_to_cells(geo, res=resolution)

#     # Calculate hexagon details
#     hex_count = len(cells)
#     hex_areas = [h3.cell_area(cell, unit='km^2') for cell in cells]
#     avg_area = sum(hex_areas) / hex_count if hex_count > 0 else 0

#     # Create a Folium map centered on the borough
#     m = folium.Map(location=[geo.centroid.y, geo.centroid.x], zoom_start=12)

#     # Add H3 cells to the map
#     for cell in cells:
#         hexagon = h3.cell_to_boundary(cell)
#         folium.Polygon(
#             locations=hexagon,
#             color='blue',
#             fill=True,
#             fill_color='blue',
#             fill_opacity=0.2,
#             weight=0.5,
#         ).add_to(m)

#     # Save the map to an HTML file
#     m.save(output_path)

#     # Prepare hexagon details
#     details = {
#         'total_hexagons': hex_count,
#         'average_area_km2': avg_area,
#         'resolution': resolution,
#         'output_path': output_path,
#     }

#     # Print details
#     print(f"Total H3 hexagons: {hex_count}")
#     print(f"Average hexagon area (km²): {avg_area:.4f}")
#     print(f"Map saved to: {output_path}")

#     return details

# # Example usage
# if __name__ == "__main__":
#     generate_hex_map(resolution=8, output_path='h3_cells_map.html', borough_index=3)



import geopandas
import geodatasets
import folium
import h3
from collections import defaultdict

def generate_hex_map(resolution=8, output_path='h3_cells_map.html', borough_index=3):
    """
    Generates a Folium map with H3 hexagons for a specified borough, displays centroids, and prints hexagon details including parent and child counts.

    Args:
        resolution (int): H3 resolution level (default: 8).
        output_path (str): Path to save the HTML map (default: 'h3_cells_map.html').
        borough_index (int): Index of the borough to plot (default: 3).

    Returns:
        dict: A dictionary containing hexagon details (count, average area, etc.).
    """
    # Load and prepare the dataset
    df = geopandas.read_file(geodatasets.get_path('nybb'))
    df = df.to_crs(epsg=4326)

    # Plot the specified borough's H3 cells
    geo = df.geometry[borough_index]
    cells = h3.geo_to_cells(geo, res=resolution)

    # Calculate hexagon details
    hex_count = len(cells)
    hex_areas = [h3.cell_area(cell, unit='km^2') for cell in cells]
    avg_area = sum(hex_areas) / hex_count if hex_count > 0 else 0

    # Create a Folium map centered on the borough
    m = folium.Map(location=[geo.centroid.y, geo.centroid.x], zoom_start=12)

    # Track parent-child relationships
    parent_child_counts = defaultdict(int)
    for cell in cells:
        parent_cell = h3.cell_to_parent(cell, resolution - 1) if resolution > 0 else None
        if parent_cell:
            parent_child_counts[parent_cell] += 1

    # Print details for each hexagon and add to map
    print("\nHexagon Details:")
    for i, cell in enumerate(cells, 1):
        centroid = h3.cell_to_latlng(cell)
        area = h3.cell_area(cell, unit='km^2')
        parent_cell = h3.cell_to_parent(cell, resolution - 1) if resolution > 0 else None
        parent_centroid = h3.cell_to_latlng(parent_cell) if parent_cell else None
        parent_area = h3.cell_area(parent_cell, unit='km^2') if parent_cell else None
        child_count = parent_child_counts.get(parent_cell, 0) if parent_cell else 0

        print(f"\nHexagon {i}:")
        print(f"  H3 Index: {cell}")
        print(f"  Centroid (Lat, Lng): {centroid}")
        print(f"  Area (km²): {area:.4f}")
        if parent_cell:
            print(f"  Parent H3 Index: {parent_cell}")
            print(f"  Parent Centroid (Lat, Lng): {parent_centroid}")
            print(f"  Parent Area (km²): {parent_area:.4f}")
            print(f"  Number of Child Hexagons: {child_count}")

        # Add hexagon to the map
        hexagon = h3.cell_to_boundary(cell)
        folium.Polygon(
            locations=hexagon,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.2,
            weight=0.5,
        ).add_to(m)

        # Add centroid marker to the map
        folium.Marker(
            location=centroid,
            popup=f"Hexagon {i}: {cell}<br>Area: {area:.4f} km²<br>Parent: {parent_cell or 'N/A'}<br>Children: {child_count}",
            icon=folium.Icon(color='red', icon='info-sign'),
        ).add_to(m)

        # Add parent hexagon to the map if exists
        if parent_cell:
            parent_hexagon = h3.cell_to_boundary(parent_cell)
            folium.Polygon(
                locations=parent_hexagon,
                color='green',
                fill=False,
                weight=1.5,
            ).add_to(m)

            folium.Marker(
                location=parent_centroid,
                popup=f"Parent Hexagon: {parent_cell}<br>Area: {parent_area:.4f} km²<br>Children: {child_count}",
                icon=folium.Icon(color='green', icon='info-sign'),
            ).add_to(m)

    # Save the map to an HTML file
    m.save(output_path)

    # Prepare hexagon details
    details = {
        'total_hexagons': hex_count,
        'average_area_km2': avg_area,
        'resolution': resolution,
        'output_path': output_path,
    }

    # Print summary
    print(f"\nSummary:")
    print(f"Total H3 hexagons: {hex_count}")
    print(f"Average hexagon area (km²): {avg_area:.4f}")
    print(f"Map saved to: {output_path}")

    return details

# Example usage
if __name__ == "__main__":
    generate_hex_map(resolution=8, output_path='h3_cells_map.html', borough_index=3)