class LeadScorer:
    def score(self, leads):
        # High-value keywords for Glambot/360 Booth clients
        high_value = ["wedding", "event", "planner", "studio", "photography", "celebration", "party", "luxury"]
        medium_value = ["marketing", "corporate", "agency", "promotion", "business"]
        
        for lead in leads:
            score = 0.4  # Base score
            text = (lead.get("description", "") + " " + lead.get("name", "")).lower()
            
            for kw in high_value:
                if kw in text: score += 0.15
            for kw in medium_value:
                if kw in text: score += 0.05
                    
            lead["score"] = round(min(score, 0.99), 2)
            
        # Sort leads so the best ones appear at the top
        return sorted(leads, key=lambda x: x["score"], reverse=True)
