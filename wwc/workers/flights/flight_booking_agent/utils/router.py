from flight_booking_agent.utils.state import FlightBookingState
from typing import Literal, Union, Dict
import logging
import json
from flight_booking_agent.models.offer_dto import OfferDTO

logger = logging.getLogger(__name__)

NodeType = Literal['search_flight_offers_node', 'human_node', 'confirm_flight_offer_node', 'payment_node', '__end__']

def search_flight_offers_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering search_flight_offers_router")
    print("state", state)
    if len(state['flight_offers']) == 0:
        return 'human_node'
    return 'confirm_flight_offer_node'
    
def confirm_flight_offer_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering confirm_flight_offer_router")
    
    if  state['selected_flight_offer_id'] and state['selected_flight_offer']:
        return 'payment_node'
    else:
        return 'human_node'
    
    # try:
    #     flight_offer_json = json.loads(state['selected_flight_offer'])
    #     flight_offer = OfferDTO(flight_offer_json)
    #     if not flight_offer_json:
    #         return 'payment_node'  # reconsider
    #     return 'confirm_flight_offer_node'
        
    # except Exception as e:
    #     logger.error(f"Error while confirming flight offer: {e}")
    #     return 'confirm_flight_offer_node'  # maybe human_node?
    
def human_router(state: FlightBookingState) -> NodeType:
    # return the node which passed the human node
    return state['from_node']
        
     
     
    