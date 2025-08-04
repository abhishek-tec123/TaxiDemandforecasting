import h3
import requests
import os
from dotenv import load_dotenv
from typing import List

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("LOCATIONIQ_API_KEY")

def reverse_geocode_h3_list(h3_ids: List[str]) -> List[dict]:
    """
    Reverse geocode a list of H3 cell IDs using LocationIQ.

    Args:
        h3_ids (List[str]): List of H3 cell IDs.

    Returns:
        List[dict]: List of parsed address info or errors per H3 cell.
    """
    if not API_KEY:
        return [{"error": "API key not found. Set LOCATIONIQ_API_KEY in .env"}]

    results = []

    for h3_id in h3_ids:
        try:
            lat, lon = h3.cell_to_latlng(h3_id)
            url = f"https://us1.locationiq.com/v1/reverse.php?key={API_KEY}&lat={lat}&lon={lon}&format=json"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                results.append({
                    "h3_id": h3_id,
                    "lat": lat,
                    "lon": lon,
                    "address": data.get("display_name"),
                    "neighbourhood": data.get("address", {}).get("neighbourhood", ""),
                    "suburb": data.get("address", {}).get("suburb", ""),
                    "city": data.get("address", {}).get("city", ""),
                    "state": data.get("address", {}).get("state", ""),
                    "country": data.get("address", {}).get("country", "")
                })
            else:
                results.append({
                    "h3_id": h3_id,
                    "error": response.status_code,
                    "message": response.text
                })
        except Exception as e:
            results.append({
                "h3_id": h3_id,
                "error": "Exception",
                "message": str(e)
            })

    return results

# # 🧪 Example usage
# if __name__ == "__main__":
#     h3_list = [
#         "882a100883fffff" # Add as many as you want
#     ]
#     result = reverse_geocode_h3_list(h3_list)
#     for item in result:
#         print(item)
