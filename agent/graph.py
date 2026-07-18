"""
TripMind AI — Agent graph / pipeline orchestration.

Builds the LangGraph StateGraph that wires together all node functions.
When LangGraph is not installed, falls back to a lightweight
``SimplePipeline`` that executes the same nodes sequentially.

**Mock-aware**: Automatically detects whether ``langgraph`` is importable
and selects the appropriate execution engine.  ``run_agent()`` and
``save_itinerary_to_db()`` work identically in both modes.
"""

import logging
from typing import TypedDict, List

from .nodes import (
    node_extract_intent,
    node_check_complete,
    node_ask_clarification,
    node_search_places,
    node_build_itinerary,
    node_estimate_budget,
)

logger = logging.getLogger('agent')

# ---------------------------------------------------------------------------
# LangGraph availability detection
# ---------------------------------------------------------------------------
USE_LANGGRAPH = False

try:
    from langgraph.graph import StateGraph, END
    USE_LANGGRAPH = True
    logger.info('Graph: LangGraph available — using StateGraph pipeline.')
except ImportError:
    USE_LANGGRAPH = False
    logger.warning(
        'Graph: LangGraph not installed — '
        'using SimplePipeline (sequential node execution).'
    )


# ---------------------------------------------------------------------------
# Shared state schema
# ---------------------------------------------------------------------------
class TripState(TypedDict):
    user_message: str
    chat_history: List[dict]
    destination: str
    num_days: int
    budget_inr: int
    category: str
    hotel_pref: str
    group_size: int
    origin_city: str
    start_date: str
    places: List[dict]
    rag_context: str
    itinerary: List[dict]
    total_cost: int
    response: str
    next_action: str
    errors: List[str]


# ---------------------------------------------------------------------------
# LangGraph-based graph builder
# ---------------------------------------------------------------------------
def route_after_check(state: TripState) -> str:
    return state.get('next_action', 'ask_clarification')


def build_graph():
    """Build and compile the LangGraph StateGraph.

    Only called when ``USE_LANGGRAPH`` is True.
    """
    graph = StateGraph(TripState)

    graph.add_node('extract_intent', node_extract_intent)
    graph.add_node('check_complete', node_check_complete)
    graph.add_node('ask_clarification', node_ask_clarification)
    graph.add_node('search_places', node_search_places)
    graph.add_node('build_itinerary', node_build_itinerary)
    graph.add_node('estimate_budget', node_estimate_budget)

    graph.set_entry_point('extract_intent')

    graph.add_edge('extract_intent', 'check_complete')
    graph.add_conditional_edges(
        'check_complete',
        route_after_check,
        {
            'search_places': 'search_places',
            'ask_clarification': 'ask_clarification',
        }
    )
    graph.add_edge('ask_clarification', END)
    graph.add_edge('search_places', 'build_itinerary')
    graph.add_edge('build_itinerary', 'estimate_budget')
    graph.add_edge('estimate_budget', END)

    return graph.compile()


# ---------------------------------------------------------------------------
# SimplePipeline — fallback when LangGraph is not installed
# ---------------------------------------------------------------------------
class SimplePipeline:
    """Lightweight sequential pipeline that mirrors the LangGraph flow.

    Execution order:
        1. extract_intent → check_complete
        2. If next_action == 'search_places':
               search_places → build_itinerary → estimate_budget
        3. If next_action == 'ask_clarification':
               ask_clarification
        4. Returns final state
    """

    def invoke(self, state: dict) -> dict:
        """Run all nodes in sequence and return the final state dict."""
        # Step 1: Extract intent
        state = node_extract_intent(state)

        # Step 2: Check completeness
        state = node_check_complete(state)

        # Step 3: Route based on next_action
        next_action = state.get('next_action', 'ask_clarification')

        if next_action == 'search_places':
            state = node_search_places(state)
            state = node_build_itinerary(state)
            state = node_estimate_budget(state)
        elif next_action == 'ask_clarification':
            state = node_ask_clarification(state)
        else:
            # Unexpected action — log and ask for clarification
            logger.warning(
                f'SimplePipeline: unexpected next_action="{next_action}", '
                f'falling back to ask_clarification.'
            )
            state = node_ask_clarification(state)

        return state


