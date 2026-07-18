"""
TripMind AI — LangGraph node functions.

Each node receives and returns a ``state`` dict that flows through the
LangGraph pipeline.  Nodes call the Gemini LLM for intent extraction and
itinerary generation, and pull live data via the tools module.

**Mock-aware**: When the Gemini API key is missing or set to a placeholder,
the LLM-dependent nodes (extract_intent, build_itinerary) automatically
fall back to pattern-matching and template-based mock functions from
``mock_data``.  Non-LLM nodes work identically in both modes.
"""

import json
import logging
import os

from .rag import retrieve_travel_context
from .tools import fetch_places, get_weather
from .mock_data import mock_extract_intent, mock_build_itinerary

logger = logging.getLogger('agent')

# ---------------------------------------------------------------------------
# Mock-mode detection
# ---------------------------------------------------------------------------
MOCK_MODE = False

_PLACEHOLDER_KEYS = {'', 'your-api-key-here', 'CHANGE_ME', 'your_api_key'}
_gemini_api_key = os.environ.get('GEMINI_API_KEY', '')

_llm = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not _gemini_api_key or _gemini_api_key in _PLACEHOLDER_KEYS:
        MOCK_MODE = True
        logger.warning(
            'Nodes: GEMINI_API_KEY is missing or placeholder — '
            'activating MOCK mode (pattern-matching intent + template itinerary).'
        )
    else:
        MOCK_MODE = False
except ImportError as _import_err:
    MOCK_MODE = True
    logger.warning(
        f'Nodes: Could not import langchain_google_genai ({_import_err}) — '
        f'activating MOCK mode.'
    )

# ---------------------------------------------------------------------------
# Module-level LLM instance (only when NOT mocked)
# ---------------------------------------------------------------------------
if not MOCK_MODE:
    _llm = ChatGoogleGenerativeAI(
        model='gemini-2.5-flash',
        google_api_key=_gemini_api_key,
        temperature=0.7,
    )
    logger.info('Nodes: Real mode active — using Gemini LLM.')


# ---------------------------------------------------------------------------
# Helper — call the LLM and strip markdown fences
# ---------------------------------------------------------------------------
def _ask(prompt: str) -> str:
    """Invoke the LLM and return the cleaned-up text response.

    Strips leading/trailing whitespace **and** common Markdown code fences
    (````json … ````) that the model sometimes emits, even when asked not to.
    """
    import re
    response = _llm.invoke(prompt)
    text = response.content.strip()

    # 1. Try to extract from Markdown code fences
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 2. If no fences, try to extract just the array or object
    start_idx = text.find('[')
    start_obj = text.find('{')
    
    if start_idx != -1 and (start_obj == -1 or start_idx < start_obj):
        end_idx = text.rfind(']')
        if end_idx != -1:
            return text[start_idx:end_idx + 1]
            
    if start_obj != -1 and (start_idx == -1 or start_obj < start_idx):
        end_idx = text.rfind('}')
        if end_idx != -1:
            return text[start_obj:end_idx + 1]

    return text


