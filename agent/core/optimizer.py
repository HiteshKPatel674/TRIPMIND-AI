import json
import logging
from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .context import PlanningContext
from agent.nodes import _ask, MOCK_MODE, mock_build_itinerary

logger = logging.getLogger(__name__)

class OptimizerAgent(BaseAgent):
    """
    Synthesizes the final itinerary using the LLM. 
    It consumes all parallel fetched data (hotels, weather, activities).
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        destination = context.destination_canonical or context.destination
        num_days = context.budget.total_days
        budget_inr = context.budget.total_budget
        category = context.user_profile.preferences.get('category', 'general')
        group_size = context.user_profile.preferences.get('group_size', 1)
        
        hotels = context.get_api_result("hotels") or []
        weather = context.get_api_result("weather") or {}
        activities = context.get_api_result("activities") or []
        
        if MOCK_MODE:
            try:
                # Use mock activities as places for the template
                places = [{"name": a.get("name"), "type": a.get("type")} for a in activities]
                itinerary = mock_build_itinerary(
                    destination=destination,
                    num_days=num_days,
                    category=category,
                    budget_inr=budget_inr,
                    group_size=group_size,
                    places=places
                )
                return AgentResult(data={"itinerary": itinerary}, confidence=0.8, verified=False, source="MockOptimizer")
            except Exception as e:
                return AgentResult(data={"error": str(e)}, confidence=0.0)

        weather_line = f"Current weather: {weather.get('condition', 'Unknown')}, {weather.get('temp_c', '')}°C." if weather else ""

        prompt = f"""You are TripMind AI, an expert Indian travel planner.

**Trip details**
- Destination: {destination}
- Duration: {num_days} day(s)
- Budget: ₹{budget_inr:,} INR (total for {group_size} person(s))
- Category: {category}
{weather_line}

**Available places & activities** (use these as much as possible):
{json.dumps(activities, indent=2)}

**Top Hotel Recommendations**:
{json.dumps(hotels, indent=2)}

**Scheduling rules — follow strictly**:
1. Each day runs from 09:00 to 21:00.
2. Breakfast at 08:30, Lunch at 13:00, Dinner at 20:00.
3. Every slot MUST have an estimated cost_inr (use 0 for free activities).
4. Cover the full {num_days} day(s).

Return **only** a JSON array.

Schema for each element:
{{
  "day": <int>,
  "title": "<string>",
  "slots": [
    {{
      "start_time": "<HH:MM>",
      "end_time": "<HH:MM>",
      "place": "<place name>",
      "type": "<sightseeing|meal|transit|activity|hotel|shopping|rest>",
      "cost_inr": <int>,
      "notes": "<short tip>",
      "visual": {{
        "primary_query": "<detailed search query for real photos of this exact place>"
      }}
    }}
  ]
}}

JSON array:"""

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, _ask, prompt)
            parsed = json.loads(raw)
            
            if isinstance(parsed, dict):
                parsed = [parsed]
                
            return AgentResult(
                data={"itinerary": parsed},
                confidence=0.95,
                verified=True,
                source="GeminiOptimizer"
            )
        except Exception as e:
            logger.error(f'OptimizerAgent error: {e}')
            return AgentResult(data={"error": str(e)}, confidence=0.0)
