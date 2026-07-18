from .base import BaseAgent, AgentResult
from .context import PlanningContext

class BudgetAgent(BaseAgent):
    """
    Deterministic rules engine to allocate budget categories.
    No LLM used here.
    """
    
    async def execute(self, context: PlanningContext) -> AgentResult:
        total_budget = context.budget.total_budget if context.budget else 0
        num_days = max(context.budget.total_days if context.budget else 1, 1)
        group_size = max(context.user_profile.preferences.get('group_size', 1) if context.user_profile else 1, 1)
        
        per_person_per_day = total_budget / (num_days * group_size) if total_budget > 0 else 0
        
        # Determine Budget Tier
        if per_person_per_day < 2000:
            budget_tier = "Backpacker"
            utilization_target = 0.65
        elif per_person_per_day < 5000:
            budget_tier = "Budget"
            utilization_target = 0.75
        elif per_person_per_day < 12000:
            budget_tier = "Comfortable"
            utilization_target = 0.80
        elif per_person_per_day < 25000:
            budget_tier = "Premium"
            utilization_target = 0.85
        else:
            budget_tier = "Luxury"
            utilization_target = 0.90
            
        target_spend = total_budget * utilization_target
        
        # Category Allocation (can be adjusted based on user preferences in the future)
        allocations = {
            "Hotels": target_spend * 0.40,
            "Flights_Transport": target_spend * 0.25,
            "Food": target_spend * 0.20,
            "Activities": target_spend * 0.10,
            "Emergency": target_spend * 0.05
        }
        
        if context.budget:
            context.budget.allocations = allocations
        context.set_api_result("budget_tier", budget_tier)
        
        data = {
            "budget_tier": budget_tier,
            "utilization_target": utilization_target,
            "allocations": allocations
        }
        
        return AgentResult(data=data, confidence=1.0, verified=True, source="RulesEngine")
