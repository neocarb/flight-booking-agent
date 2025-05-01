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
    if 'flight_offers' not in state:
        return 'human_node'
    
    try:
        flight_offers_json = json.loads(state['flight_offers'])
        flight_offers_list = [OfferDTO(**offer) for offer in flight_offers_json["offers"]]
        logger.info(f"Flight offers: {flight_offers_list}")
        if(len(flight_offers_list) == 0):
            return 'human_node' # reconsider
        return 'confirm_flight_offer_node'
        
    except Exception as e:
        logger.error(f"Error while searching flight offers: {e}")
        return 'search_flight_offers_node'  # maybe human_node?
    
def confirm_flight_offer_router(state: FlightBookingState) -> NodeType:
    logger.info("Entering confirm_flight_offer_router")
    
    if 'selected_flight_offer_id' in state and state['selected_flight_offer_id'] and 'selected_flight_offer' in state and state['selected_flight_offer']:
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
        
     
     
    