# ====================================================================
# NODE 1 — Extract intent from the user message
# ====================================================================
def node_extract_intent(state: dict) -> dict:
    """Parse the latest user message to extract or refine trip parameters.

    Preserves previously-set values so that multi-turn conversations
    accumulate context rather than overwriting it.
    """
    user_msg = state.get('user_message', '')
    prev = {
        'destination': state.get('destination', ''),
        'num_days': state.get('num_days', 0),
        'budget_inr': state.get('budget_inr', 0),
        'category': state.get('category', 'general'),
        'group_size': state.get('group_size', 1),
        'origin_city': state.get('origin_city', ''),
    }

    # ----- MOCK MODE: pattern-matching extraction -----
    if MOCK_MODE:
        try:
            parsed = mock_extract_intent(user_msg, prev)

            for key in ('destination', 'origin_city', 'start_date', 'hotel_pref'):
                value = parsed.get(key, '')
                if value:
                    state[key] = value

            for key in ('num_days', 'budget_inr', 'group_size'):
                value = parsed.get(key, 0)
                if isinstance(value, (int, float)) and value > 0:
                    state[key] = int(value)

            category = parsed.get('category', '')
            if category and category != 'general':
                state['category'] = category
            elif 'category' not in state:
                state['category'] = 'general'

            logger.info(
                f'[MOCK] Intent extracted: dest={state.get("destination")}, '
                f'days={state.get("num_days")}, '
                f'budget={state.get("budget_inr")}'
            )
        except Exception as e:
            logger.error(f'[MOCK] node_extract_intent error: {e}')

        return state

    # ----- REAL MODE: Gemini LLM extraction -----
    prompt = f"""You are TripMind AI, a smart travel-planning assistant.

The user said:
\"\"\"{user_msg}\"\"\"

Previously known trip details (keep any that the user has not changed):
{json.dumps(prev, indent=2)}

Extract or update the following fields from the user message.  Return
**only** a JSON object — no commentary, no markdown fences.

Fields:
- destination  (string — Indian city or region, or "" if unknown)
- num_days     (integer — trip duration, or 0 if unknown)
- budget_inr   (integer — total budget in INR, or 0 if unknown)
- category     (one of: beach, adventure, family, honeymoon, food,
                spiritual, general — default "general")
- group_size   (integer — number of travellers, default 1)
- origin_city  (string — departure city, or "" if unknown)

JSON:"""

    try:
        raw = _ask(prompt)
        parsed = json.loads(raw)

        # Only overwrite state values with non-empty / non-zero updates
        for key in ('destination', 'origin_city'):
            value = parsed.get(key, '')
            if value:
                state[key] = value

        for key in ('num_days', 'budget_inr', 'group_size'):
            value = parsed.get(key, 0)
            if isinstance(value, (int, float)) and value > 0:
                state[key] = int(value)

        category = parsed.get('category', '')
        if category and category != 'general':
            state['category'] = category
        elif 'category' not in state:
            state['category'] = 'general'

        logger.info(f'Intent extracted: dest={state.get("destination")}, '
                     f'days={state.get("num_days")}, '
                     f'budget={state.get("budget_inr")}')

    except json.JSONDecodeError as e:
        logger.error(f'Intent JSON parse error: {e}')
    except Exception as e:
        logger.error(f'node_extract_intent error: {e}')

    return state


# ====================================================================
# NODE 2 — Check whether we have enough info to plan
# ====================================================================
def node_check_complete(state: dict) -> dict:
    """Set ``state['next_action']`` depending on whether the minimum
    required fields (destination + num_days) are present.
    """
    destination = state.get('destination', '')
    num_days = state.get('num_days', 0)

    if destination and num_days > 0:
        state['next_action'] = 'search_places'
    else:
        state['next_action'] = 'ask_clarification'

    return state


# ====================================================================
# NODE 3 — Ask the user for missing info
# ====================================================================
def node_ask_clarification(state: dict) -> dict:
    """Build a friendly follow-up question listing whatever fields are
    still missing.
    """
    missing: list[str] = []

    if not state.get('destination'):
        missing.append('destination (which Indian city or region?)')
    if not state.get('num_days') or state['num_days'] <= 0:
        missing.append('number of days for the trip')
    if not state.get('budget_inr') or state['budget_inr'] <= 0:
        missing.append('approximate budget in INR')
    if not state.get('origin_city'):
        missing.append('your departure / origin city')

    if missing:
        fields_text = ', '.join(missing)
        state['response'] = (
            f"I'd love to plan your trip! 🗺️ Could you tell me a bit more? "
            f"I still need: **{fields_text}**."
        )
    else:
        state['response'] = (
            "Thanks! I have everything I need — let me start planning your "
            "trip. ✈️"
        )

    return state


