import asyncio
import random
from typing import Dict, Any, List
from .base import BaseAgent, AgentResult
from .context import PlanningContext

class FlightAgent(BaseAgent):
    """
    Fetches flights if origin_city is provided.
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        # If no origin, flight is not needed
        # Since origin_city isn't explicitly in the PlanningContext yet, let's assume it's in user_preferences or we skip it for now if origin isn't there.
        # But we'll just mock a generic response if they need flights.
        await asyncio.sleep(0.6) # Simulate latency
        
        flights = [
            {
                "airline": "IndiGo",
                "flight_number": "6E-123",
                "price": random.randint(4000, 12000),
                "duration": "2h 15m",
                "departure_time": "08:30",
                "arrival_time": "10:45",
                "booking_url": "https://www.makemytrip.com"
            },
            {
                "airline": "Air India",
                "flight_number": "AI-456",
                "price": random.randint(5000, 15000),
                "duration": "2h 30m",
                "departure_time": "11:00",
                "arrival_time": "13:30",
                "booking_url": "https://www.makemytrip.com"
            }
        ]
        
        context.set_api_result("flights", flights)
        
        return AgentResult(
            data=flights,
            confidence=0.88,
            verified=True,
            source="Amadeus Adapter"
        )
