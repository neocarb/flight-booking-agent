import json
import logging
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from wwc.workers.flight_agents.flight_booking_agent.utils.state import FlightBookingState
from wwc.workers.flight_agents.flight_booking_agent.utils.tools import search_offers, get_latest_offer, collect_passenger_details, get_payment_link, create_flight_booking
from langgraph.prebuilt.interrupt import HumanInterrupt, ActionRequest, HumanInterruptConfig

llm = ChatOpenAI(model="gpt-4o")
logger = logging.getLogger(__name__)

def human_node(state: FlightBookingState):
    # get user input
    last_ai_message = state['messages'][-1].content
    logger.info("last_ai_message: %s", last_ai_message)
    
    
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Provide input",  # Action name for clarity in your context
            args={}                        # No initial args; user will provide input
        ),
        config=HumanInterruptConfig(
            allow_ignore=False,
            allow_respond=True,     # Allowing textual response
            allow_edit=False,
            allow_accept=False
        ),
        description="last_ai_message"
    )
    response = interrupt([request])[0]
    logger.info("response: %s", response)
    user_input = response.get("args", "")
    
    # user_input = interrupt(last_ai_message.content)
    logger.info("user_input: %s", user_input)
    human_message = HumanMessage(content=user_input)
    # create a human message
    human_message = HumanMessage(content=user_input)
    return {
        "messages": [human_message]
    }

def search_flight_offers_node(state: FlightBookingState) -> FlightBookingState:
    search_flight_offers_instruction = """
    You are a helpful and knowledgeable flight booking assistant. Your goal is to help the user search for flight offers based on their preferences.
    You will ask they user for all the necessary information to search for flight offers.
    Only once you have all the information, you will call the search_offers tool to get the flight offers.
    You will then present the user with the flight offers from the search_offers tool in a beautiful format after which the validate_flight_offer_node will take offer to ask the user for the chosen flight offer and validate the offer.
    Keep your tone helpful, professional, and concise. If any information is ambiguous, ask clarifying questions. 
    """
    search_flight_offers_agent = create_react_agent(
        llm,
        tools=[search_offers],
        prompt=search_flight_offers_instruction
    )
    
    result = search_flight_offers_agent.invoke(state)
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'search_offers'), None)
    tool_message_content = tool_message.content if tool_message else None
        
    return {
        "messages": result['messages'],
        'from_node': 'search_flight_offers_node',
        "flight_offers": tool_message_content
    }


# make this node more deterministic and rule based gradually
def validate_flight_offer_node(state: FlightBookingState) -> FlightBookingState:
    # This node is responsible for confirming the flight offer selected by the user.
    # It will extract the flight ID from the user's response and update the state accordingly.
    
    validate_flight_offer_instruction = """
    You goal is to get the user to confirm their selected flight offer.
    1. If the user has not provided a offer ID, ask them to choose a flight offer to proceed with.DO NOT MAKE ANY ASSUMPTIONS ABOUT THE OFFER
    2. If the user has already provided a offer ID, validate if all the details of the offer are valid. TO validate follow the steps below
    2.1. Use the get_latest_offer tool to fetch the latest details of the offer using the offer ID provided by the user.
    2.2. Check if any of the offer details have changed compared to the original offer details.
    3. If the offer is no longer valid, inform the user and ask them to choose a new offer. Validate the new offer again as per step 2.
    4. If the offer is valid, ask the user to confirm if they want to proceed with the offer.
    5. if the user confirms then move on to the collect_passenger_details_node.
    """
    
    validate_flight_offer_agent = create_react_agent(
        llm,
        tools=[get_latest_offer],
        prompt=validate_flight_offer_instruction
    )
    
    result = validate_flight_offer_agent.invoke(state)
    
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'get_latest_offer'), None)
    tool_message_content = tool_message.content if tool_message else None
    tool_message_content_dict = json.loads(tool_message_content) if tool_message_content else None
    selected_offer = tool_message_content_dict.get('offer') if tool_message_content_dict else None
    selected_offer_id = selected_offer.get('offerId') if selected_offer else None
    
    #TODO: route based on wether flight offer is valid
    
    return {
        "messages": result['messages'],
        "from_node": "validate_flight_offer_node",
        "selected_flight_offer_id": selected_offer_id,  # corrected variable name
        "selected_flight_offer": json.dumps(selected_offer) if selected_offer else None,  # corrected variable name
    }

