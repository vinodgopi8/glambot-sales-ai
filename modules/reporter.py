"""
reporter.py — Automated Report Generator
===========================================
Generates daily summary reports, hot lead alerts,
and CSV exports. Reports are printed to terminal
and saved as text files.
"""

import os
import sys
import csv
import logging
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from modules.database import DatabaseManager

logger = logging.getLogger("reporter")


class ReportGenerator:
    """Generates automated reports from lead data."""

    def __init__(self):
        """Initialize reporter with database connection."""
        self.db = DatabaseManager()

    def generate_daily_report(self, save_to_file=True):
        """
        Generate a comprehensive daily summary report.
        Prints to terminal and optionally saves to file.

        Args:
            save_to_file: If True, save report to report.txt.

        Returns:
            str: The complete report text.
        """
        today = date.today().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Gather data
        all_leads = self.db.get_all_leads()
        hot_leads = self.db.get_leads_by_category("HOT")
        warm_leads = self.db.get_leads_by_category("WARM")
        cold_leads = self.db.get_leads_by_category("COLD")

        # Today's leads
        today_leads = [
            l for l in all_leads
            if l.get("found_date", "").startswith(today)
        ]
        today_hot = [l for l in today_leads if l.get("category") == "HOT"]
        today_warm = [l for l in today_leads if l.get("category") == "WARM"]
        today_cold = [l for l in today_leads if l.get("category") == "COLD"]

        # Industry distribution
        industry_dist = self.db.get_industry_distribution()

        # Search history
        search_history = self.db.get_search_history()

        # Pattern match stats
        high_match = sum(1 for l in all_leads if l.get("pattern_match") == "High")
        match_pct = (high_match / len(all_leads) * 100) if all_leads else 0

        # Build report
        lines = []
        lines.append("")
        lines.append("═" * 55)
        lines.append("   LEAD GENERATION DAILY REPORT")
        lines.append(f"   Date: {now}")
        lines.append(f"   Company: {config.COMPANY_NAME}")
        lines.append("═" * 55)
        lines.append("")
        lines.append("── TODAY'S RESULTS ──────────────────────────")
        lines.append(f"   TOTAL LEADS FOUND TODAY: {len(today_leads)}")
        lines.append(f"   HOT LEADS  🔴: {len(today_hot)}")
        lines.append(f"   WARM LEADS 🟡: {len(today_warm)}")
        lines.append(f"   COLD LEADS 🔵: {len(today_cold)}")
        lines.append("")
        lines.append("── ALL TIME TOTALS ─────────────────────────")
        lines.append(f"   TOTAL LEADS:   {len(all_leads)}")
        lines.append(f"   HOT LEADS  🔴: {len(hot_leads)}")
        lines.append(f"   WARM LEADS 🟡: {len(warm_leads)}")
        lines.append(f"   COLD LEADS 🔵: {len(cold_leads)}")
        lines.append("")

        # Top 5 HOT leads
        lines.append("── TOP 5 HOT LEADS ─────────────────────────")
        if hot_leads:
            for i, lead in enumerate(hot_leads[:5], 1):
                name = lead.get("name", "Unknown")[:20]
                company = lead.get("company", "Unknown")[:22]
                title = lead.get("job_title", "")[:15]
                email = lead.get("email", "no email")[:25]
                score = lead.get("score", 0)
                lines.append(
                    f"   {i}. {name:20s} | {company:22s} | "
                    f"{title:15s} | {email:25s} | Score: {score}"
                )
        else:
            lines.append("   No HOT leads yet. Run scraper to find some!")
        lines.append("")

        # Best search queries
        lines.append("── BEST SEARCH QUERIES ─────────────────────")
        if search_history:
            # Group by query and sum results
            query_totals = {}
            for sh in search_history:
                q = sh.get("query", "")
                query_totals[q] = query_totals.get(q, 0) + sh.get("results_count", 0)

            sorted_queries = sorted(query_totals.items(), key=lambda x: x[1], reverse=True)
            for i, (query, count) in enumerate(sorted_queries[:5], 1):
                lines.append(f'   {i}. "{query[:50]}" → {count} results')
        else:
            lines.append("   No searches run yet.")
        lines.append("")

        # Industry distribution
        lines.append("── INDUSTRIES FOUND ────────────────────────")
        if industry_dist:
            for industry, count in sorted(industry_dist.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * min(count, 20)
                lines.append(f"   {industry:20s}: {count:3d} {bar}")
        else:
            lines.append("   No industry data yet.")
        lines.append("")

        # Pattern insights
        lines.append("── PATTERN INSIGHTS ────────────────────────")
        lines.append(f"   {match_pct:.1f}% of leads match your ideal customer profile")

        location_dist = self.db.get_location_distribution()
        if location_dist:
            top_loc = max(location_dist, key=location_dist.get)
            lines.append(f"   Most leads from: {top_loc}")

        title_dist = self.db.get_title_distribution()
        if title_dist:
            top_title = max(title_dist, key=title_dist.get)
            lines.append(f"   Most common title: {top_title}")

        lines.append("")
        lines.append("── PIPELINE STATUS ─────────────────────────")
        status_dist = self.db.get_status_distribution()
        for status in ["new", "contacted", "replied", "meeting", "closed"]:
            count = status_dist.get(status, 0)
            lines.append(f"   {status:12s}: {count}")

        lines.append("")
        lines.append("═" * 55)
        lines.append(f"   Generated by {config.COMPANY_NAME} Lead Gen System")
        lines.append("═" * 55)
        lines.append("")

        report_text = "\n".join(lines)

        # Print to terminal
        print(report_text)

        # Save to file
        if save_to_file:
            try:
                with open(config.REPORT_PATH, "w", encoding="utf-8") as f:
                    f.write(report_text)
                print(f"📄 Report saved to: {config.REPORT_PATH}")
                logger.info("Daily report saved to %s", config.REPORT_PATH)
            except Exception as e:
                logger.error("Failed to save report: %s", str(e))

        return report_text

    def generate_hot_leads_alert(self):
        """
        Generate a quick alert showing only HOT leads.
        Useful for quick management updates.

        Returns:
            str: Hot leads alert text.
        """
        hot_leads = self.db.get_leads_by_category("HOT")

        lines = []
        lines.append("")
        lines.append("🔴" * 20)
        lines.append("   HOT LEADS ALERT!")
        lines.append(f"   {len(hot_leads)} HOT leads found")
        lines.append("🔴" * 20)
        lines.append("")

        if hot_leads:
            for i, lead in enumerate(hot_leads[:10], 1):
                lines.append(f"   {i}. {lead.get('name', 'Unknown')}")
                lines.append(f"      Company:  {lead.get('company', 'Unknown')}")
                lines.append(f"      Title:    {lead.get('job_title', 'N/A')}")
                lines.append(f"      Email:    {lead.get('email', 'not found')}")
                lines.append(f"      Phone:    {lead.get('phone', 'not found')}")
                lines.append(f"      Location: {lead.get('location', 'N/A')}")
                lines.append(f"      Score:    {lead.get('score', 0)}/100")
                lines.append("")
        else:
            lines.append("   No HOT leads yet. Keep running the scraper!")
            lines.append("")

        alert_text = "\n".join(lines)
        print(alert_text)
        return alert_text

    def export_hot_leads_csv(self, filepath=None):
        """
        Export only HOT leads to a separate CSV file.
        Useful for sales team handoff.

        Args:
            filepath: Output path. Uses config default if None.

        Returns:
            str: Path to the exported CSV.
        """
        filepath = filepath or config.HOT_LEADS_CSV

        try:
            hot_leads = self.db.get_leads_by_category("HOT")

            if not hot_leads:
                print("⚠️  No HOT leads to export.")
                return None

            # Select key fields for sales team
            export_fields = [
                "id", "name", "company", "job_title", "industry",
                "location", "email", "phone", "linkedin_url",
                "website", "score", "pattern_match", "found_date",
            ]

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=export_fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(hot_leads)

            print(f"✅ Exported {len(hot_leads)} HOT leads to: {filepath}")
            logger.info("Exported %d HOT leads to %s", len(hot_leads), filepath)
            return filepath

        except Exception as e:
            logger.error("HOT leads export failed: %s", str(e))
            print(f"❌ Export failed: {e}")
            return None

    def get_report_data(self):
        """
        Get all report data as a dictionary (for dashboard use).

        Returns:
            dict: Complete report data.
        """
        all_leads = self.db.get_all_leads()
        today = date.today().strftime("%Y-%m-%d")

        today_leads = [
            l for l in all_leads
            if l.get("found_date", "").startswith(today)
        ]

        return {
            "total_leads": len(all_leads),
            "hot_leads": len(self.db.get_leads_by_category("HOT")),
            "warm_leads": len(self.db.get_leads_by_category("WARM")),
            "cold_leads": len(self.db.get_leads_by_category("COLD")),
            "today_leads": len(today_leads),
            "industry_distribution": self.db.get_industry_distribution(),
            "location_distribution": self.db.get_location_distribution(),
            "title_distribution": self.db.get_title_distribution(),
            "status_distribution": self.db.get_status_distribution(),
            "daily_stats": self.db.get_daily_stats(),
            "search_history": self.db.get_search_history(),
            "pattern_match_pct": (
                sum(1 for l in all_leads if l.get("pattern_match") == "High")
                / len(all_leads) * 100
            ) if all_leads else 0,
        }


# ═══════════════════════════════════════════════
# Quick test when run directly
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    reporter = ReportGenerator()
    reporter.generate_daily_report()
    reporter.generate_hot_leads_alert()
    print("\nReporter module working correctly! ✅")
