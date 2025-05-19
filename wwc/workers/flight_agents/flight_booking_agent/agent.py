from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from wwc.workers.flight_agents.flight_booking_agent.utils.state import FlightBookingState
from wwc.workers.flight_agents.flight_booking_agent.utils.router import (
    search_flight_offers_router, 
    validate_flight_offer_router, 
    human_router, 
    collect_passenger_details_router
)
from wwc.workers.flight_agents.flight_booking_agent.utils.nodes import (
    search_flight_offers_node,
    human_node,
    validate_flight_offer_node,
    collect_passenger_details_node,
    create_flight_booking_node
)

flight_booking_builder = StateGraph(FlightBookingState)
flight_booking_builder.add_node("search_flight_offers_node", search_flight_offers_node)
flight_booking_builder.add_node("validate_flight_offer_node", validate_flight_offer_node)
flight_booking_builder.add_node("collect_passenger_details_node", collect_passenger_details_node)
flight_booking_builder.add_node("create_flight_booking_node", create_flight_booking_node)
flight_booking_builder.add_node("human_node", human_node)

# flight_booking_builder.add_node("payment_node", make_payment_node)
# flight_booking_builder.add_node("create_flight_booking_node", create_flight_booking_node)

flight_booking_builder.add_edge(START, "search_flight_offers_node")
flight_booking_builder.add_conditional_edges(
            "search_flight_offers_node",
            search_flight_offers_router,
            {
                "human_node": "human_node",
                "validate_flight_offer_node": "validate_flight_offer_node"
            }
        )
flight_booking_builder.add_conditional_edges(
            "validate_flight_offer_node",
            validate_flight_offer_router,
            {
                "collect_passenger_details_node": "collect_passenger_details_node",
                "human_node": "human_node"
            }
        )

flight_booking_builder.add_conditional_edges(
    "collect_passenger_details_node", 
    collect_passenger_details_router,
    {
        "human_node": "human_node",
        "create_flight_booking_node": "create_flight_booking_node",
    }
    )

flight_booking_builder.add_edge("create_flight_booking_node", END)

flight_booking_builder.add_conditional_edges(
    "human_node",
    human_router,
    {
        "search_flight_offers_node": "search_flight_offers_node",
        "validate_flight_offer_node": "validate_flight_offer_node",
        "collect_passenger_details_node": "collect_passenger_details_node",
    }
)

checkpointer = MemorySaver()
flight_booking_agent = flight_booking_builder.compile(name="flight_booking_agent")

'''
thread_config = {"configurable": {"thread_id": 30}}
input_dict = {"messages": [HumanMessage(content="Heyyy")]}
for event in flight_booking_agent.stream(
        input_dict,
        config=thread_config,
        stream_mode="values",
        debug=True,
        subgraphs=True):
    print(event)
    print("--------------------------------")
'''



