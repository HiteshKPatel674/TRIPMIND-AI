from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from .context import PlanningContext

class AgentResult:
    """Standardized response from any Agent in the DAG."""
    def __init__(self, data: Any, confidence: float = 1.0, verified: bool = False, source: str = "System"):
        self.data = data
        self.confidence = confidence
        self.verified = verified
        self.source = source
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data,
            "confidence": self.confidence,
            "verified": self.verified,
            "source": self.source
        }

class BaseAgent(ABC):
    """
    Abstract base class for all specialized micro-agents.
    """
    
    @abstractmethod
    async def execute(self, context: PlanningContext) -> AgentResult:
        """
        Execute the agent's core logic.
        Must return an AgentResult object.
        """
        pass
    
    async def run_with_fallback(self, context: PlanningContext) -> AgentResult:
        """
        Wrapper to handle timeouts and fallbacks.
        """
        try:
            return await self.execute(context)
        except Exception as e:
            # Implement global fallback logic / circuit breaking here
            return AgentResult(data={"error": str(e)}, confidence=0.0, verified=False, source="Fallback")