# ---------------------------------------------------------------------------
# Module-level graph / pipeline instance
# ---------------------------------------------------------------------------
if USE_LANGGRAPH:
    TRIP_GRAPH = build_graph()
else:
    TRIP_GRAPH = SimplePipeline()


# ---------------------------------------------------------------------------
# Database persistence
# ---------------------------------------------------------------------------
def save_itinerary_to_db(result: dict, user, session):
    from core.models import Trip, TripVersion, ItineraryItem
    from django.core.exceptions import ValidationError
    from datetime import datetime
    
    if session.trip:
        trip = session.trip
        trip.destination = result.get('destination', trip.destination)
        trip.num_days = result.get('num_days', trip.num_days)
        trip.budget_inr = result.get('budget_inr', trip.budget_inr)
        trip.group_size = result.get('group_size', trip.group_size)
        trip.category = result.get('category', trip.category)
        trip.origin_city = result.get('origin_city', trip.origin_city)
        trip.hotel_pref = result.get('hotel_pref', trip.hotel_pref)
        raw_start = result.get('start_date')
        if raw_start:
            try:
                datetime.strptime(raw_start, '%Y-%m-%d')
                trip.start_date = raw_start
            except ValueError:
                pass
        trip.save()
    else:
        raw_start = result.get('start_date')
        valid_start = None
        if raw_start:
            try:
                datetime.strptime(raw_start, '%Y-%m-%d')
                valid_start = raw_start
            except ValueError:
                pass
                
        trip = Trip.objects.create(
            user=user,
            destination=result.get('destination', ''),
            num_days=result.get('num_days', 3),
            budget_inr=result.get('budget_inr', 0),
            group_size=result.get('group_size', 1),
            category=result.get('category', 'general'),
            origin_city=result.get('origin_city', ''),
            hotel_pref=result.get('hotel_pref', ''),
            start_date=valid_start,
        )
        session.trip = trip

    # Create a new version
    version_num = TripVersion.objects.filter(trip=trip).count() + 1
    version = TripVersion.objects.create(
        trip=trip,
        version_number=version_num,
        itinerary_json=result.get('itinerary', [])
    )
    
    items = []
    for day in result.get('itinerary', []):
        if not isinstance(day, dict):
            continue
        day_number = day.get('day', 1)
        slots = day.get('slots', [])
        if not isinstance(slots, list):
            continue
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            items.append(ItineraryItem(
                version=version,
                day_number=day_number,
                start_time=slot.get('start_time', '09:00'),
                end_time=slot.get('end_time', '10:00'),
                place_name=slot.get('place', ''),
                place_type=slot.get('type', 'attraction'),
                description=slot.get('notes', ''),
                cost_inr=slot.get('cost_inr', 0),
                maps_url=slot.get('maps_url', ''),
                visual_metadata=slot.get('visual')
            ))
            
    ItineraryItem.objects.bulk_create(items)
    return trip


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_agent(user_message: str, session) -> tuple:
    initial_state = {
        'user_message': user_message,
        'chat_history': session.messages[-10:] if session.messages else [],
        'destination': session.graph_state.get('destination', ''),
        'num_days': session.graph_state.get('num_days', 0),
        'budget_inr': session.graph_state.get('budget_inr', 0),
        'category': session.graph_state.get('category', 'general'),
        'group_size': session.graph_state.get('group_size', 1),
        'origin_city': session.graph_state.get('origin_city', ''),
        'hotel_pref': session.graph_state.get('hotel_pref', ''),
        'start_date': session.graph_state.get('start_date', ''),
        'places': [],
        'rag_context': '',
        'itinerary': [],
        'total_cost': 0,
        'response': '',
        'next_action': '',
        'errors': []
    }
    
    result = TRIP_GRAPH.invoke(initial_state)
    
    session.graph_state = {
        'destination': result.get('destination', ''),
        'num_days': result.get('num_days', 0),
        'budget_inr': result.get('budget_inr', 0),
        'category': result.get('category', 'general'),
        'group_size': result.get('group_size', 1),
        'origin_city': result.get('origin_city', ''),
        'hotel_pref': result.get('hotel_pref', ''),
        'start_date': result.get('start_date', ''),
    }
    
    if result.get('itinerary'):
        save_itinerary_to_db(result, session.user, session)
        
    session.messages.append({'role': 'assistant', 'content': result.get('response', '')})
    session.save()
    
    return result.get('response', ''), session
