import json
import logging
from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .context import PlanningContext
from agent.nodes import _ask, MOCK_MODE, mock_extract_intent

logger = logging.getLogger(__name__)

class IntentAgent(BaseAgent):
    """
    Analyzes the user's chat message and extracts parameters to populate the PlanningContext.
    If mandatory fields (destination, num_days) are missing, it sets a clarification flag.
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        user_msg = context.user_profile.preferences.get("last_message", "")
        if not user_msg:
            return AgentResult(data={"missing": True, "message": "What kind of trip are you looking for?"}, confidence=0.0)
            
        prev = {
            'destination': context.destination,
            'num_days': context.budget.total_days if context.budget else 0,
            'budget_inr': context.budget.total_budget if context.budget else 0,
            'category': context.user_profile.preferences.get('category', 'general'),
            'group_size': context.user_profile.preferences.get('group_size', 1),
            'origin_city': context.user_profile.preferences.get('origin_city', ''),
        }

        if MOCK_MODE:
            try:
                parsed = mock_extract_intent(user_msg, prev)
                return self._process_parsed_intent(parsed, context)
            except Exception as e:
                logger.error(f'[MOCK] IntentAgent error: {e}')
                return AgentResult(data={"error": str(e)}, confidence=0.0)
                
        prompt = f"""You are TripMind AI, a smart travel-planning assistant.

The user said:
\"\"\"{user_msg}\"\"\"

Previously known trip details (keep any that the user has not changed):
{json.dumps(prev, indent=2)}

Extract or update the following fields from the user message. Return **only** a JSON object.

Fields:
- destination  (string — Indian city or region, or "" if unknown)
- num_days     (integer — trip duration, or 0 if unknown)
- budget_inr   (integer — total budget in INR, or 0 if unknown)
- category     (one of: beach, adventure, family, honeymoon, food, spiritual, general)
- group_size   (integer — number of travellers, default 1)
- origin_city  (string — departure city, or "" if unknown)

JSON:"""

        try:
            # Temporarily block async context to call synchronous LLM
            # In a true async environment, we'd use _llm.ainvoke()
            import asyncio
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, _ask, prompt)
            parsed = json.loads(raw)
            return self._process_parsed_intent(parsed, context)
            
        except json.JSONDecodeError as e:
            logger.error(f'Intent JSON parse error: {e}')
            return AgentResult(data={"error": "json parse error"}, confidence=0.0)
        except Exception as e:
            logger.error(f'IntentAgent error: {e}')
            return AgentResult(data={"error": str(e)}, confidence=0.0)

    def _process_parsed_intent(self, parsed: dict, context: PlanningContext) -> AgentResult:
        # Populate context with extracted intent
        if parsed.get('destination'):
            context.destination = parsed['destination']
            
        from .context import BudgetBreakdown
        if parsed.get('budget_inr') or parsed.get('num_days'):
            b = parsed.get('budget_inr', 0)
            d = parsed.get('num_days', 0)
            context.budget = BudgetBreakdown(total_budget=b, total_days=d, allocations={})
            
        for k in ['category', 'group_size', 'origin_city']:
            if parsed.get(k):
                context.user_profile.preferences[k] = parsed[k]
                
        missing = []
        if not context.destination: missing.append('destination')
        if not context.budget or not context.budget.total_days: missing.append('number of days')
        if not context.budget or not context.budget.total_budget: missing.append('budget')
        
        if missing:
            return AgentResult(
                data={"complete": False, "missing": missing},
                confidence=1.0,
                verified=True,
                source="IntentExtraction"
            )
            
        return AgentResult(
            data={"complete": True, "parsed": parsed},
            confidence=0.9,
            verified=True,
            source="IntentExtraction"
        )
