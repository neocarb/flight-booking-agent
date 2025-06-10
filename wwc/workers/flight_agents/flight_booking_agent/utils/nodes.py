import json
import logging
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, trim_messages

from wwc.workers.flight_agents.flight_booking_agent.utils.state import FlightBookingState
from wwc.workers.flight_agents.flight_booking_agent.utils.tools import search_offers, get_latest_offer, collect_passenger_details, get_payment_link, create_flight_booking, get_today_date, register_offer
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

reset_message = "Please click the reset button to start over"

def human_node(state: FlightBookingState):    
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
    user_input = response.get("args", "")
    
    # user_input = interrupt(last_ai_message.content)
    human_message = HumanMessage(content=user_input)
    # create a human message
    human_message = HumanMessage(content=user_input)
    return {
        "messages": [human_message]
    }

# stop child from making a booking; Handle child
# query -> confirm -> tool_call
def search_flight_offers_node(state: FlightBookingState) -> FlightBookingState:
    search_flight_offers_instruction = f"""
    You are a professional flight booking assistant helping users search for one-way flights for a single passenger.
    Your job is to help the user search for flight offers based on the following conditions:
    - Departure and destination airports or cities
    - Travel date (Today's date is {get_today_date()}, ensure the travel date is always in the future)
    
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
    - Present the options clearly in a table format
    - Include key details (airline, departure time, price) and the `offerId` for each.
    - Ask the user to select an offer by its `offerId`. Once the user selects an offer, call the `register_offer` tool to register the selected offer ID. do not tell the user that you are registering offer.

    Keep your responses helpful, concise, and professional. Ask clarifying questions if any detail is missing or ambiguous.
    """
    search_flight_offers_agent = create_react_agent(
        llm,
        tools=[search_offers, register_offer],
        prompt=build_agent_prompt(search_flight_offers_instruction, 1, "This is the start of the booking process.", "Collect passenger details from user for booking")
    )
    
    result = search_flight_offers_agent.invoke(state) # input should last x messages and the state, this helps with context issues. Can have a helper fucntion
    
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'search_offers'), None)
    flight_offers = tool_message.content if tool_message and tool_message.content else None
    
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'register_offer'), None)
    selected_flight_offer = tool_message.content if tool_message and tool_message.content else None
    logger.info("selected_flight_offer: %s", selected_flight_offer)

    msgs = trim_messages(
        result['messages'],
        max_tokens=1000,
        strategy="last",
        token_counter=ChatOpenAI(model="gpt-4o"),
        include_system=False,
        allow_partial=False,
    )

    return {
        "messages": msgs,
        'from_node': 'search_flight_offers_node',
        "flight_offers": flight_offers,
        "selected_flight_offer": selected_flight_offer
    }


# make this node more deterministic and rule based gradually
def validate_flight_offer_node(state: FlightBookingState) -> FlightBookingState:
    """
    Validates the selected flight offer against the latest offer data.
    Returns updated state with validation status and messages.
    """
    selected_offer = json.loads(state["selected_flight_offer"]) if state["selected_flight_offer"] else None
    logger.info("selected_flight_offer: %s", selected_offer)

    if not selected_offer:
        ai_message = AIMessage(content="No flight offer selected. " + reset_message)
        return {
            "messages": state["messages"] + [ai_message],
            "from_node": "validate_flight_offer_node",
            "validation_status": False,
            "selected_flight_offer": None,
        }

    selected_offer_id = selected_offer.get("offerId")
    selected_offer_price = selected_offer.get("totalCost")

    latest_offer_json = get_latest_offer(selected_offer_id)

    logger.info("latest_offer_json: %s", latest_offer_json)
    logger.info("selected_offer: %s", selected_offer)

    if not latest_offer_json:
        ai_message = AIMessage(content="Sorry, the selected offer is not available. " + reset_message)
        return {
            "messages": state["messages"] + [ai_message],
            "from_node": "validate_flight_offer_node",
            "validation_status": False,
            "selected_flight_offer": None,
        }
    
    latest_offer_price = latest_offer_json.get("offer", {}).get("totalCost")
    
    if latest_offer_price != selected_offer_price:
        ai_message = AIMessage(content="Hmm.. seems like the flight details has changed. " + reset_message)
        return {
            "messages": state["messages"] + [ai_message],
            "from_node": "validate_flight_offer_node",
            "validation_status": False,
            "selected_flight_offer": None,
        }

    # Offer is valid
    return {
        "messages": state["messages"],
        "from_node": "validate_flight_offer_node",
        "validation_status": True,
    }

def collect_passenger_details_node(state: FlightBookingState) -> FlightBookingState:
    collect_passenger_details_instruction = """
    You are now collecting passenger details for flight booking.
    Step-by-step:
    1. Ask the user for the following required information:
    - Title (mr, ms, mrs)
    - First name
    - Last name
    - Contact number (country code + number, e.g., +1 1234567890)
    - Email address (should be valid and will be used for sending the airline tickets)
    - Date of Birth (DOB) in YYYY-MM-DD format
    - Gender (m for male, f for female)
    2. Once all fields are collected, show a structured summary and ask the user to confirm everything is correct.
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
    # print("collect_passenger_details_node result", result)
    
    passenger_details = None
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'collect_passenger_details'), None)
    tool_message_content = tool_message.content if tool_message and tool_message.content else None
    logger.info("tool_message_content: %s", tool_message_content)
    tool_message_content_dict = json.loads(tool_message_content) if tool_message_content else None
    passenger_details = tool_message_content_dict.get('passenger') if tool_message_content_dict else None
    print("passenger_details", passenger_details)
    
    return {
        "messages": result['messages'],
        "from_node": "collect_passenger_details_node",
        "passenger_details": json.dumps(passenger_details) if passenger_details else None,  # corrected variable name
    }
    
def create_flight_booking_node(state: FlightBookingState) -> FlightBookingState:
    description = "Flight booking payment"
    logger.info("state: %s", state)
    selected_offer = json.loads(state["selected_flight_offer"]) if state["selected_flight_offer"] else None
    logger.info("selected_offer: %s", selected_offer)
    
    selected_offer_id = selected_offer.get("offerId") if selected_offer else None
    passenger_details = json.loads(state['passenger_details']) if state['passenger_details'] else None
    logger.info("passenger_details %s", passenger_details)
    if not passenger_details:
        payment_message = AIMessage(content="There is a problem with the payment. " + reset_message)
        return {
            "messages": [payment_message],
            "from_node": "create_flight_booking_node",
        }

    if not selected_offer_id:
        payment_message = AIMessage(content="Seems like you have not selected a valid offer. " + reset_message)
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

    payment_link = create_flight_booking(description, selected_offer_id, title, first_name, last_name, contact, email, date_of_birth,gender)
    print("payment_link", payment_link)
    if not payment_link:
        payment_message = AIMessage(content="There is a problem with the payment. " + reset_message)
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
