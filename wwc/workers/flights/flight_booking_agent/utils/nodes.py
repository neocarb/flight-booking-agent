from langchain_openai import ChatOpenAI
from flight_booking_agent.utils.state import FlightBookingState
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from flight_booking_agent.utils.tools import search_offers, confirm_offer
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage,ToolMessage

llm = ChatOpenAI(model="gpt-4o")

def human_node(state: FlightBookingState):
    # get user input
    user_input = interrupt("Enter your input: ")
    # create a human message
    human_message = HumanMessage(content=user_input)
    return FlightBookingState(
        messages=state.messages + [human_message],
        from_node="human_node",
    )
    


def search_flight_offers_node(state: FlightBookingState) -> FlightBookingState:
    search_flight_offers_instruction = """
    You are a helpful and knowledgeable flight booking assistant. Your goal is to help the user search for flight offers based on their preferences.
    You will ask they user for all the necessary information to search for flight offers.
    Only once you have all the information, you will call the search_offers tool to get the flight offers.
    You will then present the user with the flight offers from the search_offers tool in a beautiful format after which the confirm_flight_offer_node will take offer to ask the user for the chosen flight offer and validate the offer.
    Keep your tone helpful, professional, and concise. If any information is ambiguous, ask clarifying questions. 
    """
    search_flight_offers_agent = create_react_agent(
        llm,
        tools=[search_offers],
        prompt=search_flight_offers_instruction
    )
    
    result = search_flight_offers_agent.invoke(state)
    ai_message = result['messages'][-1]
    return FlightBookingState(
        messages=state['messages'] + [ai_message],
        from_node="search_flight_offers_node"
    )


# make this node more deterministic gradually
def confirm_flight_offer_node(state: FlightBookingState) -> FlightBookingState:
    # This node is responsible for confirming the flight offer selected by the user.
    # It will extract the flight ID from the user's response and update the state accordingly.
    
    confirm_flight_offer_instruction = """
    You goal is to get the user to confirm their selected flight offer.
    1. If the user has already provided a offer ID, confirm it using the confirm_order tool. If any of the details of the offer has changed, inform the user and ask them to confirm the new offer.
    2. If the user has not provided a offer ID, ask them to choose a flight offer to proceed with.
    """
    
    confirm_flight_offer_agent = create_react_agent(
        llm,
        tools=[confirm_offer],
        prompt=confirm_flight_offer_instruction
    )
    
    result = confirm_flight_offer_agent.invoke(state)
    ai_message = result['messages'][-1]
    return FlightBookingState(
        messages=state['messages'] + [ai_message],
        from_node="confirm_flight_offer_node"
    )


def make_payment_node(state: FlightBookingState) -> FlightBookingState:    
    return FlightBookingState(
        from_node="make_payment_node"
    )

def create_flight_booking_node(state: FlightBookingState) -> FlightBookingState:  
    return FlightBookingState(
        from_node="create_flight_booking_node"
    )
    
        

    
    
    
    
    
    
