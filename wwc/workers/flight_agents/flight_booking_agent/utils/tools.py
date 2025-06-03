import requests
import logging
from typing import Annotated
from langchain_core.tools import tool
from datetime import datetime
from langchain.tools import Tool
import json

logger = logging.getLogger(__name__)

@tool
def search_offers(
    origin: Annotated[str, "IATA code of flight origin city"],
    destination: Annotated[str, "IATA code flight destination city"],
    departure_date: Annotated[str,"flight departure date from origin, format YYYY-MM-DD"],
    maxConnections: Annotated[int, "maximum number of connections allowed for the flight search, default is 0 (direct flight only)"] = None,
    cabinClass: Annotated[str, "cabin class for the flight search, allowed values are first, business"] = None,
    sortByPrice: Annotated[str, "sort by price of flight offers, allowed values are ascending or descending"] = None,
    ):
    """Search for flights based on user preference of origin, destination and departure date. Returns a json string with details of relevant flights."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "https://flightbookingserver-458112.ue.r.appspot.com/api/booking/searchFlight"

        headers = {
            "Content-Type": "application/json"
        }
        
        passengers = [{"type": "adult"}]
        payload = {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "passengers": passengers
        }
        
        params = {}
        if maxConnections:
            params["maxConnections"] = maxConnections
        if cabinClass:
            params["cabinClass"] = cabinClass
        if sortByPrice:
            params["sortByPrice"] = sortByPrice
        
        logger.info("search_offers payload: %s", payload)
        logger.info("search_offers params: %s", params)

        response = requests.post(api_url, headers=headers, json=payload, params=params)

        if response.status_code == 200:
            flights_data = response.json()
            return flights_data.get('data')
        else:
           return None
    except Exception as e:
        return None


def get_latest_offer(
    offer_id: Annotated[str, "offer ID"]) -> Annotated[dict, "flight offer details"]:
    """Fetch flight offer details based on the offer ID to see if  the offer is still valid. Returns a json string with details of the flight offer."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = f"https://flightbookingserver-458112.ue.r.appspot.com/api/booking/getOffer?offer_id={offer_id}"

        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            offer_data = response.json()
            return offer_data.get('data')
        else:
            return None
    except Exception as e:
        return None
    
@tool
def collect_passenger_details(
    passenger_title: Annotated[str, "passenger title, 'mr', 'ms', 'mrs'"],
    passenger_first_name: str,
    passenger_last_name: str,
    passenger_contact_number: str,
    passenger_email: str,
    passenger_date_of_birth: str,
    passenger_gender: Annotated[str, "passenger gender, 'm' for male, 'f' for female"],
    ) -> dict:
    """Collect passenger details for flight booking."""
    return {
        "passenger": {
            "title": passenger_title.lower(),
            "first_name": passenger_first_name,
            "last_name": passenger_last_name,
            "contact": passenger_contact_number,
            "email": passenger_email,
            "date_of_birth": passenger_date_of_birth,
            "gender": passenger_gender.lower()  
        }
    }

def get_payment_link(
    description: Annotated[float, "description of the payment"],
    name: Annotated[str, "passenger name for making payment"],  
    contact: Annotated[str, "passenger contact number for making payment"],
    email: Annotated[str, "passenger email for making payment"],
    ) -> Annotated[str,"url to open the payment page for making the payment"]:
    """Process payment for the flight booking. Returns a URL to open the payment page for the passenger to make the payment."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "https://flightbookingserver-458112.ue.r.appspot.com/api/razorpay/createPaymentLink"

        headers = {
            "Content-Type": "application/json"
        }
        
        customer = {
            "name": name,
            "contact": contact,
            "email": email
        }
        payload = {
            "description": description,
            "customer": customer,
        }

        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            payment_url = data.get('data', {}).get('short_url')
            return payment_url
        else:
            return None
    except Exception as e:
       return None
   

def create_flight_booking(
    description: Annotated[float, "description of the payment"],
    booking_offer_id: Annotated[str, "offer id to create booking for"],
    booking_passenger_title,
    booking_passenger_given_name,
    booking_passenger_family_name,
    booking_passenger_phone_number: Annotated[str, "offer id to create booking for"],
    booking_passenger_email,
    booking_passenger_born_on,
    booking_passenger_gender
    ) -> Annotated[str,"url to open the payment page for making the payment"]:
    """Process payment for the flight booking. Returns a URL to open the payment page for the passenger to make the payment."""
    try:
        # Example API endpoint and API key (replace with your real ones)
        api_url = "https://flightbookingserver-458112.ue.r.appspot.com/api/booking/create"

        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "description": description,
            "booking_offer_id": booking_offer_id,
            "booking_passenger_phone_number": booking_passenger_phone_number,
            "booking_passenger_email": booking_passenger_email,
            "booking_passenger_born_on": booking_passenger_born_on,
            "booking_passenger_title": booking_passenger_title,
            "booking_passenger_gender": booking_passenger_gender,
            "booking_passenger_family_name": booking_passenger_family_name,
            "booking_passenger_given_name": booking_passenger_given_name   
        }
        
        logger.info("create_flight_booking payload: %s", payload)
        response = requests.post(api_url, headers=headers, json=payload, verify=True)
        logger.info("create_flight_booking response: %s", response)

        if response.status_code == 200:
            data = response.json()
            payment_url = data.get('data', {}).get('payment_link')
            return payment_url
        else:
            return None
    except Exception as e:
       return None
   
def get_today_date() -> Annotated[str, "todays date in iso format"]:
    """returns todays date"""
    return datetime.now().isoformat()

@tool
def register_offer_id(offer_id: Annotated[str, "the offer id to register"]):
    """Registers the selected flight offer ID."""
    logger.info("Registering offer ID: %s", offer_id)
    # Store the offer ID in a persistent way (e.g., database, file, etc.)
    return offer_id