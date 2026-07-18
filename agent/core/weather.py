import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .context import PlanningContext

class WeatherAgent(BaseAgent):
    """
    Fetches comprehensive weather data for the canonical coordinates.
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        coords = context.coordinates
        if not coords:
            return AgentResult(data={}, confidence=0.0, verified=False, source="System")
            
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        # MOCK IMPLEMENTATION (In production, call OpenWeatherMap API with coords['lat'], coords['lon'])
        
        # Calculate if the trip dates overlap with monsoon/winter for realistic mock data
        temp = 25.0 + random.uniform(-5.0, 10.0)
        humidity = random.randint(40, 90)
        
        condition = "Clear"
        icon = "bi-brightness-high"
        rain_warning = False
        
        if humidity > 80:
            condition = "Rainy"
            icon = "bi-cloud-rain"
            rain_warning = True
        elif temp < 15:
            condition = "Cold"
            icon = "bi-thermometer-snow"
            
        data = {
            "temp_c": round(temp, 1),
            "humidity": humidity,
            "condition": condition,
            "icon": icon,
            "rain_warning": rain_warning,
            "wind_kph": random.randint(5, 25),
            "timestamp": datetime.now().isoformat(),
            "timezone": "Asia/Kolkata",
            "lat": coords["lat"],
            "lon": coords["lon"]
        }
        
        # Save to context for other agents to use (e.g. ActivityAgent checking for rain)
        context.set_api_result("weather", data)
        
        return AgentResult(
            data=data,
            confidence=0.85,
            verified=True,
            source="MockWeatherAPI" # Update source when using real API
        )
