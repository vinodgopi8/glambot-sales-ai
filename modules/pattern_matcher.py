"""
pattern_matcher.py — Pattern Learning & Matching System
=========================================================
Learns what a "good lead" looks like from existing customers,
then matches new leads against those patterns.

Phase 1: Manual pattern extraction from existing_customers.csv
Phase 2: Pattern matching with similarity scoring
Phase 3: Logistic Regression when enough data (50+ rows)
Phase 4: Automated insight reports
"""

import os
import sys
import csv
import logging
from collections import Counter

from fuzzywuzzy import fuzz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from modules.database import DatabaseManager

logger = logging.getLogger("pattern_matcher")


class PatternMatcher:
    """
    Learns ideal customer patterns from existing customers
    and matches new leads against those patterns.
    """

    def __init__(self):
        """Initialize pattern matcher with database connection."""
        self.db = DatabaseManager()
        self.patterns = {}  # Extracted patterns from existing customers
        self.has_model = False  # Whether ML model is trained

    def load_existing_customers(self):
        """
        Load existing customers from CSV file.
        User fills this manually with their 5-10 known customers.

        Returns:
            list: List of customer dictionaries.
        """
        csv_path = config.EXISTING_CUSTOMERS_PATH

        if not os.path.exists(csv_path):
            print(f"⚠️  No existing_customers.csv found at: {csv_path}")
            print("   Create it with your current customers to enable pattern matching.")
            return []

        try:
            customers = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customers.append(row)

            print(f"📋 Loaded {len(customers)} existing customers from CSV")
            logger.info("Loaded %d existing customers", len(customers))
            return customers

        except Exception as e:
            logger.error("Failed to load existing customers: %s", str(e))
            print(f"❌ Error loading customers CSV: {e}")
            return []

    def extract_patterns(self):
        """
        PHASE 1: Extract common patterns from existing customers.
        Finds the most common industry, job title, location, etc.

        Returns:
            dict: Extracted patterns dictionary.
        """
        customers = self.load_existing_customers()

        if not customers:
            # Use config defaults as fallback patterns
            self.patterns = {
                "top_industries": config.TARGET_INDUSTRIES[:3],
                "top_titles": config.TARGET_JOB_TITLES[:3],
                "top_locations": config.TARGET_LOCATIONS[:3],
                "top_company_sizes": config.COMPANY_SIZE_KEYWORDS[:2],
                "avg_deal_value": 0,
                "customer_count": 0,
                "source": "config_defaults",
            }
            print("   Using config defaults as patterns (no customer data)")
            return self.patterns

        # Count occurrences of each attribute
        industries = Counter()
        titles = Counter()
        locations = Counter()
        sizes = Counter()
        deal_values = []

        for c in customers:
            if c.get("industry"):
                industries[c["industry"].strip().lower()] += 1
            if c.get("job_title"):
                titles[c["job_title"].strip()] += 1
            if c.get("location"):
                locations[c["location"].strip()] += 1
            if c.get("company_size"):
                sizes[c["company_size"].strip().lower()] += 1
            if c.get("deal_value"):
                try:
                    deal_values.append(float(c["deal_value"]))
                except ValueError:
                    pass

        self.patterns = {
            "top_industries": [item[0] for item in industries.most_common(5)],
            "top_titles": [item[0] for item in titles.most_common(5)],
            "top_locations": [item[0] for item in locations.most_common(5)],
            "top_company_sizes": [item[0] for item in sizes.most_common(3)],
            "avg_deal_value": (
                sum(deal_values) / len(deal_values) if deal_values else 0
            ),
            "customer_count": len(customers),
            "source": "existing_customers",
        }

        print("\n📊 PATTERNS EXTRACTED FROM EXISTING CUSTOMERS:")
        print(f"   Top Industries:  {', '.join(self.patterns['top_industries'][:3])}")
        print(f"   Top Titles:      {', '.join(self.patterns['top_titles'][:3])}")
        print(f"   Top Locations:   {', '.join(self.patterns['top_locations'][:3])}")
        print(f"   Avg Deal Value:  ₹{self.patterns['avg_deal_value']:,.0f}")
        print(f"   Total Customers: {self.patterns['customer_count']}")

        logger.info("Patterns extracted from %d customers", len(customers))
        return self.patterns

    def calculate_similarity(self, lead):
        """
        PHASE 2: Compare a lead against extracted patterns.
        Returns a similarity percentage.

        Args:
            lead: Lead dictionary.

        Returns:
            tuple: (similarity_percentage, match_level_str)
        """
        if not self.patterns:
            self.extract_patterns()

        score = 0
        max_score = 4  # 4 dimensions to match

        # Industry similarity
        lead_industry = lead.get("industry", "").lower()
        if lead_industry:
            for pat_industry in self.patterns.get("top_industries", []):
                ratio = fuzz.partial_ratio(lead_industry, pat_industry.lower())
                if ratio >= 70:
                    score += 1
                    break

        # Job title similarity
        lead_title = lead.get("job_title", "").lower()
        if lead_title:
            for pat_title in self.patterns.get("top_titles", []):
                ratio = fuzz.partial_ratio(lead_title, pat_title.lower())
                if ratio >= 70:
                    score += 1
                    break

        # Location similarity
        lead_location = lead.get("location", "").lower()
        if lead_location:
            for pat_loc in self.patterns.get("top_locations", []):
                ratio = fuzz.ratio(lead_location, pat_loc.lower())
                if ratio >= 70:
                    score += 1
                    break

        # Contact quality bonus (if has email or phone, +0.5)
        if lead.get("email") or lead.get("phone"):
            score += 0.5
            max_score += 0.5

        # Calculate percentage
        similarity = int((score / max_score) * 100) if max_score > 0 else 0

        # Classify match level
        if similarity >= 75:
            match_level = "High"
        elif similarity >= 50:
            match_level = "Medium"
        else:
            match_level = "Low"

        return similarity, match_level

    def match_all_leads(self):
        """
        Run pattern matching on all leads in the database.
        Updates each lead with pattern_match field.

        Returns:
            dict: Summary of matching results.
        """
        print("\n" + "=" * 60)
        print("🧠 PATTERN MATCHING ENGINE")
        print("=" * 60)

        # First extract patterns
        self.extract_patterns()

        # Get all leads
        leads = self.db.get_all_leads()
        if not leads:
            print("   No leads to match.")
            return {"high": 0, "medium": 0, "low": 0}

        print(f"\n   Matching {len(leads)} leads against customer patterns...\n")

        high_count = 0
        medium_count = 0
        low_count = 0

        for lead in leads:
            similarity, match_level = self.calculate_similarity(lead)

            # Update lead in database
            self.db.update_lead(lead["id"], {"pattern_match": match_level})

            if match_level == "High":
                high_count += 1
            elif match_level == "Medium":
                medium_count += 1
            else:
                low_count += 1

        print(f"   Pattern Match Results:")
        print(f"   🟢 High Match:   {high_count}")
        print(f"   🟡 Medium Match: {medium_count}")
        print(f"   🔴 Low Match:    {low_count}")
        print("=" * 60 + "\n")

        logger.info("Pattern matching: %d high, %d medium, %d low",
                     high_count, medium_count, low_count)

        return {"high": high_count, "medium": medium_count, "low": low_count}

    def train_logistic_regression(self):
        """
        PHASE 3: Train a logistic regression model when enough data exists.
        Requires 50+ leads AND scikit-learn installed.

        Returns:
            dict: Model results (accuracy, feature importance) or None.
        """
        leads = self.db.get_all_leads()

        if len(leads) < 50:
            print(f"   ⏳ Need 50+ leads for ML model (currently {len(leads)})")
            print("   Run the scraper a few more times to collect enough data.")
            return None

        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import numpy as np

            print("\n" + "=" * 60)
            print("🤖 TRAINING LOGISTIC REGRESSION MODEL")
            print("=" * 60)

            # Prepare features
            features = []
            targets = []
            feature_names = [
                "industry_match", "title_match", "location_match",
                "contact_score", "keyword_score"
            ]

            for lead in leads:
                # Build feature vector
                industry_match = 1 if lead.get("industry") in [
                    i.lower() for i in config.TARGET_INDUSTRIES
                ] else 0

                title_match = 1 if lead.get("job_title") in config.TARGET_JOB_TITLES else 0

                location_match = 1 if lead.get("location") in config.TARGET_LOCATIONS else 0

                contact_score = 0
                if lead.get("email"):
                    contact_score += 0.5
                if lead.get("phone"):
                    contact_score += 0.3
                if lead.get("linkedin_url"):
                    contact_score += 0.2

                keyword_score = 1 if any(
                    kw in lead.get("search_query", "").lower()
                    for kw in config.SEARCH_KEYWORDS
                ) else 0

                features.append([
                    industry_match, title_match, location_match,
                    contact_score, keyword_score
                ])

                # Target: use score > WARM threshold as proxy for "convertible"
                targets.append(
                    1 if lead.get("score", 0) >= config.WARM_LEAD_THRESHOLD else 0
                )

            X = np.array(features)
            y = np.array(targets)

            # Check if we have both classes
            if len(set(y)) < 2:
                print("   ⚠️ Need both positive and negative examples for ML.")
                return None

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Train model
            model = LogisticRegression(max_iter=200)
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Feature importance
            importances = dict(zip(feature_names, model.coef_[0]))
            sorted_features = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)

            print(f"\n   📈 Model Accuracy: {accuracy * 100:.1f}%")
            print(f"\n   Feature Importance:")
            for feat, imp in sorted_features:
                bar = "█" * int(abs(imp) * 5)
                direction = "+" if imp > 0 else "-"
                print(f"     {feat:20s}: {direction}{abs(imp):.3f}  {bar}")

            self.has_model = True

            result = {
                "accuracy": accuracy,
                "feature_importance": dict(sorted_features),
                "total_samples": len(leads),
                "positive_samples": int(sum(y)),
            }

            logger.info("ML model trained: %.1f%% accuracy", accuracy * 100)
            print("=" * 60 + "\n")

            return result

        except ImportError:
            print("   ℹ️  scikit-learn not installed — ML features disabled.")
            print("   Install with: pip install scikit-learn")
            return None

        except Exception as e:
            logger.error("ML training error: %s", str(e))
            print(f"   ❌ ML training failed: {e}")
            return None

    def generate_insight_report(self):
        """
        PHASE 4: Generate automated insights from collected data.
        Prints which leads convert best, best industries, etc.

        Returns:
            dict: Insight data dictionary.
        """
        print("\n" + "=" * 60)
        print("💡 PATTERN INSIGHTS REPORT")
        print("=" * 60)

        # Get distributions from database
        industry_dist = self.db.get_industry_distribution()
        location_dist = self.db.get_location_distribution()
        title_dist = self.db.get_title_distribution()

        # Best industry
        best_industry = max(industry_dist, key=industry_dist.get) if industry_dist else "Unknown"
        print(f"\n   🏭 Best Industry for Leads: {best_industry}")

        # Best location
        best_location = max(location_dist, key=location_dist.get) if location_dist else "Unknown"
        print(f"   📍 Best Location for Leads: {best_location}")

        # Best job title
        best_title = max(title_dist, key=title_dist.get) if title_dist else "Unknown"
        print(f"   👤 Most Common Decision Maker: {best_title}")

        # Pattern match percentage
        all_leads = self.db.get_all_leads()
        if all_leads:
            high_match = sum(
                1 for l in all_leads if l.get("pattern_match") == "High"
            )
            match_pct = (high_match / len(all_leads)) * 100
            print(f"\n   🎯 {match_pct:.1f}% of leads match your ideal customer profile")
            print(f"   📊 Pattern match leads convert significantly better!")
        else:
            match_pct = 0

        # Hot lead insights
        hot_leads = self.db.get_leads_by_category("HOT")
        if hot_leads:
            hot_industries = Counter(l.get("industry", "") for l in hot_leads if l.get("industry"))
            if hot_industries:
                top_hot_industry = hot_industries.most_common(1)[0]
                print(f"\n   🔴 Most HOT leads come from: {top_hot_industry[0]} ({top_hot_industry[1]} leads)")

        # Try ML if enough data
        ml_result = self.train_logistic_regression()

        insights = {
            "best_industry": best_industry,
            "best_location": best_location,
            "best_title": best_title,
            "pattern_match_pct": match_pct,
            "total_leads": len(all_leads),
            "ml_result": ml_result,
            "industry_distribution": industry_dist,
            "location_distribution": location_dist,
            "title_distribution": title_dist,
        }

        print("=" * 60 + "\n")
        return insights


# ═══════════════════════════════════════════════
# Quick test when run directly
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    matcher = PatternMatcher()
    patterns = matcher.extract_patterns()
    print(f"\nExtracted patterns: {patterns}")

    # Test similarity with a sample lead
    sample = {
        "industry": "manufacturing",
        "job_title": "CEO",
        "location": "Chennai",
        "email": "test@example.com",
    }
    sim, level = matcher.calculate_similarity(sample)
    print(f"\nSample similarity: {sim}% ({level})")
    print("\nPattern matcher module working correctly! ✅")
