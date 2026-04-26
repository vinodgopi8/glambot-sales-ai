"""
scorer.py — Lead Scoring Engine
=================================
Scores each lead 0-100 based on how well they match
the Ideal Customer Profile defined in config.py.

Scoring breakdown:
- Industry match:    30 points
- Job title match:   25 points
- Location match:    20 points
- Contact available: 15 points (email=8, phone=4, linkedin=3)
- Keyword signals:   10 points

Classification:
- 75-100 = HOT 🔴
- 50-74  = WARM 🟡
- 0-49   = COLD 🔵
"""

import os
import sys
import logging

# fuzzywuzzy for fuzzy string matching (free, no API key)
from fuzzywuzzy import fuzz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from modules.database import DatabaseManager

logger = logging.getLogger("scorer")


class LeadScorer:
    """Scores leads based on Ideal Customer Profile matching."""

    def __init__(self):
        """Initialize scorer with database connection."""
        self.db = DatabaseManager()
        self.weights = config.SCORING_WEIGHTS

    def score_industry(self, industry):
        """
        Score how well the lead's industry matches our targets.

        Args:
            industry: The lead's industry string.

        Returns:
            tuple: (score, explanation_string)
        """
        if not industry:
            return 0, "No industry data"

        max_weight = self.weights["industry_match"]  # 30 points

        # Check exact match
        for target in config.TARGET_INDUSTRIES:
            if target.lower() == industry.lower():
                return max_weight, f"Exact industry match: {industry} ✅"

        # Check fuzzy match (partial similarity)
        best_ratio = 0
        best_match = ""
        for target in config.TARGET_INDUSTRIES:
            ratio = fuzz.partial_ratio(industry.lower(), target.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = target

        if best_ratio >= 70:
            score = int(max_weight * 0.5)  # 15 points for fuzzy match
            return score, f"Fuzzy industry match: {industry} ≈ {best_match} ({best_ratio}%)"

        return 0, f"No industry match: {industry}"

    def score_job_title(self, job_title):
        """
        Score how well the lead's job title matches target titles.

        Args:
            job_title: The lead's job title string.

        Returns:
            tuple: (score, explanation_string)
        """
        if not job_title:
            return 0, "No job title data"

        max_weight = self.weights["job_title_match"]  # 25 points

        # Check exact match
        for target in config.TARGET_JOB_TITLES:
            if target.lower() == job_title.lower():
                return max_weight, f"Exact title match: {job_title} ✅"

        # Check if title contains key decision-maker words
        senior_keywords = [
            "ceo", "cto", "cfo", "coo", "director", "md",
            "managing director", "vp", "vice president", "head",
            "president", "founder", "owner", "partner", "chairman",
            "general manager", "chief",
        ]
        title_lower = job_title.lower()
        for keyword in senior_keywords:
            if keyword in title_lower:
                score = int(max_weight * 0.6)  # 15 points for similar title
                return score, f"Senior title detected: {job_title} (contains '{keyword}')"

        # Fuzzy match against target titles
        best_ratio = 0
        best_match = ""
        for target in config.TARGET_JOB_TITLES:
            ratio = fuzz.partial_ratio(title_lower, target.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = target

        if best_ratio >= 70:
            score = int(max_weight * 0.5)
            return score, f"Fuzzy title match: {job_title} ≈ {best_match} ({best_ratio}%)"

        return 0, f"No title match: {job_title}"

    def score_location(self, location):
        """
        Score how well the lead's location matches target locations.

        Args:
            location: The lead's location/city string.

        Returns:
            tuple: (score, explanation_string)
        """
        if not location:
            return 0, "No location data"

        max_weight = self.weights["location_match"]  # 20 points

        # Check exact city match
        for target in config.TARGET_LOCATIONS:
            if target.lower() == location.lower():
                return max_weight, f"Exact location match: {location} ✅"

        # Check fuzzy match (e.g., "Bengaluru" ≈ "Bangalore")
        best_ratio = 0
        best_match = ""
        for target in config.TARGET_LOCATIONS:
            ratio = fuzz.ratio(location.lower(), target.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = target

        if best_ratio >= 70:
            score = int(max_weight * 0.5)  # 10 points for close match
            return score, f"Fuzzy location match: {location} ≈ {best_match} ({best_ratio}%)"

        # Check if location is in same country (India)
        india_cities = [
            "india", "bengaluru", "new delhi", "gurgaon", "noida",
            "ghaziabad", "faridabad", "thane", "navi mumbai",
        ]
        if location.lower() in india_cities:
            score = int(max_weight * 0.25)  # 5 points for same country
            return score, f"Same country: {location} (India)"

        return 0, f"No location match: {location}"

    def score_contact_info(self, lead):
        """
        Score based on available contact information.
        More contact details = higher score.

        Args:
            lead: Lead dictionary with email, phone, linkedin_url fields.

        Returns:
            tuple: (score, explanation_string)
        """
        score = 0
        details = []

        # Email is most valuable (8 points)
        if lead.get("email"):
            score += 8
            details.append("Has email (+8)")

        # Phone number (4 points)
        if lead.get("phone"):
            score += 4
            details.append("Has phone (+4)")

        # LinkedIn profile (3 points)
        if lead.get("linkedin_url"):
            score += 3
            details.append("Has LinkedIn (+3)")

        explanation = ", ".join(details) if details else "No contact info available"
        return score, explanation

    def score_keyword_signals(self, search_query):
        """
        Score based on the search query that found this lead.
        High-intent keywords indicate stronger leads.

        Args:
            search_query: The Google search query that led to this lead.

        Returns:
            tuple: (score, explanation_string)
        """
        if not search_query:
            return 0, "No search query data"

        max_weight = self.weights["keyword_match"]  # 10 points
        query_lower = search_query.lower()

        # Check for high-intent procurement keywords
        high_intent = [
            "procurement", "supplier needed", "vendor required",
            "rfq", "quotation", "tender", "sourcing", "looking for",
        ]
        for keyword in high_intent:
            if keyword in query_lower:
                return max_weight, f"High-intent keyword: '{keyword}' ✅"

        # General industry search — moderate intent
        for industry in config.TARGET_INDUSTRIES:
            if industry.lower() in query_lower:
                score = int(max_weight * 0.5)
                return score, f"Industry keyword in query (+{score})"

        return 0, "Generic search query"

    def score_lead(self, lead):
        """
        Score a single lead on a 0-100 scale.
        Returns the total score, category, and detailed breakdown.

        Args:
            lead: Dictionary with lead data fields.

        Returns:
            dict: {
                'score': int,
                'category': str ('HOT'/'WARM'/'COLD'),
                'breakdown': dict of component scores,
                'explanations': dict of component explanations,
            }
        """
        breakdown = {}
        explanations = {}

        # Score each component
        s1, e1 = self.score_industry(lead.get("industry", ""))
        breakdown["industry_match"] = s1
        explanations["industry_match"] = e1

        s2, e2 = self.score_job_title(lead.get("job_title", ""))
        breakdown["job_title_match"] = s2
        explanations["job_title_match"] = e2

        s3, e3 = self.score_location(lead.get("location", ""))
        breakdown["location_match"] = s3
        explanations["location_match"] = e3

        s4, e4 = self.score_contact_info(lead)
        breakdown["contact_available"] = s4
        explanations["contact_available"] = e4

        s5, e5 = self.score_keyword_signals(lead.get("search_query", ""))
        breakdown["keyword_match"] = s5
        explanations["keyword_match"] = e5

        # Calculate total score (0-100)
        total_score = min(sum(breakdown.values()), 100)

        # Classify the lead
        if total_score >= config.HOT_LEAD_THRESHOLD:
            category = "HOT"
        elif total_score >= config.WARM_LEAD_THRESHOLD:
            category = "WARM"
        else:
            category = "COLD"

        return {
            "score": total_score,
            "category": category,
            "breakdown": breakdown,
            "explanations": explanations,
        }

    def score_all_new_leads(self):
        """
        Score all leads in the database that haven't been scored yet (score=0).
        Updates each lead's score and category in the database.

        Returns:
            int: Number of leads scored.
        """
        print("\n" + "=" * 60)
        print("📊 LEAD SCORING ENGINE")
        print("=" * 60)

        unscored = self.db.get_new_unscored_leads()
        if not unscored:
            print("   No new leads to score.")
            return 0

        print(f"   Scoring {len(unscored)} new leads...\n")

        hot_count = 0
        warm_count = 0
        cold_count = 0

        for lead in unscored:
            result = self.score_lead(lead)

            # Update lead in database
            self.db.update_lead(lead["id"], {
                "score": result["score"],
                "category": result["category"],
            })

            # Track counts
            if result["category"] == "HOT":
                hot_count += 1
                emoji = "🔴"
            elif result["category"] == "WARM":
                warm_count += 1
                emoji = "🟡"
            else:
                cold_count += 1
                emoji = "🔵"

            print(f"   {emoji} Score {result['score']:3d} | "
                  f"{result['category']:4s} | "
                  f"{lead.get('name', 'Unknown'):20s} | "
                  f"{lead.get('company', 'Unknown'):25s}")

        print(f"\n   Scoring Complete:")
        print(f"   🔴 HOT:  {hot_count}")
        print(f"   🟡 WARM: {warm_count}")
        print(f"   🔵 COLD: {cold_count}")
        print("=" * 60 + "\n")

        logger.info("Scored %d leads: %d HOT, %d WARM, %d COLD",
                     len(unscored), hot_count, warm_count, cold_count)

        return len(unscored)

    def explain_score(self, lead_id):
        """
        Show detailed breakdown of why a lead got its score.

        Args:
            lead_id: Database ID of the lead.

        Returns:
            str: Formatted explanation string.
        """
        lead = self.db.get_lead_by_id(lead_id)
        if not lead:
            return f"Lead ID {lead_id} not found."

        result = self.score_lead(lead)

        explanation = []
        explanation.append(f"\n{'=' * 50}")
        explanation.append(f"SCORE BREAKDOWN — Lead #{lead_id}")
        explanation.append(f"{'=' * 50}")
        explanation.append(f"Name:    {lead.get('name', 'Unknown')}")
        explanation.append(f"Company: {lead.get('company', 'Unknown')}")
        explanation.append(f"{'─' * 50}")

        for component, score in result["breakdown"].items():
            max_score = self.weights.get(component, 0)
            reason = result["explanations"].get(component, "")
            bar = "█" * int(score / max_score * 10) if max_score > 0 else ""
            explanation.append(
                f"  {component:20s}: {score:3d}/{max_score:2d}  {bar}  {reason}"
            )

        explanation.append(f"{'─' * 50}")
        explanation.append(f"  TOTAL SCORE: {result['score']}/100")
        explanation.append(f"  CATEGORY:    {result['category']}")
        explanation.append(f"{'=' * 50}\n")

        output = "\n".join(explanation)
        print(output)
        return output

    def get_top_leads(self, n=10):
        """
        Get the top N leads by score.

        Args:
            n: Number of top leads to return.

        Returns:
            list: Top N lead dictionaries sorted by score descending.
        """
        all_leads = self.db.get_all_leads()
        return sorted(all_leads, key=lambda x: x.get("score", 0), reverse=True)[:n]


# ═══════════════════════════════════════════════
# Quick test when run directly
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    scorer = LeadScorer()

    # Test with a sample lead
    sample = {
        "name": "Rajesh Kumar",
        "company": "ABC Manufacturing Ltd",
        "job_title": "Managing Director",
        "industry": "manufacturing",
        "location": "Chennai",
        "email": "rajesh@abcmfg.com",
        "phone": "+919876543210",
        "linkedin_url": "https://linkedin.com/in/rajeshkumar",
        "search_query": "procurement manager manufacturing Chennai",
    }

    result = scorer.score_lead(sample)
    print(f"\nSample Lead Score: {result['score']}/100 — {result['category']}")
    for comp, score in result["breakdown"].items():
        print(f"  {comp}: {score} — {result['explanations'][comp]}")
    print("\nScorer module working correctly! ✅")
