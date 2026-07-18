from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import date

class BudgetBreakdown(BaseModel):
    total_budget: int = 0
    total_days: int = 0
    allocations: Dict[str, float] = Field(default_factory=dict)

class PlanningContext(BaseModel):
    """
    The immutable context object passed through the DAG.
    Agents read from this context and write back to specific keys in a state dictionary
    to avoid mutating the shared context directly in ways that cause race conditions.
    """
    trip_id: str = ""
    destination: str = ""
    destination_canonical: str = ""
    coordinates: Optional[Dict[str, float]] = None  # {"lat": ..., "lon": ...}
    country: str = ""
    
    budget: Optional[BudgetBreakdown] = None
    
    # Store the Django UserProfile model or a mock profile
    user_profile: Any = None
    
    # Storage for external API results
    api_results: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = False
        arbitrary_types_allowed = True

    def set_api_result(self, key: str, value: Any):
        self.api_results[key] = value

    def get_api_result(self, key: str) -> Any:
        return self.api_results.get(key)
