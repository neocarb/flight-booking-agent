import json
import logging
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from wwc.workers.flight_agents.flight_booking_agent.utils.state import FlightBookingState
from wwc.workers.flight_agents.flight_booking_agent.utils.tools import search_offers, get_latest_offer, collect_passenger_details, get_payment_link, create_flight_booking, get_today_date
from langgraph.prebuilt.interrupt import HumanInterrupt, ActionRequest, HumanInterruptConfig

# should try to reduce the number of nodes, reduces failure rate

llm = ChatOpenAI(model="gpt-4o")
logger = logging.getLogger(__name__)

def build_agent_prompt(base_instruction: str, step_number: int, previous_step: str, next_step: str) -> str:
    flow_context = f"""
Context: You are step {step_number} in a multi-step flight booking process.
- Previous step: {previous_step}
- Next step: {next_step}
Your goal is to generate natural, flowing responses that feel like part of a single conversation. 
Avoid robotic transitions. Refer casually to earlier steps where appropriate.
"""
    return base_instruction.strip() + "\n" + flow_context.strip()


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

# stop child from making a booking; Handle child
# query -> confirm -> tool_call
def search_flight_offers_node(state: FlightBookingState) -> FlightBookingState:
    search_flight_offers_instruction = """
    You are a professional flight booking assistant helping users search for one-way flights for a single passenger.
    Your job is to help the user search for flight offers based on the following conditions:
    - Departure and destination airports or cities
    - Travel date (if needed, use the `get_today_date` tool to get the todays date)
    - if the passenger is an adult. Any one above the age of 18 is considered an adult.
    
    Optionally, you can also ask for:
    - Max number of connections or stops
    - Cabin class preference (economy, business, first)
    - Sort order for flight offers (ascending or descending by price)
    
    
    You follow the following steps to search for flight offers:
    1. Ask the user for the conditions to search for flights.
    2. If you have all the conditions to search for flights, ask the user for confirmation before calling the `search_offers` tool. Else go back to step 1.
    3. If the user confirms, call the `search_offers` tool with the most latest set fo conditions. Else go back to step 1.
    
    Do not call any tools in parallel.

    Once you get the offers:
    - Present the options clearly, with key details (airline, departure time, price) and the `offer_id` for each.
    - Use bullet points or a table for easy reading.

    Keep your responses helpful, concise, and professional. Ask clarifying questions if any detail is missing or ambiguous.
    """
    search_flight_offers_agent = create_react_agent(
        llm,
        tools=[search_offers, get_today_date],
        prompt=build_agent_prompt(search_flight_offers_instruction, 1, "This is the start of the booking process.", "Select flight offer and see if it is still valid")
    )
    
    result = search_flight_offers_agent.invoke(state)
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'search_offers'), None)
    tool_message_content = tool_message.content if tool_message and tool_message.content else None
    logger.info("tool_message_content: %s", tool_message_content)
        
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
    You are validating the user's selected flight offer to ensure it is still available and accurate.

    Follow these steps:
    1. If the user has not provided an `offer_id`, ask them to choose one of the flight offers.
    2. If they have provided an `offer_id`, use the `get_latest_offer` tool to fetch the latest details.
    3. Compare the new offer details with the originally displayed ones:
    - If there are changes or the offer is no longer valid, inform the user and ask them to pick a different offer. Restart validation.
    - If the offer is unchanged and valid, say "Let's proceed to the next step in the booking process" and proceed to the next step in the booking process. 

    Only validate one offer at a time. Be precise and polite — the user is about to finalize their choice.
    """
    
    validate_flight_offer_agent = create_react_agent(
        llm,
        tools=[get_latest_offer],
        prompt=build_agent_prompt(validate_flight_offer_instruction, 2, "User just reviewed flight options", "Collect passenger details to finalize the booking.")
    )
    
    result = validate_flight_offer_agent.invoke(state)
    
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'get_latest_offer'), None)
    tool_message_content = tool_message.content if tool_message and tool_message.content else None
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
    You are now collecting passenger details for flight booking.
    Step-by-step:
    1. Ask the user for the following required information:
    - Title (mr, ms, mrs)
    - First name
    - Last name
    - Contact number
    - Email address
    - Date of Birth (DOB) in YYYY-MM-DD format
    - Gender (m for male, f for female)
    2. Once all fields are collected, show a structured summary and ask the user to confirm everything is correct, specially the email as that is the only way to access the tickets after booking.
    3. Only after the user confirms, call the `collect_passenger_details` tool to record the information.
    4. Once complete, the process will proceed automatically to payment and booking. Ask the user to wait patiently for the payment link

    Do not call the tool without complete details. Maintain a clear, respectful tone to ensure trust.

    """
    
    collect_passenger_details_agent = create_react_agent(
        llm,
        tools=[collect_passenger_details],
        prompt=build_agent_prompt(collect_passenger_details_instruction, 3, "Flight offer was validated successfully.", "Generate a payment link and share it with the user.")
    )
    
    result = collect_passenger_details_agent.invoke(state)
    print("collect_passenger_details_node result", result)
    
    passenger_details = None
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'collect_passenger_details'), None)
    tool_message_content = tool_message.content if tool_message and tool_message.content else None
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
    
    title = passenger_details.get('title')
    first_name = passenger_details.get('first_name')
    last_name = passenger_details.get('last_name')
    date_of_birth = passenger_details.get('date_of_birth')
    contact = passenger_details.get('contact')
    email = passenger_details.get('email')
    gender = passenger_details.get('gender')

    payment_link = create_flight_booking(description, offer_id, title, first_name, last_name, contact, email, date_of_birth,gender)
    print("payment_link", payment_link)
    if not payment_link:
        payment_message = AIMessage(content="There is a problem with the payment, please try again.")
        return {
            "messages": [payment_message],
            "from_node": "create_flight_booking_node",
        }
    payment_message = AIMessage(content=f"Please make the payment using the following link: {payment_link}" + "\n" + "Once the payment is successful, the tickets will be mailed to the provided email. Hope you enjoy your trip!")
    return {
        "from_node": "create_flight_booking_node",
        "messages": [payment_message],
        "payment_link": payment_link,
    }