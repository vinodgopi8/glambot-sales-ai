"""
main.py — Lead Generation System Orchestrator
================================================
Runs the complete pipeline: scrape → score → enrich → match → report.

Usage:
    python main.py --run-now       Run full pipeline immediately
    python main.py --dashboard     Launch Streamlit dashboard
    python main.py --report        Generate report only
    python main.py --export        Export HOT leads to CSV
    python main.py --schedule      Run on daily schedule (9:00 AM)
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from datetime import datetime

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from modules.database import DatabaseManager
from modules.scraper import LeadScraper
from modules.scorer import LeadScorer
from modules.enricher import LeadEnricher
from modules.pattern_matcher import PatternMatcher
from modules.reporter import ReportGenerator

logger = logging.getLogger("main")


def print_banner():
    """Print the system startup banner."""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║                                                        ║")
    print("║   🚀 LEAD GENERATION SYSTEM                           ║")
    print(f"║   📌 {config.COMPANY_NAME:<50s}║")
    print("║   🤖 AI-Powered • Zero API Keys • 100% Free           ║")
    print("║                                                        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()


def run_full_pipeline():
    """
    Run the complete lead generation pipeline.

    Steps:
        1. Initialize database
        2. Load config and ICP
        3. Build search queries from config
        4. Run scraper for each query
        5. Score all new leads
        6. Enrich HOT and WARM leads
        7. Run pattern matching
        8. Generate daily report
        9. Export HOT leads to CSV
        10. Print summary
    """
    start_time = datetime.now()

    print_banner()
    print("🚀 Starting Full Lead Generation Pipeline...")
    print(f"⏰ Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Step 1: Initialize Database ──
    print("━" * 55)
    print("STEP 1/10: Initializing Database...")
    print("━" * 55)
    db = DatabaseManager()
    print(f"   📊 Current leads in database: {db.get_total_count()}")
    print()

    # ── Step 2: Load Config ──
    print("━" * 55)
    print("STEP 2/10: Loading Ideal Customer Profile...")
    print("━" * 55)
    print(f"   🏢 Company: {config.COMPANY_NAME}")
    print(f"   🏭 Industries: {', '.join(config.TARGET_INDUSTRIES[:5])}...")
    print(f"   👤 Titles: {', '.join(config.TARGET_JOB_TITLES[:5])}...")
    print(f"   📍 Locations: {', '.join(config.TARGET_LOCATIONS[:5])}...")
    print(f"   🎯 HOT threshold: {config.HOT_LEAD_THRESHOLD}")
    print(f"   🎯 WARM threshold: {config.WARM_LEAD_THRESHOLD}")
    print()

    # ── Step 3: Build Search Queries ──
    print("━" * 55)
    print("STEP 3/10: Building Search Queries...")
    print("━" * 55)
    scraper = LeadScraper()
    queries = scraper.build_search_queries()
    print(f"   📋 Generated {len(queries)} unique search queries")
    print()

    # ── Step 4: Run Scraper ──
    print("━" * 55)
    print("STEP 4/10: Running Web Scraper...")
    print("━" * 55)
    new_leads = scraper.run_scraper()
    print()

    # ── Step 5: Score All New Leads ──
    print("━" * 55)
    print("STEP 5/10: Scoring Leads...")
    print("━" * 55)
    scorer = LeadScorer()
    scored_count = scorer.score_all_new_leads()
    print()

    # ── Step 6: Enrich HOT and WARM Leads ──
    print("━" * 55)
    print("STEP 6/10: Enriching Top Leads...")
    print("━" * 55)
    enricher = LeadEnricher()
    enriched_count = enricher.enrich_leads_by_category(["HOT", "WARM"])
    print()

    # ── Step 7: Pattern Matching ──
    print("━" * 55)
    print("STEP 7/10: Running Pattern Matching...")
    print("━" * 55)
    matcher = PatternMatcher()
    match_results = matcher.match_all_leads()
    print()

    # ── Step 8: Generate Daily Report ──
    print("━" * 55)
    print("STEP 8/10: Generating Daily Report...")
    print("━" * 55)
    reporter = ReportGenerator()
    reporter.generate_daily_report()
    print()

    # ── Step 9: Export HOT Leads ──
    print("━" * 55)
    print("STEP 9/10: Exporting HOT Leads...")
    print("━" * 55)
    reporter.export_hot_leads_csv()
    print()

    # ── Step 10: Update Stats & Summary ──
    print("━" * 55)
    print("STEP 10/10: Updating Statistics...")
    print("━" * 55)
    db.update_daily_stats()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║            ✅ PIPELINE COMPLETE!                       ║")
    print("╠════════════════════════════════════════════════════════╣")
    print(f"║  ⏱️  Duration:       {duration:.0f} seconds{' ' * (33 - len(f'{duration:.0f} seconds'))}║")
    print(f"║  🆕 New Leads:      {new_leads}{' ' * (33 - len(str(new_leads)))}║")
    print(f"║  📊 Total Scored:   {scored_count}{' ' * (33 - len(str(scored_count)))}║")
    print(f"║  🔍 Enriched:       {enriched_count}{' ' * (33 - len(str(enriched_count)))}║")
    print(f"║  🔴 HOT Leads:      {db.get_count_by_category('HOT')}{' ' * (33 - len(str(db.get_count_by_category('HOT'))))}║")
    print(f"║  🟡 WARM Leads:     {db.get_count_by_category('WARM')}{' ' * (33 - len(str(db.get_count_by_category('WARM'))))}║")
    print(f"║  🔵 COLD Leads:     {db.get_count_by_category('COLD')}{' ' * (33 - len(str(db.get_count_by_category('COLD'))))}║")
    print(f"║  📁 Total in DB:    {db.get_total_count()}{' ' * (33 - len(str(db.get_total_count())))}║")
    print("╠════════════════════════════════════════════════════════╣")
    print("║  Next: python main.py --dashboard                     ║")
    print("║  Then open: http://localhost:8501                      ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()

    logger.info("Pipeline complete: %d new leads in %.0f seconds", new_leads, duration)


def launch_dashboard():
    """Launch the Streamlit dashboard."""
    print_banner()
    print("🖥️  Launching Dashboard...")
    print(f"   Open in browser: http://localhost:{config.STREAMLIT_PORT}")
    print("   Press Ctrl+C to stop\n")

    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", dashboard_path,
            "--server.port", str(config.STREAMLIT_PORT),
            "--server.headless", "true",
            "--theme.base", "dark",
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped.")
    except Exception as e:
        print(f"❌ Dashboard launch failed: {e}")
        print("   Make sure streamlit is installed: pip install streamlit")


def generate_report_only():
    """Generate and display the daily report without scraping."""
    print_banner()
    reporter = ReportGenerator()
    reporter.generate_daily_report()
    reporter.generate_hot_leads_alert()


def export_only():
    """Export leads to CSV without scraping."""
    print_banner()
    reporter = ReportGenerator()
    db = DatabaseManager()

    # Export all leads
    db.export_to_csv()

    # Export HOT leads separately
    reporter.export_hot_leads_csv()


def run_on_schedule():
    """
    Run the pipeline on a daily schedule using the schedule library.
    Runs at the time configured in config.DAILY_RUN_TIME.
    """
    import schedule

    print_banner()
    print(f"📅 Scheduled to run daily at {config.DAILY_RUN_TIME}")
    print("   Press Ctrl+C to stop\n")

    # Schedule the pipeline
    schedule.every().day.at(config.DAILY_RUN_TIME).do(run_full_pipeline)

    logger.info("Scheduler started. Daily run at %s", config.DAILY_RUN_TIME)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped.")


def main():
    """Parse command-line arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="🚀 Lead Generation System — Find customers automatically!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run-now       Run full pipeline now
  python main.py --dashboard     Open live dashboard
  python main.py --report        View today's report
  python main.py --export        Export leads to CSV
  python main.py --schedule      Auto-run daily at 9 AM
        """
    )

    parser.add_argument(
        "--run-now", action="store_true",
        help="Run the full lead generation pipeline immediately"
    )
    parser.add_argument(
        "--dashboard", action="store_true",
        help="Launch the Streamlit dashboard"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Generate and display the daily report"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export all leads and HOT leads to CSV"
    )
    parser.add_argument(
        "--schedule", action="store_true",
        help=f"Run pipeline daily at {config.DAILY_RUN_TIME}"
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n💡 Quick start: python main.py --run-now")
        return

    if args.run_now:
        run_full_pipeline()
    elif args.dashboard:
        launch_dashboard()
    elif args.report:
        generate_report_only()
    elif args.export:
        export_only()
    elif args.schedule:
        run_on_schedule()


if __name__ == "__main__":
    main()
