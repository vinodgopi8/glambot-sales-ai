# 🚀 Lead Generation System

**AI-Powered • Zero API Keys • 100% Free**

Automatically finds potential B2B customers from the internet, scores them against your Ideal Customer Profile, and displays everything in a live professional dashboard.

---

## ✅ Features

- 🔍 **Auto Google Search** — Builds smart queries from your ICP and scrapes results
- 📊 **Lead Scoring** — Scores 0-100 with fuzzy matching (industry, title, location, contact, intent)
- 🔴🟡🔵 **Classification** — HOT / WARM / COLD categorization
- 🔍 **Enrichment** — Scrapes company websites, guesses emails, finds social profiles
- 🧠 **Pattern Matching** — Learns from your existing customers, predicts best leads
- 🤖 **ML Ready** — Logistic Regression activates automatically at 50+ leads
- 📈 **Live Dashboard** — Professional Streamlit UI with Plotly charts
- 📋 **Reports** — Daily summaries, hot lead alerts, CSV exports
- ⏰ **Scheduling** — Runs automatically every day at 9 AM

---

## 🛠️ Setup (5 minutes)

### Step 1: Install Python 3.10+
Download from [python.org](https://www.python.org/downloads/)

### Step 2: Install dependencies
```bash
cd lead_gen_system
pip install -r requirements.txt
```

### Step 3: Configure your ICP
Open `config.py` and edit:
- `COMPANY_NAME` — Your company name
- `TARGET_INDUSTRIES` — Industries you sell to
- `TARGET_JOB_TITLES` — Decision makers you want
- `TARGET_LOCATIONS` — Cities to focus on
- `SEARCH_KEYWORDS` — Intent signals to look for

### Step 4: Add existing customers (optional but recommended)
Open `existing_customers.csv` and add your 5-10 current customers.
This trains the pattern matcher to find similar leads.

### Step 5: Run the system
```bash
python main.py --run-now
```

### Step 6: Launch dashboard
```bash
python main.py --dashboard
```

### Step 7: Open browser
Go to **http://localhost:8501** and watch leads appear live!

---

## 📖 Usage Commands

| Command | What it does |
|---|---|
| `python main.py --run-now` | Run full pipeline immediately |
| `python main.py --dashboard` | Launch live Streamlit dashboard |
| `python main.py --report` | Generate daily report |
| `python main.py --export` | Export leads to CSV |
| `python main.py --schedule` | Auto-run daily at 9:00 AM |

---

## 📁 Project Structure

```
lead_gen_system/
├── config.py                  # Your Ideal Customer Profile
├── main.py                    # Pipeline orchestrator + CLI
├── dashboard.py               # Streamlit dashboard (5 pages)
├── existing_customers.csv     # Your current customers (for pattern learning)
├── requirements.txt           # Python dependencies
├── modules/
│   ├── scraper.py             # Google search + web scraping
│   ├── scorer.py              # Lead scoring engine (0-100)
│   ├── enricher.py            # Company website + email enrichment
│   ├── pattern_matcher.py     # Pattern learning + ML
│   ├── reporter.py            # Reports + CSV exports
│   └── database.py            # SQLite database manager
└── data/
    ├── leads.db               # SQLite database (auto-created)
    ├── leads.csv              # All leads export
    ├── hot_leads.csv          # HOT leads export
    ├── report.txt             # Daily report
    └── logs/
        └── system.log         # System log file
```

---

## 🎯 Demo Script for Management

> "Sir, watch this. I am telling the system our ideal customer profile —
> which industries, which job titles, which cities.
>
> Now I click **Run**. See — it is searching Google automatically,
> finding companies, extracting contacts, scoring them against our profile,
> and showing HOT leads in real time on this dashboard.
>
> These are **brand new people who never saw our ad**.
>
> The system also learns what a good lead looks like from our existing
> customers. As we collect more data, it gets smarter.
>
> This can run **every single day automatically at 9 AM**.
> This is how we increase customers using technology."

---

## ⚠️ Important Notes

- **Rate Limiting**: The scraper adds random delays (2-5 sec) between requests to avoid being blocked by Google. If blocked, it waits 30 seconds and retries.
- **LinkedIn**: Only scrapes publicly visible data. Does NOT login or use LinkedIn API.
- **Guessed Emails**: Email pattern guesses are NOT verified — use them as starting points for outreach.
- **Data Privacy**: This tool scrapes publicly available information. Ensure compliance with local data protection laws before using for outreach.
- **First Run**: The first run may take 5-15 minutes depending on the number of queries. Subsequent runs are faster due to duplicate detection.

---

## 📊 Scoring Breakdown

| Component | Max Points | How it's scored |
|---|---|---|
| Industry Match | 30 | Exact = 30, Fuzzy = 15, None = 0 |
| Job Title Match | 25 | Exact = 25, Senior keyword = 15, None = 0 |
| Location Match | 20 | Exact city = 20, Fuzzy = 10, None = 0 |
| Contact Available | 15 | Email = 8, Phone = 4, LinkedIn = 3 |
| Keyword Signals | 10 | High-intent = 10, Industry = 5, None = 0 |

**Classification:** 75-100 = HOT 🔴 | 50-74 = WARM 🟡 | 0-49 = COLD 🔵

---

Built with ❤️ — Zero API Keys, 100% Free
