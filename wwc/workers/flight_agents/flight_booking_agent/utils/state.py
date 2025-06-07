from langgraph.graph import MessagesState

class FlightBookingState(MessagesState):
    selected_flight_offer: str = ""
    passenger_details: str = ""
    payment_link: str = ""
    from_node: str = ""
    validation_status: bool = False