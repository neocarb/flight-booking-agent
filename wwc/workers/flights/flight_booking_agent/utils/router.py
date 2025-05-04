from flight_booking_agent.utils.state import FlightBookingState
from typing import Literal, Union, Dict
import logging
import json
from flight_booking_agent.models.offer_dto import OfferDTO

logger = logging.getLogger(__name__)

NodeType = Literal['search_flight_offers_node', 'human_node', 'validate_flight_offer_node', 'payment_node', '__end__']

def search_flight_offers_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering search_flight_offers_router")
    print("state", state)
    if 'flight_offers' in state and state['flight_offers']:
        return 'validate_flight_offer_node'
    return 'human_node'
    
def validate_flight_offer_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering validate_flight_offer_router")
    print("state", state)
    
    if  'selected_flight_offer_id' in state and state['selected_flight_offer_id'] and 'selected_flight_offer' in state and state['selected_flight_offer']:
        return 'collect_passenger_details_node'
    return 'human_node'
    
    # try:
    #     flight_offer_json = json.loads(state['selected_flight_offer'])
    #     flight_offer = OfferDTO(flight_offer_json)
    #     if not flight_offer_json:
    #         return 'payment_node'  # reconsider
    #     return 'validate_flight_offer_node'
        
    # except Exception as e:
    #     logger.error(f"Error while confirming flight offer: {e}")
    #     return 'validate_flight_offer_node'  # maybe human_node?
    
def collect_passenger_details_router(state: FlightBookingState) -> NodeType:
    if 'passenger_details' in state and state['passenger_details']:
        return 'payment_node'
    return 'human_node'
    
def human_router(state: FlightBookingState) -> NodeType:
    # return the node which passed the human node
    return state['from_node']