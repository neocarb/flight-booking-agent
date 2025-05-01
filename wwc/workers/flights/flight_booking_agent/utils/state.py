from langgraph.graph import MessagesState
from flight_booking_agent.models.offer_dto import OfferDTO
from flight_booking_agent.models.passenger_dto import PassengerDTO
from flight_booking_agent.models.payment_dto import PaymentDTO


class FlightBookingState(MessagesState):
    flight_offers: str = None
    selected_flight_offer_id: str = None
    selected_flight_offer: str = None
    passenger_details: PassengerDTO = None
    payment_details: PaymentDTO = None
    booking_reference: str = None
    from_node: str = None