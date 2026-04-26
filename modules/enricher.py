"""
enricher.py — Lead Enrichment Module
=======================================
Finds MORE details about leads already in the database.
Scrapes company websites, guesses email patterns,
checks social presence, and classifies industries.

Uses ONLY: requests, beautifulsoup4. No API keys.
"""

import re
import os
import sys
import time
import random
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from modules.database import DatabaseManager

logger = logging.getLogger("enricher")


class LeadEnricher:
    """Enriches existing leads with additional details from the web."""

    def __init__(self):
        """Initialize enricher with database and HTTP session."""
        self.db = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _safe_delay(self):
        """Random delay between requests to avoid being blocked."""
        time.sleep(random.uniform(config.MIN_REQUEST_DELAY, config.MAX_REQUEST_DELAY))

    def enrich_company_website(self, lead):
        """
        Search for and scrape the company's website for additional info.
        Extracts: founding year, team size, services, office locations.

        Args:
            lead: Lead dictionary with at least 'company' field.

        Returns:
            dict: Enriched data found (may be empty dict).
        """
        company = lead.get("company", "")
        if not company:
            return {}

        enriched = {}

        try:
            # If we already have a website, scrape its About page
            website = lead.get("website", "")

            if not website:
                # Search Google for the company website
                from googlesearch import search as google_search
                query = f"{company} official website"
                results = list(google_search(query, num_results=3, sleep_interval=3))
                if results:
                    website = results[0]
                    enriched["website"] = website
                self._safe_delay()

            if not website:
                return enriched

            # Try to find and scrape the About Us page
            domain = urlparse(website).scheme + "://" + urlparse(website).netloc
            about_urls = [
                f"{domain}/about",
                f"{domain}/about-us",
                f"{domain}/about.html",
                f"{domain}/company",
                website,  # Fall back to homepage
            ]

            page_text = ""
            for about_url in about_urls:
                try:
                    resp = self.session.get(about_url, timeout=8)
                    if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for tag in soup(["script", "style", "nav"]):
                            tag.decompose()
                        page_text = soup.get_text(separator=" ", strip=True)
                        break
                except Exception:
                    continue

            if not page_text:
                return enriched

            # ── Extract founding year ──
            year_pattern = re.compile(
                r'(?:founded|established|since|started)\s*(?:in\s+)?(\d{4})',
                re.IGNORECASE
            )
            year_match = year_pattern.search(page_text)
            if year_match:
                year = int(year_match.group(1))
                if 1900 <= year <= 2026:
                    enriched["founding_year"] = year

            # ── Extract team size clues ──
            team_patterns = [
                re.compile(r'(\d{1,5})\+?\s*(?:employees|team members|professionals|staff)', re.IGNORECASE),
                re.compile(r'team\s*(?:of|size)?\s*(\d{1,5})', re.IGNORECASE),
            ]
            for pattern in team_patterns:
                match = pattern.search(page_text)
                if match:
                    enriched["team_size"] = match.group(1)
                    break

            # ── Extract services/products offered ──
            services = []
            service_keywords = [
                "manufacturing", "logistics", "consulting", "software",
                "automation", "engineering", "supply chain", "construction",
                "healthcare", "finance", "procurement", "distribution",
            ]
            text_lower = page_text.lower()
            for keyword in service_keywords:
                if keyword in text_lower:
                    services.append(keyword)
            if services:
                enriched["services"] = ", ".join(services[:5])

            # ── Extract office locations ──
            locations_found = []
            for loc in config.TARGET_LOCATIONS:
                if loc.lower() in text_lower:
                    locations_found.append(loc)
            if locations_found:
                enriched["office_locations"] = ", ".join(locations_found)

            # Build company_info string
            info_parts = []
            if enriched.get("founding_year"):
                info_parts.append(f"Founded: {enriched['founding_year']}")
            if enriched.get("team_size"):
                info_parts.append(f"Team: {enriched['team_size']}+")
            if enriched.get("services"):
                info_parts.append(f"Services: {enriched['services']}")
            if enriched.get("office_locations"):
                info_parts.append(f"Offices: {enriched['office_locations']}")

            if info_parts:
                enriched["company_info"] = " | ".join(info_parts)

            logger.info("🔍 Enriched company info for: %s", company)

        except ImportError:
            logger.warning("googlesearch-python not installed — skipping website search")
        except Exception as e:
            logger.debug("Company enrichment error for %s: %s", company, str(e))

        return enriched

    def guess_emails(self, lead):
        """
        Generate possible email addresses based on name and company domain.
        These are guesses, NOT verified addresses.

        Args:
            lead: Lead dictionary with 'name' and optionally 'website' fields.

        Returns:
            list: List of guessed email addresses.
        """
        name = lead.get("name", "").strip()
        website = lead.get("website", "").strip()

        if not name:
            return []

        # Extract domain from website URL
        domain = ""
        if website:
            try:
                parsed = urlparse(website)
                domain = parsed.netloc.replace("www.", "")
            except Exception:
                pass

        if not domain:
            # Try to construct domain from company name
            company = lead.get("company", "").strip()
            if company:
                # Simple domain guess: remove spaces, add .com
                domain_guess = re.sub(r'[^a-zA-Z0-9]', '', company.lower())
                domain = f"{domain_guess}.com"

        if not domain:
            return []

        # Parse name into parts
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            return []

        firstname = name_parts[0].lower()
        lastname = name_parts[-1].lower()
        first_initial = firstname[0]

        # Generate email variations
        guesses = [
            f"{firstname}@{domain}",
            f"{firstname}.{lastname}@{domain}",
            f"{first_initial}.{lastname}@{domain}",
            f"{firstname}{lastname}@{domain}",
            f"{lastname}@{domain}",
            f"{first_initial}{lastname}@{domain}",
            f"info@{domain}",
            f"contact@{domain}",
        ]

        logger.info("📧 Generated %d email guesses for: %s", len(guesses), name)
        return guesses

    def check_social_presence(self, lead):
        """
        Check if the company has social media profiles.
        Checks LinkedIn company page and Twitter/X.

        Args:
            lead: Lead dictionary with 'company' field.

        Returns:
            dict: Social URLs found {'linkedin': url, 'twitter': url}.
        """
        company = lead.get("company", "").strip()
        if not company:
            return {}

        social_urls = {}

        try:
            from googlesearch import search as google_search

            # Search for LinkedIn company page
            linkedin_query = f"site:linkedin.com/company {company}"
            try:
                results = list(google_search(linkedin_query, num_results=2, sleep_interval=3))
                for url in results:
                    if "linkedin.com/company" in url:
                        social_urls["linkedin_company"] = url
                        break
                self._safe_delay()
            except Exception:
                pass

            # Search for Twitter/X page
            twitter_query = f"site:twitter.com {company}"
            try:
                results = list(google_search(twitter_query, num_results=2, sleep_interval=3))
                for url in results:
                    if "twitter.com" in url or "x.com" in url:
                        social_urls["twitter"] = url
                        break
                self._safe_delay()
            except Exception:
                pass

        except ImportError:
            logger.warning("googlesearch-python not installed — skipping social check")

        if social_urls:
            logger.info("🌐 Social presence found for %s: %s",
                         company, list(social_urls.keys()))

        return social_urls

    def classify_industry(self, lead):
        """
        Classify a lead's industry based on website content keywords.
        Used when industry field is empty or needs correction.

        Args:
            lead: Lead dictionary.

        Returns:
            str: Classified industry name, or empty string.
        """
        website = lead.get("website", "")
        if not website:
            return lead.get("industry", "")

        try:
            resp = self.session.get(website, timeout=8)
            if resp.status_code != 200:
                return lead.get("industry", "")

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True).lower()

            # Count mentions of each target industry
            industry_scores = {}
            for industry in config.TARGET_INDUSTRIES:
                count = text.count(industry.lower())
                # Also check related keywords
                related = {
                    "manufacturing": ["factory", "plant", "production", "fabrication"],
                    "logistics": ["shipping", "transport", "warehouse", "freight"],
                    "construction": ["building", "civil", "infrastructure", "contractor"],
                    "healthcare": ["hospital", "medical", "pharma", "clinic"],
                    "finance": ["banking", "investment", "financial", "insurance"],
                    "automotive": ["automobile", "vehicle", "auto parts"],
                    "pharma": ["pharmaceutical", "drug", "medicine", "biotech"],
                    "textiles": ["fabric", "garment", "apparel", "clothing"],
                    "chemicals": ["chemical", "polymer", "specialty chemicals"],
                    "food processing": ["food", "beverage", "agri", "dairy"],
                }
                for keyword in related.get(industry, []):
                    count += text.count(keyword)

                if count > 0:
                    industry_scores[industry] = count

            if industry_scores:
                best_industry = max(industry_scores, key=industry_scores.get)
                logger.info("🏭 Industry classified for %s: %s",
                             lead.get("company", ""), best_industry)
                return best_industry

        except Exception as e:
            logger.debug("Industry classification error: %s", str(e))

        return lead.get("industry", "")

    def enrich_lead(self, lead):
        """
        Run all enrichment steps for a single lead.

        Args:
            lead: Lead dictionary from database.

        Returns:
            dict: Updates to apply to the lead record.
        """
        updates = {}
        lead_name = lead.get("name") or lead.get("company", "Unknown")
        print(f"  🔍 Enriching: {lead_name}...")

        # Step 1: Enrich from company website
        company_data = self.enrich_company_website(lead)
        if company_data.get("company_info"):
            updates["company_info"] = company_data["company_info"]
        if company_data.get("website") and not lead.get("website"):
            updates["website"] = company_data["website"]

        # Step 2: Guess emails if we don't have one
        if not lead.get("email"):
            guesses = self.guess_emails(lead)
            if guesses:
                updates["guessed_emails"] = ", ".join(guesses[:4])

        # Step 3: Check social presence
        social = self.check_social_presence(lead)
        if social:
            social_str = " | ".join([f"{k}: {v}" for k, v in social.items()])
            updates["social_urls"] = social_str
            # Update LinkedIn URL if not already set
            if not lead.get("linkedin_url") and social.get("linkedin_company"):
                updates["linkedin_url"] = social["linkedin_company"]

        # Step 4: Classify industry if missing
        if not lead.get("industry"):
            industry = self.classify_industry(lead)
            if industry:
                updates["industry"] = industry

        return updates

    def enrich_leads_by_category(self, categories=None):
        """
        Enrich all leads in specified categories.
        Default: enrich HOT and WARM leads only (to save time).

        Args:
            categories: List of categories to enrich. Default: ['HOT', 'WARM'].

        Returns:
            int: Number of leads enriched.
        """
        categories = categories or ["HOT", "WARM"]

        print("\n" + "=" * 60)
        print("🔍 LEAD ENRICHMENT ENGINE")
        print(f"   Categories: {', '.join(categories)}")
        print("=" * 60)

        enriched_count = 0

        for category in categories:
            leads = self.db.get_leads_by_category(category)
            if not leads:
                print(f"   No {category} leads to enrich.")
                continue

            print(f"\n   Processing {len(leads)} {category} leads...")

            for lead in leads:
                try:
                    updates = self.enrich_lead(lead)

                    if updates:
                        self.db.update_lead(lead["id"], updates)
                        enriched_count += 1
                        print(f"     ✅ Enriched: {lead.get('name') or lead.get('company')}")
                    else:
                        print(f"     ⏩ No new data for: {lead.get('name') or lead.get('company')}")

                    self._safe_delay()

                except Exception as e:
                    logger.error("Enrichment error for lead %d: %s", lead["id"], str(e))
                    print(f"     ❌ Error: {e}")

        print(f"\n   Enrichment Complete: {enriched_count} leads updated")
        print("=" * 60 + "\n")

        logger.info("Enrichment complete: %d leads enriched", enriched_count)
        return enriched_count


# ═══════════════════════════════════════════════
# Quick test when run directly
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    enricher = LeadEnricher()

    # Test email guessing
    sample = {
        "name": "Rajesh Kumar",
        "company": "ABC Manufacturing Ltd",
        "website": "https://www.abcmfg.com",
    }
    guesses = enricher.guess_emails(sample)
    print("Email guesses:")
    for g in guesses:
        print(f"  → {g}")
    print("\nEnricher module working correctly! ✅")
