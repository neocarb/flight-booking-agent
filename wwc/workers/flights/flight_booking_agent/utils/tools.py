import json
import requests
from typing import Annotated, List
from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.tools.base import InjectedToolCallId
from langchain_core.messages import ToolMessage

# can tools only return json string or dict? Can they return POJO or other types of objects?
@tool
def search_offers(
    tool_call_id: Annotated[str, InjectedToolCallId],
    origin: Annotated[str, "flight origin city"],
    destination: Annotated[str, "flight destination city"],
    departure_date: Annotated[str,"flight departure date from origin"],
    passenger_age: Annotated[str,"if passenger is above 18 then adult otherwise age"]):
    """Search for flights based on user preference of origin, destination and departure date. Returns a json string with details of relevant flights."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "https://flightbookingserver-458112.ue.r.appspot.com/api/duffel/searchFlight"

        headers = {
            "Content-Type": "application/json"
        }
        
        passengers = [{"type": passenger_age}]
        payload = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "passengers": passengers
        }

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            flights_data = response.json()
            return Command(
                update={
                    "flight_offers": json.dumps(flights_data.get('data')),
                    "messages": [ToolMessage(flights_data.get('data'), tool_call_id=tool_call_id)]
                }
            )
        else:
            return Command(update={"messages": [ToolMessage("Failed to fetch flight offers", tool_call_id=tool_call_id)]})
    except Exception as e:
       return Command(update={"messages": [ToolMessage("Unable to fetch flight offers", tool_call_id=tool_call_id)]})

@tool
def get_latest_offer(
    tool_call_id: Annotated[str, InjectedToolCallId],
    offer_id: Annotated[str, "offer ID"]) -> Annotated[dict, "flight offer details"]:
    """Fetch flight offer details based on the offer ID to see if  the offer is still valid. Returns a json string with details of the flight offer."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = f"https://flightbookingserver-458112.ue.r.appspot.com/api/duffel/getOffer?offer_id={offer_id}"

        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            offer_data = response.json()
            return offer_data.get('data')
        else:
            return {"error": f"Failed to fetch offer. Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
        
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