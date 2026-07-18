import asyncio
from typing import Dict, Any, List
from .base import BaseAgent, AgentResult
from .context import PlanningContext

class ActivityAgent(BaseAgent):
    """
    Fetches top attractions, activities, and local experiences.
    Depends on Weather (to filter out outdoor activities if raining) 
    and Location (canonical lat/lon).
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        if not context.coordinates:
            return AgentResult(data=[], confidence=0.0, verified=False, source="System")
            
        await asyncio.sleep(0.7) # Simulate latency
        
        # Read weather from context to influence suggestions
        weather = context.get_api_result("weather")
        rain = weather.get("rain_warning", False) if weather else False
        
        activities = []
        if rain:
            activities.extend([
                {"name": f"{context.destination_canonical} National Museum", "type": "museum", "rating": 4.6, "indoor": True},
                {"name": "Local Art Gallery", "type": "gallery", "rating": 4.4, "indoor": True}
            ])
        else:
            activities.extend([
                {"name": f"{context.destination_canonical} Central Park", "type": "park", "rating": 4.7, "indoor": False},
                {"name": "Historic Fort Viewpoint", "type": "monument", "rating": 4.8, "indoor": False}
            ])
            
        # Add universal activities
        activities.extend([
            {"name": "Main Street Shopping Bazaar", "type": "shopping", "rating": 4.3, "indoor": True},
            {"name": "Local Cultural Show", "type": "entertainment", "rating": 4.5, "indoor": True}
        ])
        
        context.set_api_result("activities", activities)
        
        return AgentResult(
            data=activities,
            confidence=0.90,
            verified=True,
            source="Google Places API Adapter"
        )
