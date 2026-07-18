import asyncio
import logging
from typing import Dict, Any, List, AsyncGenerator
from .context import PlanningContext
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class DAGExecutor:
    """
    Executes a Directed Acyclic Graph of agents.
    Independent agents execute concurrently using asyncio.gather.
    """
    def __init__(self):
        pass
    
    async def execute_parallel(self, agents: List[BaseAgent], context: PlanningContext) -> Dict[str, AgentResult]:
        """
        Executes a list of agents completely in parallel.
        """
        results = await asyncio.gather(*(agent.run_with_fallback(context) for agent in agents), return_exceptions=True)
        
        output = {}
        for agent, result in zip(agents, results):
            agent_name = agent.__class__.__name__
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_name} critically failed: {result}")
                output[agent_name] = AgentResult(data={"error": str(result)}, confidence=0.0, verified=False, source="System")
            else:
                output[agent_name] = result
        return output

    async def run_dag(self, context: PlanningContext) -> AsyncGenerator[str, None]:
        """
        Main execution flow defining the DAG structure. Yields progress strings.
        """
        yield "Analyzing your request..."
        
        # Step 1: Intent Extraction
        from .intent import IntentAgent
        intent_results = await self.execute_parallel([IntentAgent()], context)
        intent_res = intent_results["IntentAgent"]
        
        if intent_res.data.get("error"):
            yield f"Error: {intent_res.data['error']}"
            context.set_api_result("final_error", intent_res.data['error'])
            return
            
        if not intent_res.data.get("complete", False):
            # Missing info
            missing = intent_res.data.get("missing", [])
            fields_text = ', '.join(missing)
            msg = f"I'd love to plan your trip! 🗺️ Could you tell me a bit more? I still need: **{fields_text}**."
            yield msg
            context.set_api_result("clarification", msg)
            return

        yield "Validating destination and calculating budget..."
        
        # Step 2: Geocoding & Budget
        from .geocoder import GeocodeAgent
        from .budget import BudgetAgent
        await self.execute_parallel([GeocodeAgent(), BudgetAgent()], context)
        
        yield "Fetching live data (Hotels, Weather, Activities) in parallel..."
        
        # Step 3: Parallel Data Fetching
        from .weather import WeatherAgent
        from .hotel import HotelAgent
        from .flight import FlightAgent
        from .activity import ActivityAgent
        
        data_agents = [WeatherAgent(), HotelAgent(), FlightAgent(), ActivityAgent()]
        await self.execute_parallel(data_agents, context)
        
        yield "Synthesizing your optimized itinerary..."
        
        # Step 4: Optimization (LLM)
        from .optimizer import OptimizerAgent
        opt_results = await self.execute_parallel([OptimizerAgent()], context)
        opt_res = opt_results["OptimizerAgent"]
        
        if opt_res.data.get("error"):
            yield "Something went wrong while generating your itinerary."
            context.set_api_result("final_error", opt_res.data["error"])
            return
            
        context.set_api_result("final_itinerary", opt_res.data.get("itinerary", []))
        yield "✅ I have meticulously crafted your itinerary!"
