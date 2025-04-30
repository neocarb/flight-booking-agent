from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from flight_booking_agent.utils.state import FlightBookingState
from flight_booking_agent.utils.nodes import (
    search_flight_offers_node,
    human_node,
    confirm_flight_offer_node,
    make_payment_node,
    create_flight_booking_node
)
from flight_booking_agent.utils.router import search_flight_offers_router, confirm_flight_offer_router, human_router

flight_booking_builder = StateGraph(FlightBookingState)
flight_booking_builder.add_node("search_flight_offers_node", search_flight_offers_node)
flight_booking_builder.add_node("human_node", human_node)
flight_booking_builder.add_node("confirm_flight_offer_node", confirm_flight_offer_node)
flight_booking_builder.add_node("payment_node", make_payment_node)
flight_booking_builder.add_node("create_flight_booking_node", create_flight_booking_node)

flight_booking_builder.add_edge(START, "search_flight_offers_node")
flight_booking_builder.add_conditional_edges(
            "search_flight_offers_node",
            search_flight_offers_router,
            {
                "search_flight_offers_node": "search_flight_offers_node",
                "human_node": "human_node",
                "confirm_flight_offer_node": "confirm_flight_offer_node"
            }
        )
flight_booking_builder.add_conditional_edges(
            "confirm_flight_offer_node",
            confirm_flight_offer_router,
            {
                "confirm_flight_offer_node": "confirm_flight_offer_node",
                "payment_node": "payment_node",
                "human_node": "human_node"
            }
        )
flight_booking_builder.add_conditional_edges(
    "human_node",
    human_router,
    {
        "search_flight_offers_node": "search_flight_offers_node",
        "confirm_flight_offer_node": "confirm_flight_offer_node",
        "payment_node": "payment_node",
        "create_flight_booking_node": "create_flight_booking_node"
    }
)
flight_booking_builder.add_edge("confirm_flight_offer_node", END)
graph = flight_booking_builder.compile()



