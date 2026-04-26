"""
config.py — Ideal Customer Profile (ICP) Configuration
========================================================
This file defines WHO your ideal customer is.
Edit these values to match YOUR business before running.
No API keys needed. Just fill in your profile.
"""

# ═══════════════════════════════════════════════
# YOUR COMPANY DETAILS
# ═══════════════════════════════════════════════
COMPANY_NAME = "GlamBot Pro"
PRODUCT_DESCRIPTION = "AI-powered industrial automation solutions for B2B enterprises"

# ═══════════════════════════════════════════════
# IDEAL CUSTOMER PROFILE (ICP)
# ═══════════════════════════════════════════════

# Which industries should we target?
TARGET_INDUSTRIES = [
    "manufacturing",
    "logistics",
    "construction",
    "healthcare",
    "finance",
    "automotive",
    "pharma",
    "textiles",
    "chemicals",
    "food processing",
]

# Which job titles are decision makers?
TARGET_JOB_TITLES = [
    "CEO",
    "Managing Director",
    "CFO",
    "Procurement Manager",
    "Operations Head",
    "CTO",
    "VP Operations",
    "Director",
    "General Manager",
    "Head of Procurement",
    "Chief Operating Officer",
    "Founder",
]

# Which cities/locations to focus on?
TARGET_LOCATIONS = [
    "Chennai",
    "Mumbai",
    "Bangalore",
    "Delhi",
    "Hyderabad",
    "Pune",
    "Ahmedabad",
    "Kolkata",
    "Coimbatore",
    "Noida",
]

# Company size keywords to look for
COMPANY_SIZE_KEYWORDS = [
    "mid-size",
    "enterprise",
    "large",
    "multinational",
    "group of companies",
    "500+ employees",
    "1000+ employees",
]

# Search intent keywords — signals someone needs a vendor
SEARCH_KEYWORDS = [
    "looking for",
    "supplier needed",
    "vendor required",
    "procurement",
    "bulk purchase",
    "RFQ",
    "quotation request",
    "tender",
    "sourcing",
    "buy in bulk",
]

# ═══════════════════════════════════════════════
# LEAD SCORING WEIGHTS (must total 100)
# ═══════════════════════════════════════════════
SCORING_WEIGHTS = {
    "industry_match": 30,    # How well does their industry match ours?
    "job_title_match": 25,   # Is this person a decision maker?
    "location_match": 20,    # Are they in our target geography?
    "keyword_match": 15,     # Were they found via high-intent keywords?
    "contact_available": 10, # Do we have their contact details?
}

# ═══════════════════════════════════════════════
# LEAD CLASSIFICATION THRESHOLDS
# ═══════════════════════════════════════════════
HOT_LEAD_THRESHOLD = 75    # Score >= 75 → HOT 🔴
WARM_LEAD_THRESHOLD = 50   # Score 50-74 → WARM 🟡
# Score < 50 → COLD 🔵

# ═══════════════════════════════════════════════
# SCRAPING SETTINGS
# ═══════════════════════════════════════════════
MAX_LEADS_PER_RUN = 100          # Max leads to collect per run
SEARCH_DELAY_SECONDS = 3         # Base delay between Google searches
MIN_REQUEST_DELAY = 2            # Minimum seconds between web requests
MAX_REQUEST_DELAY = 5            # Maximum seconds between web requests
SEARCH_RESULTS_PER_QUERY = 10   # Number of Google results per query
MAX_RETRIES = 3                  # Retry count if blocked

# Realistic browser User-Agent to avoid being blocked
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ═══════════════════════════════════════════════
# FILE PATHS
# ═══════════════════════════════════════════════
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
CSV_PATH = os.path.join(DATA_DIR, "leads.csv")
HOT_LEADS_CSV = os.path.join(DATA_DIR, "hot_leads.csv")
REPORT_PATH = os.path.join(DATA_DIR, "report.txt")
EXISTING_CUSTOMERS_PATH = os.path.join(BASE_DIR, "existing_customers.csv")
LOG_FILE = os.path.join(LOG_DIR, "system.log")

# Create data directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ═══════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)

# ═══════════════════════════════════════════════
# SCHEDULE SETTINGS
# ═══════════════════════════════════════════════
DAILY_RUN_TIME = "09:00"  # Run pipeline daily at 9:00 AM

# ═══════════════════════════════════════════════
# DASHBOARD SETTINGS
# ═══════════════════════════════════════════════
DASHBOARD_REFRESH_SECONDS = 30  # Auto-refresh dashboard every 30 seconds
STREAMLIT_PORT = 8501
