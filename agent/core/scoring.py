from typing import List, Dict, Any
from .context import PlanningContext

class ScoringEngine:
    """
    Evaluates a list of candidate items (hotels, restaurants, activities)
    and scores them based on a weighted matrix.
    """
    
    @staticmethod
    def score_hotels(candidates: List[Dict[str, Any]], context: PlanningContext) -> List[Dict[str, Any]]:
        """
        Score hotels based on:
        Rating (35%)
        Distance to center (20%) - Not fully implemented without coordinates, mock for now
        Budget fit (20%)
        Amenities (15%)
        Reviews (10%)
        """
        budget_allocated = context.budget_breakdown.get("Hotels", 0)
        
        for candidate in candidates:
            score = 0.0
            
            # 1. Rating (out of 5) -> 35 points max
            rating = candidate.get("rating", 3.0)
            score += (rating / 5.0) * 35
            
            # 2. Distance (Mocked for now) -> 20 points max
            # Closer is better. Assume distance in km.
            distance_km = candidate.get("distance_km", 5.0)
            dist_score = max(0, 20 - (distance_km * 2))
            score += dist_score
            
            # 3. Budget Fit -> 20 points max
            # If the hotel price for the trip fits perfectly into 80-100% of allocated budget, max points.
            price = candidate.get("total_price", 0)
            if budget_allocated > 0:
                ratio = price / budget_allocated
                if 0.5 <= ratio <= 1.0:
                    score += 20
                elif ratio > 1.0:
                    score += max(0, 20 - ((ratio - 1.0) * 20)) # Penalize over budget
                else:
                    score += 10 # Under budget is okay, but maybe not maximizing luxury
            else:
                score += 10
                
            # 4. Amenities -> 15 points max
            amenities = candidate.get("amenities", [])
            score += min(15, len(amenities) * 3)
            
            # 5. Reviews Count -> 10 points max
            reviews = candidate.get("review_count", 0)
            score += min(10, (reviews / 1000) * 10)
            
            candidate["_internal_score"] = score
            
        # Sort descending by score
        return sorted(candidates, key=lambda x: x["_internal_score"], reverse=True)
