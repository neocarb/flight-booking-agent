from flight_booking_agent.utils.state import FlightBookingState
from typing import Literal
import logging

logger = logging.getLogger(__name__)

NodeType = Literal['search_flight_offers_node', 'human_node', 'validate_flight_offer_node', 'payment_node', '__end__']

def search_flight_offers_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering search_flight_offers_router")
    if 'flight_offers' in state and state['flight_offers']:
        return 'validate_flight_offer_node'
    return 'human_node'
    
def validate_flight_offer_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering validate_flight_offer_router")
    if  'selected_flight_offer_id' in state and state['selected_flight_offer_id'] and 'selected_flight_offer' in state and state['selected_flight_offer']:
        return 'collect_passenger_details_node'
    return 'human_node'
    
def collect_passenger_details_router(state: FlightBookingState) -> NodeType:
    if 'passenger_details' in state and state['passenger_details']:
        return 'payment_node'
    return 'human_node'
    
def human_router(state: FlightBookingState) -> NodeType:
    return state['from_node']