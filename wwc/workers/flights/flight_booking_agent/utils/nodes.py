from langchain_openai import ChatOpenAI
from flight_booking_agent.utils.state import FlightBookingState
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
from flight_booking_agent.utils.tools import search_offers, get_latest_offer
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage,ToolMessage
import json

llm = ChatOpenAI(model="gpt-4o")

def human_node(state: FlightBookingState):
    # get user input
    user_input = interrupt("Enter your input: ")
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
    ai_message = result['messages'][-1]
    print("result", result)
    # get tool message from the result
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage)), None)
    if tool_message:
        tool_message_content = tool_message.content
        print("tool_message_content", tool_message_content)
        
    return {
        "messages": result['messages'],
        'from_node': 'search_flight_offers_node',
        "flight_offers": tool_message_content,
    }


# make this node more deterministic gradually
def validate_flight_offer_node(state: FlightBookingState) -> FlightBookingState:
    # This node is responsible for confirming the flight offer selected by the user.
    # It will extract the flight ID from the user's response and update the state accordingly.
    
    confirm_flight_offer_instruction = """
    You goal is to get the user to confirm their selected flight offer.
    1. If the user has not provided a offer ID, ask them to choose a flight offer to proceed with.DO NOT MAKE ANY ASSUMPTIONS ABOUT THE OFFER
    2. If the user has already provided a offer ID, validate if all the details of the offer are valid. TO validate follow the steps below
    2.1. Use the get_latest_offer tool to fetch the latest details of the offer using the offer ID provided by the user.
    2.2. Check if any of the offer details have changed compared to the original offer details.
    3. If the offer is no longer valid, inform the user and ask them to choose a new offer. Validate the new offer again as per step 2.
    4. If the offer is valid, ask the user to confirm if they want to proceed with the offer.
    5. if the user confirms then move on to the payment node.
    
    """
    
    confirm_flight_offer_agent = create_react_agent(
        llm,
        tools=[get_latest_offer],
        prompt=confirm_flight_offer_instruction
    )
    
    result = confirm_flight_offer_agent.invoke(state)
    print("validate_flight_offer_node result", result)
    
    selected_offer = None
    selected_offer_id = None
    # update state with the selected flight offer ID  
    tool_message = next((msg for msg in result['messages'] if isinstance(msg, ToolMessage) and msg.name == 'confirm_offer'), None)
    tool_message_content = tool_message.content if tool_message else None
    tool_message_content_dict = json.loads(tool_message_content) if tool_message_content else None
    selected_offer = tool_message_content_dict.get('offer') if tool_message_content_dict else None
    selected_offer_id = selected_offer.get('offerId') if selected_offer else None
    print("selected_offer", selected_offer)
    print("selected_offer_id", selected_offer_id)
    
    return {
        "messages": result['messages'],
        "from_node": "validate_flight_offer_node",
        "selected_flight_offer_id": selected_offer_id,  # corrected variable name
        "selected_flight_offer": str(selected_offer) if selected_offer else None,  # corrected variable name
    }


def make_payment_node(state: FlightBookingState) -> FlightBookingState:    
    return FlightBookingState(
        from_node="make_payment_node"
    )

def create_flight_booking_node(state: FlightBookingState) -> FlightBookingState:  
    return FlightBookingState(
        from_node="create_flight_booking_node"
    )
    
        

    
    
    
    
    
    
