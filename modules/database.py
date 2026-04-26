"""
database.py — SQLite Database Manager
======================================
Handles all database operations for the lead generation system.
Uses SQLite (built-in, no setup needed).
Creates tables, inserts leads, handles duplicates, exports data.
"""

import sqlite3
import csv
import os
import logging
from datetime import datetime, date

# Import paths from config
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

logger = logging.getLogger("database")


class DatabaseManager:
    """Manages all SQLite database operations for lead storage and retrieval."""

    def __init__(self, db_path=None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Uses config default if None.
        """
        self.db_path = db_path or config.DB_PATH
        self.initialize_database()

    def _get_connection(self):
        """Create and return a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

    def initialize_database(self):
        """
        Create all required tables if they don't exist.
        Tables: leads, search_history, daily_stats
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # ── leads table: stores every lead found ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    company TEXT,
                    job_title TEXT,
                    industry TEXT,
                    location TEXT,
                    email TEXT,
                    website TEXT,
                    linkedin_url TEXT,
                    phone TEXT,
                    source_url TEXT,
                    search_query TEXT,
                    score INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'COLD',
                    status TEXT DEFAULT 'new',
                    guessed_emails TEXT,
                    social_urls TEXT,
                    company_info TEXT,
                    pattern_match TEXT DEFAULT 'Low',
                    found_date TEXT,
                    last_updated TEXT
                )
            """)

            # ── search_history table: tracks what queries were run ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    results_count INTEGER DEFAULT 0,
                    timestamp TEXT
                )
            """)

            # ── daily_stats table: aggregated daily metrics ──
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    leads_found INTEGER DEFAULT 0,
                    hot_leads INTEGER DEFAULT 0,
                    warm_leads INTEGER DEFAULT 0,
                    cold_leads INTEGER DEFAULT 0
                )
            """)

            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully at %s", self.db_path)
            print(f"✅ Database ready: {self.db_path}")

        except Exception as e:
            logger.error("❌ Database initialization failed: %s", str(e))
            print(f"❌ Database initialization failed: {e}")
            raise

    def insert_lead(self, lead_dict):
        """
        Insert a new lead into the database.
        Checks for duplicates before inserting.

        Args:
            lead_dict: Dictionary with lead fields (name, company, etc.)

        Returns:
            int: The ID of the inserted lead, or None if duplicate/error.
        """
        try:
            # Check for duplicate first
            if self.check_duplicate(
                lead_dict.get("company", ""),
                lead_dict.get("name", "")
            ):
                logger.info("⏩ Duplicate skipped: %s at %s",
                            lead_dict.get("name"), lead_dict.get("company"))
                return None

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leads (
                    name, company, job_title, industry, location,
                    email, website, linkedin_url, phone,
                    source_url, search_query, score, category,
                    status, found_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_dict.get("name", ""),
                lead_dict.get("company", ""),
                lead_dict.get("job_title", ""),
                lead_dict.get("industry", ""),
                lead_dict.get("location", ""),
                lead_dict.get("email", ""),
                lead_dict.get("website", ""),
                lead_dict.get("linkedin_url", ""),
                lead_dict.get("phone", ""),
                lead_dict.get("source_url", ""),
                lead_dict.get("search_query", ""),
                lead_dict.get("score", 0),
                lead_dict.get("category", "COLD"),
                "new",
                now,
                now,
            ))

            lead_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info("✅ Lead saved [ID:%d]: %s at %s",
                        lead_id, lead_dict.get("name"), lead_dict.get("company"))
            print(f"  💾 Saved: {lead_dict.get('name', 'Unknown')} | "
                  f"{lead_dict.get('company', 'Unknown')} | "
                  f"{lead_dict.get('email', 'no email')}")
            return lead_id

        except Exception as e:
            logger.error("❌ Insert failed: %s", str(e))
            print(f"  ❌ Save failed: {e}")
            return None

    def update_lead(self, lead_id, updates):
        """
        Update specific fields of a lead.

        Args:
            lead_id: ID of the lead to update.
            updates: Dictionary of field:value pairs to update.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build dynamic SET clause
            set_parts = []
            values = []
            for key, value in updates.items():
                set_parts.append(f"{key} = ?")
                values.append(value)

            # Always update last_updated timestamp
            set_parts.append("last_updated = ?")
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            values.append(lead_id)

            query = f"UPDATE leads SET {', '.join(set_parts)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            conn.close()

            logger.info("✅ Lead [ID:%d] updated: %s", lead_id, list(updates.keys()))

        except Exception as e:
            logger.error("❌ Update failed for lead %d: %s", lead_id, str(e))

    def update_lead_status(self, lead_id, status):
        """
        Update the status of a lead (new/contacted/replied/meeting/closed).

        Args:
            lead_id: ID of the lead.
            status: New status string.
        """
        valid_statuses = ["new", "contacted", "replied", "meeting", "closed"]
        if status not in valid_statuses:
            print(f"❌ Invalid status: {status}. Must be one of {valid_statuses}")
            return

        self.update_lead(lead_id, {"status": status})
        print(f"✅ Lead [ID:{lead_id}] status updated to: {status}")

    def get_leads_by_category(self, category):
        """
        Get all leads of a specific category (HOT/WARM/COLD).

        Args:
            category: 'HOT', 'WARM', or 'COLD'

        Returns:
            list: List of lead dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM leads WHERE category = ? ORDER BY score DESC",
                (category.upper(),)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("❌ Fetch by category failed: %s", str(e))
            return []

    def get_all_leads(self):
        """
        Get all leads from database ordered by score descending.

        Returns:
            list: List of all lead dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads ORDER BY score DESC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("❌ Fetch all leads failed: %s", str(e))
            return []

    def get_new_unscored_leads(self):
        """
        Get leads that haven't been scored yet (score = 0).

        Returns:
            list: List of unscored lead dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM leads WHERE score = 0 ORDER BY found_date DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("❌ Fetch unscored leads failed: %s", str(e))
            return []

    def check_duplicate(self, company, name):
        """
        Check if a lead with the same company AND name already exists.

        Args:
            company: Company name to check.
            name: Person name to check.

        Returns:
            bool: True if duplicate exists, False otherwise.
        """
        if not company and not name:
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check exact match on company+name (case-insensitive)
            cursor.execute("""
                SELECT COUNT(*) FROM leads
                WHERE LOWER(company) = LOWER(?) AND LOWER(name) = LOWER(?)
            """, (company.strip(), name.strip()))

            count = cursor.fetchone()[0]
            conn.close()
            return count > 0

        except Exception as e:
            logger.error("❌ Duplicate check failed: %s", str(e))
            return False

    def get_lead_by_id(self, lead_id):
        """
        Get a single lead by its ID.

        Args:
            lead_id: The lead's database ID.

        Returns:
            dict: Lead dictionary or None.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

        except Exception as e:
            logger.error("❌ Fetch lead by ID failed: %s", str(e))
            return None

    def get_total_count(self):
        """Get total number of leads in database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def get_count_by_category(self, category):
        """Get count of leads in a specific category."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM leads WHERE category = ?",
                (category.upper(),)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def log_search(self, query, results_count):
        """
        Log a search query and how many results it produced.

        Args:
            query: The search query string.
            results_count: Number of leads found from this query.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history (query, results_count, timestamp)
                VALUES (?, ?, ?)
            """, (query, results_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error("❌ Search log failed: %s", str(e))

    def get_search_history(self):
        """Get all search history records."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM search_history ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def update_daily_stats(self):
        """
        Calculate and update today's statistics.
        Called after each scraping run.
        """
        try:
            today = date.today().strftime("%Y-%m-%d")
            conn = self._get_connection()
            cursor = conn.cursor()

            # Count leads found today
            cursor.execute(
                "SELECT COUNT(*) FROM leads WHERE DATE(found_date) = ?", (today,)
            )
            leads_found = cursor.fetchone()[0]

            # Count by category for today
            cursor.execute(
                "SELECT COUNT(*) FROM leads WHERE DATE(found_date) = ? AND category = 'HOT'",
                (today,)
            )
            hot = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM leads WHERE DATE(found_date) = ? AND category = 'WARM'",
                (today,)
            )
            warm = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM leads WHERE DATE(found_date) = ? AND category = 'COLD'",
                (today,)
            )
            cold = cursor.fetchone()[0]

            # Upsert daily stats
            cursor.execute("""
                INSERT INTO daily_stats (date, leads_found, hot_leads, warm_leads, cold_leads)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    leads_found = excluded.leads_found,
                    hot_leads = excluded.hot_leads,
                    warm_leads = excluded.warm_leads,
                    cold_leads = excluded.cold_leads
            """, (today, leads_found, hot, warm, cold))

            conn.commit()
            conn.close()
            logger.info("📊 Daily stats updated: %d leads, %d hot, %d warm, %d cold",
                        leads_found, hot, warm, cold)

        except Exception as e:
            logger.error("❌ Daily stats update failed: %s", str(e))

    def get_daily_stats(self):
        """
        Get daily stats for all recorded days.

        Returns:
            list: List of daily stats dictionaries.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_stats ORDER BY date DESC")
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error("❌ Get daily stats failed: %s", str(e))
            return []

    def get_leads_by_status(self, status):
        """Get all leads with a specific status."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM leads WHERE status = ? ORDER BY score DESC",
                (status,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def get_industry_distribution(self):
        """Get count of leads per industry."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT industry, COUNT(*) as count
                FROM leads
                WHERE industry != ''
                GROUP BY industry
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return {row["industry"]: row["count"] for row in rows}
        except Exception:
            return {}

    def get_location_distribution(self):
        """Get count of leads per location."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT location, COUNT(*) as count
                FROM leads
                WHERE location != ''
                GROUP BY location
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return {row["location"]: row["count"] for row in rows}
        except Exception:
            return {}

    def get_title_distribution(self):
        """Get count of leads per job title."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT job_title, COUNT(*) as count
                FROM leads
                WHERE job_title != ''
                GROUP BY job_title
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            return {row["job_title"]: row["count"] for row in rows}
        except Exception:
            return {}

    def get_status_distribution(self):
        """Get count of leads per status (for funnel chart)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM leads
                GROUP BY status
                ORDER BY
                    CASE status
                        WHEN 'new' THEN 1
                        WHEN 'contacted' THEN 2
                        WHEN 'replied' THEN 3
                        WHEN 'meeting' THEN 4
                        WHEN 'closed' THEN 5
                    END
            """)
            rows = cursor.fetchall()
            conn.close()
            return {row["status"]: row["count"] for row in rows}
        except Exception:
            return {}

    def export_to_csv(self, filepath=None, category=None):
        """
        Export leads to CSV file.

        Args:
            filepath: Output CSV path. Uses config default if None.
            category: Optional — only export leads of this category.
        """
        filepath = filepath or config.CSV_PATH

        try:
            leads = (
                self.get_leads_by_category(category)
                if category
                else self.get_all_leads()
            )

            if not leads:
                print("⚠️  No leads to export.")
                return

            # Write CSV with all fields
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                writer.writeheader()
                writer.writerows(leads)

            print(f"✅ Exported {len(leads)} leads to: {filepath}")
            logger.info("✅ CSV exported: %d leads → %s", len(leads), filepath)

        except Exception as e:
            logger.error("❌ CSV export failed: %s", str(e))
            print(f"❌ Export failed: {e}")


# ═══════════════════════════════════════════════
# Quick test when run directly
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    db = DatabaseManager()
    print(f"Total leads in database: {db.get_total_count()}")
    print("Database module working correctly! ✅")