def collect_passenger_details_node(state: FlightBookingState) -> FlightBookingState:
    collect_passenger_details_instruction = """
    You goal is to get the user to provide their passenger details for flight booking.
    1. Ask the user for their name, contact number, email, and age.
    2. Once you have all the details, present them in a structured format for the user to review
    3. Only nce the user confirms and finalises the details, call the collect_passenger_details tool to collect the passenger details. never call the collect_passenger_details tool without all the details.
    4. After you are done, create flight booking node will be called to handle payment and create the booking
    """
    
    collect_passenger_details_agent = create_react_agent(
        llm,
        tools=[collect_passenger_details],
        prompt=collect_passenger_details_instruction
    )
    
    result = collect_passenger_details_agent.invoke(state)
    print("collect_passenger_details_node result", result)
    
    passenger_details = None
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'collect_passenger_details'), None)
    tool_message_content = tool_message.content if tool_message else None
    tool_message_content_dict = json.loads(tool_message_content) if tool_message_content else None
    passenger_details = tool_message_content_dict.get('passenger') if tool_message_content_dict else None
    print("passenger_details", passenger_details)
    
    return {
        "messages": result['messages'],
        "from_node": "collect_passenger_details_node",
        "passenger_details": json.dumps(passenger_details) if passenger_details else None,  # corrected variable name
    }

def payment_node(state: FlightBookingState) -> FlightBookingState:
    description = "Flight booking payment"
    passenger_details = json.loads(state['passenger_details']) if state['passenger_details'] else None
    if not passenger_details:
        payment_message = AIMessage(content="There is a problem with the payment, please try again.")
        return {
            "messages": [payment_message],
            "from_node": "payment_node",
        }
    name = passenger_details.get('name')
    contact = passenger_details.get('contact')
    email = passenger_details.get('email')
    payment_link = get_payment_link(
        description=description,
        name=name,
        contact=contact,
        email=email
    )
    print("payment_link", payment_link)
    if not payment_link:
        payment_message = AIMessage(content="There is a problem with the payment, please try again.")
        return {
            "messages": [payment_message],
            "from_node": "payment_node",
        }
    payment_message = AIMessage(content=f"Please make the payment using the following link: {payment_link}")
    return {
        "from_node": "payment_node",
        "messages": [payment_message],
        "payment_link": payment_link,
    }
    
def create_flight_booking_node(state: FlightBookingState) -> FlightBookingState:
    description = "Flight booking payment"
    offer_id = state['selected_flight_offer_id']
    passenger_details = json.loads(state['passenger_details']) if state['passenger_details'] else None
    logger.info("passenger_details %s", passenger_details)
    if not passenger_details:
        payment_message = AIMessage(content="There is a problem with the payment, please try again.")
        return {
            "messages": [payment_message],
            "from_node": "create_flight_booking_node",
        }
    name = passenger_details.get('name')
    contact = passenger_details.get('contact')
    email = passenger_details.get('email')
    
    
    
    payment_link = create_flight_booking(description, name, contact, email, offer_id, contact, email, "07/12/1998", "mr", "m", name, name)
    print("payment_link", payment_link)
    if not payment_link:
        payment_message = AIMessage(content="There is a problem with the payment, please try again.")
        return {
            "messages": [payment_message],
            "from_node": "create_flight_booking_node",
        }
    payment_message = AIMessage(content=f"Please make the payment using the following link: {payment_link}")
    return {
        "from_node": "create_flight_booking_node",
        "messages": [payment_message],
        "payment_link": payment_link,
    }