# ====================================================================
# NODE 4 — Search places via OpenTripMap + RAG context
# ====================================================================
def node_search_places(state: dict) -> dict:
    """Fetch live place data and augment it with RAG context from the
    local ChromaDB collection.
    """
    destination = state.get('destination', '')
    category = state.get('category', 'general')

    # --- Live places from OpenTripMap ---
    raw_places = fetch_places(destination, category)
    places: list[dict] = []
    for place_json in raw_places:
        try:
            places.append(json.loads(place_json))
        except json.JSONDecodeError:
            continue
    state['places'] = places
    logger.info(f'Fetched {len(places)} places for {destination} / {category}')

    # --- RAG context ---
    rag_query = f'{category} travel experiences in {destination}'
    rag_context = retrieve_travel_context(
        query=rag_query,
        destination=destination,
    )
    state['rag_context'] = rag_context

    return state


# ====================================================================
# NODE 5 — Build the hour-by-hour itinerary via Gemini
# ====================================================================
def node_build_itinerary(state: dict) -> dict:
    """Call Gemini to generate a structured, day-by-day itinerary.

    The prompt includes live place data (max 12), RAG context, weather,
    and strict scheduling rules.

    In mock mode, uses ``mock_build_itinerary()`` which generates a
    realistic template-based itinerary without any LLM call.
    """
    destination = state.get('destination', '')
    num_days = state.get('num_days', 1)
    budget_inr = state.get('budget_inr', 0)
    category = state.get('category', 'general')
    group_size = state.get('group_size', 1)
    places = state.get('places', [])[:12]
    rag_context = state.get('rag_context', '')

    # Optional weather data
    weather = get_weather(destination)
    weather_line = ''
    if weather:
        weather_line = (
            f"Current weather: {weather['description']}, "
            f"{weather['temp_c']}°C. "
            f"{'⚠️ Rain expected — include umbrellas/indoor backup plans.' if weather.get('rain_warning') else ''}"
        )

    # ----- MOCK MODE: template-based itinerary -----
    if MOCK_MODE:
        try:
            itinerary = mock_build_itinerary(
                destination=destination,
                num_days=num_days,
                category=category,
                budget_inr=budget_inr,
                group_size=group_size,
                places=places,
            )
            state['itinerary'] = itinerary
            state['response'] = (
                f"✅ I have meticulously crafted your {num_days}-day {category} itinerary for "
                f"{destination}."
            )
            if weather_line:
                state['response'] += f'\n\n🌤️ {weather_line}'
            logger.info(f'[MOCK] Itinerary built: {len(itinerary)} day(s)')
        except Exception as e:
            logger.error(f'[MOCK] node_build_itinerary error: {e}')
            state['itinerary'] = []
            state['response'] = (
                "Something went wrong while generating your itinerary. "
                "Please try again in a moment."
            )
        return state

    # ----- REAL MODE: Gemini LLM generation -----
    places_block = json.dumps(places, indent=2) if places else '[]'
    user_message = state.get('user_message', '')
    chat_history = state.get('chat_history', [])
    chat_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history[-6:]]) if chat_history else "No previous history."

    prompt = f"""You are TripMind AI, an expert Indian travel planner.

**Trip details**
- Destination: {destination}
- Duration: {num_days} day(s)
- Budget: ₹{budget_inr:,} INR (total for {group_size} person(s))
- Category: {category}
{weather_line}

**Recent Conversation Context**:
{chat_context}

**User's Latest Request (pay special attention to this for custom modifications)**:
{user_message}

**Available places** (use these as much as possible):
{places_block}

**Additional travel knowledge (RAG)**:
{rag_context[:2000] if rag_context else 'No additional context available.'}

**Scheduling rules — follow strictly**:
1. Each day runs from 09:00 to 21:00.
2. Breakfast at 08:30, Lunch at 13:00, Dinner at 20:00 — always include these as meal slots.
3. Add realistic transit / travel slots between places (30-60 min).
4. Every slot MUST have an estimated cost_inr (use 0 for free activities).
5. Include a maps_url for each place slot (use OpenStreetMap URLs from the place data, or generate plausible ones).
6. Cover the full {num_days} day(s).

Return **only** a JSON array — no commentary, no markdown fences.

Schema for each element:
{{
  "day": <int>,
  "title": "<string — catchy day title>",
  "slots": [
    {{
      "start_time": "<HH:MM>",
      "end_time": "<HH:MM>",
      "place": "<place name or activity>",
      "type": "<sightseeing|meal|transit|activity|shopping|rest>",
      "cost_inr": <int>,
      "notes": "<short tip or description>",
      "maps_url": "<URL>",
      "visual": {{
        "type": "<category like monument, restaurant, beach, museum, cafe, airport, etc.>",
        "city": "{destination}",
        "country": "India",
        "landmark": "<specific landmark name if applicable, else empty>",
        "keywords": ["<keyword1>", "<keyword2>"],
        "primary_query": "<detailed search query for real photos of this exact place>",
        "secondary_query": "<alternative search query>",
        "fallback_query": "<broad fallback query like city skyline or generic category>"
      }}
    }}
  ]
}}

JSON array:"""

    try:
        raw = _ask(prompt)
        parsed = json.loads(raw)
        
        if isinstance(parsed, dict):
            parsed = [parsed]
            
        itinerary = [day for day in parsed if isinstance(day, dict)]
        if not itinerary:
            raise ValueError("Parsed JSON did not contain valid day objects.")
            
        state['itinerary'] = itinerary
        state['response'] = (
            f"✅ I have meticulously crafted your {num_days}-day {category} itinerary for "
            f"{destination}."
        )
        logger.info(f'Itinerary built: {len(itinerary)} day(s)')

    except json.JSONDecodeError as e:
        logger.error(
            f'Itinerary JSON parse error: {e} — '
            f'raw (first 300 chars): {raw[:300] if raw else "<empty>"}'
        )
        state['itinerary'] = []
        state['response'] = (
            "I ran into a formatting issue while building your itinerary. "
            "Let me try again — could you repeat your request?"
        )
    except Exception as e:
        logger.error(f'node_build_itinerary error: {e}')
        state['itinerary'] = []
        state['response'] = (
            "Something went wrong while generating your itinerary. "
            "Please try again in a moment."
        )

    return state


