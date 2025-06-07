import logging
from typing import Literal
from langgraph.graph import END

from wwc.workers.flight_agents.flight_booking_agent.utils.state import FlightBookingState

logger = logging.getLogger(__name__)

NodeType = Literal['search_flight_offers_node', 'human_node', 'validate_flight_offer_node', END, 'collect_passenger_details_node', 'create_flight_booking_node']

def search_flight_offers_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering search_flight_offers_router, state: %s", state)   
    if 'selected_flight_offer' in state and state['selected_flight_offer']:
        return 'validate_flight_offer_node'
    return 'human_node'
    
def validate_flight_offer_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering validate_flight_offer_router")
    if 'validation_status' in state and state['validation_status']:
        return 'collect_passenger_details_node'
    return END

def collect_passenger_details_router(state: FlightBookingState) -> NodeType:
    if 'passenger_details' in state and state['passenger_details']:
        return 'create_flight_booking_node'
    return 'human_node'
    
def human_router(state: FlightBookingState) -> NodeType:
    last_human_message = state['messages'][-1].content
    if 'reset' in last_human_message:
        return END
    return state['from_node']