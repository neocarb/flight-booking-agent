# ✈️ Flight Booking AI Agent

An end-to-end flight booking assistant built with [LangGraph](https://github.com/langchain-ai/langgraph) that guides users through searching, selecting, and booking flights via natural conversation — with human-in-the-loop control at every step.

## How It Works

```
🔍 Search Offers → 🎯 Select Offer → ✅ Validate Offer → 📝 Passenger Details → 💳 Payment
```

1. **Search Offers** — Provide origin, destination, date, and optional preferences (cabin class, max connections, sort order). The agent queries a flight API and returns structured results.
2. **Select Offer** — Pick a flight from the list. The agent registers your selection.
3. **Validate Offer** — The system re-fetches the offer to confirm availability and that the price hasn't changed since the search.
4. **Collect Passenger Details** — The agent collects title, name, contact, email, DOB, and gender, then asks you to confirm before proceeding.
5. **Payment** — A payment link is generated. Tickets are emailed to the provided address upon successful payment.

The user is prompted for input at each transition, so nothing happens without explicit confirmation.

## Architecture

```
START
  │
  ▼
┌─────────────────────────┐
│  Search Flight Offers   │◄──────────────────┐
│  (LLM + search API)     │                   │
└───────────┬─────────────┘                   │
            │                                 │
      ┌─────┴──────┐                          │
      │ Offer      │ No                       │
      │ selected?  ├──► Human Node ───────────┘
      │            │     (get user input)
      └─────┬──────┘
        Yes │
            ▼
┌─────────────────────────┐
│  Validate Offer         │
│  (re-fetch & compare)   │
└───────────┬─────────────┘
            │
      ┌─────┴──────┐
      │ Valid?     │ No ──► END (ask user to restart)
      └─────┬──────┘
        Yes │
            ▼
┌─────────────────────────┐
│  Collect Passenger      │◄──────────────────┐
│  Details (LLM + tool)   │                   │
└───────────┬─────────────┘                   │
            │                                 │
      ┌─────┴──────┐                          │
      │ Details    │ No                       │
      │ complete?  ├──► Human Node ───────────┘
      └─────┬──────┘
        Yes │
            ▼
┌─────────────────────────┐
│  Create Booking         │
│  (API call + payment)   │
└───────────┬─────────────┘
            │
            ▼
          END (payment link shared)
```

The graph uses **conditional routing** to decide the next step based on state. LLM-driven nodes (search, passenger collection) use `create_react_agent` internally, while validation is rule-based for reliability. A shared **human node** with LangGraph interrupts handles all user input, routing back to whichever node requested it.

## State

| Field                   | Type   | Description                                |
|-------------------------|--------|--------------------------------------------|
| `messages`              | list   | Full conversation history                  |
| `selected_flight_offer` | str    | JSON of the chosen offer                   |
| `validation_status`     | bool   | Whether the offer passed validation        |
| `passenger_details`     | str    | JSON of collected passenger info           |
| `payment_link`          | str    | Generated payment URL                      |
| `from_node`             | str    | Tracks which node the human node returns to|

## Tech Stack

- **LangGraph** — State machine orchestration, conditional routing, human-in-the-loop interrupts
- **LangChain + OpenAI GPT-4o** — LLM backbone for conversational steps
- **Flight Search API** — Duffel-based flight offer search and booking
- **Razorpay** — Payment link generation

## Project Structure

```
wwc/workers/flight_agents/flight_booking_agent/
├── agent.py                 # Graph definition and compilation
└── utils/
    ├── nodes.py             # Node logic (search, validate, collect, book)
    ├── router.py            # Conditional edge functions
    ├── tools.py             # API tools (search, validate, payment, etc.)
    └── state.py             # FlightBookingState definition
```

## Getting Started

### Prerequisites

- Python 3.11+
- An OpenAI API key

### Installation

```bash
git clone <repo-url>
cd <repo-name>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-key
```

### Run

```bash
langgraph dev
```

The `flight_booking_agent` graph is registered in `langgraph.json` and will be available through the LangGraph Studio UI.

## License

MIT