# ====================================================================
# NODE 6 — Estimate total budget and compare
# ====================================================================
def node_estimate_budget(state: dict) -> dict:
    """Sum all ``cost_inr`` fields from the itinerary and compare against
    the user's stated budget.
    """
    itinerary = state.get('itinerary', [])
    budget_inr = state.get('budget_inr', 0)

    total_cost = 0
    for day in itinerary:
        if not isinstance(day, dict):
            continue
        slots = day.get('slots', [])
        if not isinstance(slots, list):
            continue
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            cost = slot.get('cost_inr', 0)
            if isinstance(cost, (int, float)):
                total_cost += int(cost)

    state['estimated_cost_inr'] = total_cost

    # Build budget comparison message
    response = state.get('response', '')
    if budget_inr > 0:
        diff = budget_inr - total_cost
        if diff >= 0:
            budget_msg = (
                f"\n\n💰 Estimated cost: ₹{total_cost:,} — "
                f"this beautifully aligns with your budget, leaving you ₹{diff:,} under. "
                f"Excellent value! 🎉"
            )
        else:
            budget_msg = (
                f"\n\n⚠️ Estimated cost: ₹{total_cost:,} — "
                f"this curated experience goes ₹{abs(diff):,} over your budget. "
                f"You might consider refining a few selections to stay within limits."
            )
        state['response'] = response + budget_msg
    else:
        state['response'] = (
            response +
            f"\n\n💰 Estimated trip cost: ₹{total_cost:,}"
        )

    return state
