import json
import requests
from typing import Annotated, List
from langchain_core.tools import tool

# can tools only return json string or dict? Can they return POJO or other types of objects?
@tool
def search_offers(
    origin: Annotated[str, "flight origin city"],
    destination: Annotated[str, "flight destination city"],
    departure_date: Annotated[str,"flight departure date from origin"],
    passengers: Annotated[List[str],"list of passenger types if passenger is above 18 then adult otherwise age"],
) -> Annotated[str,"json string with details of searched flights offers and passenger details"]:
    """Search for flights based on user preference of origin, destination and departure date. Returns a json string with details of relevant flights."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "https://flightbookingserver-458112.ue.r.appspot.com/api/duffel/searchFlight"

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

@tool
def get_offer(
    offer_id: Annotated[str, "offer ID"],
) -> Annotated[str,"json string with details of flight offer"]:
    """Fetch flight offer details based on the offer ID. Returns a json string with details of the flight offer."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = f"https://flightbookingserver-458112.ue.r.appspot.com/api/duffel/getOffer?offer_id={offer_id}"

        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            offer_data = response.json()
            return json.dumps(offer_data, indent=2)
        else:
            return json.dumps({
                "error": f"Failed to fetch offer. Status Code: {response.status_code}",
                "details": response.text
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": "An exception occurred while fetching offer.",
            "details": str(e)
        }, indent=2)
        
@tool
def process_payment(
    amount: Annotated[float, "amount to be paid"],
    currency: Annotated[str, "currency of the payment"],  
    ) -> Annotated[bool,"True if payment is successful else False"]:
    """Process payment for the flight booking. Returns True if payment is successful, else False."""
    return True

@tool
def create_flight_booking(
    selected_offer_id: Annotated[str, "selected offer ID"],
    payment_details: Annotated[dict, "payment details"],
    passenger_details: Annotated[dict, "passenger details"],
    ) -> Annotated[str,"booking reference for the flight booking"]:
    """Create a flight booking based on the selected offer ID, payment details and passenger details. Returns a booking reference."""
    return "booking_reference_12345"


if __name__ == "__main__":
    result = get_offer(
        offer_id="off_0000AtaArLGLsZ8NKvvpDC"
    )
    print(result)