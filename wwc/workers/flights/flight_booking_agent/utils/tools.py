import json
import requests
from typing import Annotated, List
from langchain_core.tools import tool

@tool
def search_flights(
    origin: Annotated[str, "flight origin city"],
    destination: Annotated[str, "flight destination city"],
    departure_date: Annotated[str,"flight departure date from origin"],
    passengers: Annotated[List[str],"list of passenger types if passenger is above 18 then adult otherwise age"],
) -> Annotated[str,"json string with details of searched flights offers and passenger details"]:
    """Search for flights based on user preference of origin, destination and departure date. Returns a json string with details of relevant flights."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "localhost:8080/api/duffel/searchFlight"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "passengers": passengers
        }

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            flights_data = response.json()
            return json.dumps(flights_data, indent=2)
        else:
            return json.dumps({
                "error": f"Failed to fetch flights. Status Code: {response.status_code}",
                "details": response.text
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": "An exception occurred while fetching flights.",
            "details": str(e)
        }, indent=2)