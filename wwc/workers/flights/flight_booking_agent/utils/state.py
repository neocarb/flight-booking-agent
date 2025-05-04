from langgraph.graph import MessagesState
from flight_booking_agent.models.offer_dto import OfferDTO
from flight_booking_agent.models.passenger_dto import PassengerDTO
from flight_booking_agent.models.payment_dto import PaymentDTO


class FlightBookingState(MessagesState):
    flight_offers: str = ""
    selected_flight_offer_id: str = ""
    selected_flight_offer: str = ""
    passenger_details: str = ""
    payment_link: str = ""
    booking_reference: str = ""
    from_node: str = ""