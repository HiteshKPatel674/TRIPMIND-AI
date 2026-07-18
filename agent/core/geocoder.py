import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any, Optional
from .base import BaseAgent, AgentResult
from .context import PlanningContext

logger = logging.getLogger(__name__)

class GeocodeAgent(BaseAgent):
    """
    Validates the destination and retrieves canonical coordinates.
    Uses OpenStreetMap (Nominatim) as a free fallback.
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        destination = context.destination
        
        # 1. Setup Nominatim URL
        query = urllib.parse.quote(destination)
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'TripMindAI/1.0 (contact@tripmind.test)'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    best_match = data[0]
                    lat = float(best_match['lat'])
                    lon = float(best_match['lon'])
                    canonical = best_match['display_name']
                    
                    # Update context directly (only safe here as it's the first sequential node)
                    context.destination_canonical = canonical
                    context.coordinates = {"lat": lat, "lon": lon}
                    
                    return AgentResult(
                        data={"lat": lat, "lon": lon, "canonical": canonical},
                        confidence=0.95,
                        verified=True,
                        source="Nominatim"
                    )
                else:
                    return self._fallback_mock(context)
                    
        except Exception as e:
            logger.warning(f"Geocoding failed for {destination}: {e}")
            return self._fallback_mock(context)
            
    def _fallback_mock(self, context: PlanningContext) -> AgentResult:
        # Fallback to mock coordinates for Indian cities
        mocks = {
            "goa": (15.2993, 74.1240),
            "delhi": (28.6139, 77.2090),
            "mumbai": (19.0760, 72.8777),
            "jaipur": (26.9124, 75.7873),
            "manali": (32.2396, 77.1887),
        }
        dest_lower = context.destination.lower()
        
        lat, lon = (0.0, 0.0)
        for key, coords in mocks.items():
            if key in dest_lower:
                lat, lon = coords
                break
                
        if lat == 0.0:
            # Default to center of India if totally unknown
            lat, lon = 20.5937, 78.9629
            
        context.destination_canonical = context.destination.title()
        context.coordinates = {"lat": lat, "lon": lon}
        
        return AgentResult(
            data={"lat": lat, "lon": lon, "canonical": context.destination_canonical},
            confidence=0.4,
            verified=False,
            source="MockFallback"
        )
