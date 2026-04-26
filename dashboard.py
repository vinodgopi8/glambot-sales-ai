"""
dashboard.py — Professional Streamlit Dashboard
==================================================
Live dashboard for monitoring lead generation results.
5 pages: Overview, Hot Leads, All Leads, Insights, System Control.

Launch: streamlit run dashboard.py
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from modules.database import DatabaseManager
from modules.reporter import ReportGenerator

# ── Page Config ──
st.set_page_config(
    page_title=f"{config.COMPANY_NAME} — Lead Gen Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for dark premium look ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 24px; text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .metric-card h2 { margin: 0; font-size: 2.4rem; font-weight: 700; }
    .metric-card p { margin: 4px 0 0; opacity: 0.7; font-size: 0.9rem; }
    .hot { color: #ff4757; } .warm { color: #ffa502; }
    .cold { color: #3742fa; } .green { color: #2ed573; }
    .blue { color: #1e90ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05); border-radius: 8px;
        padding: 8px 20px; font-weight: 500;
    }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Initialize DB & Reporter ──
db = DatabaseManager()
reporter = ReportGenerator()


def render_metric_card(label, value, css_class="blue"):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <h2 class="{css_class}">{value}</h2>
        <p>{label}</p>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ──
with st.sidebar:
    st.markdown(f"## 🚀 {config.COMPANY_NAME}")
    st.caption("AI-Powered Lead Generation")
    st.divider()
    page = st.radio("Navigation", [
        "📊 Live Overview",
        "🔴 Hot Leads",
        "📋 All Leads",
        "💡 Pattern Insights",
        "⚙️ System Control",
    ], label_visibility="collapsed")
    st.divider()
    total = db.get_total_count()
    st.metric("Total Leads", total)
    st.metric("HOT", db.get_count_by_category("HOT"))
    st.metric("WARM", db.get_count_by_category("WARM"))
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Refresh Now"):
        st.rerun()


# ════════════════════════════════════════
# PAGE 1: LIVE OVERVIEW
# ════════════════════════════════════════
if page == "📊 Live Overview":
    st.title("📊 Live Overview")

    # Metric cards row
    c1, c2, c3, c4 = st.columns(4)
    data = reporter.get_report_data()
    with c1:
        render_metric_card("Total Leads Found", data["total_leads"], "blue")
    with c2:
        render_metric_card("HOT Leads 🔴", data["hot_leads"], "hot")
    with c3:
        render_metric_card("WARM Leads 🟡", data["warm_leads"], "warm")
    with c4:
        render_metric_card(f"Pattern Match %", f"{data['pattern_match_pct']:.0f}%", "green")

    st.divider()
    col_left, col_right = st.columns(2)

    # Pipeline Funnel
    with col_left:
        st.subheader("Pipeline Funnel")
        status_dist = data["status_distribution"]
        stages = ["new", "contacted", "replied", "meeting", "closed"]
        stage_labels = ["🆕 Found", "📧 Contacted", "↩️ Replied", "🤝 Meeting", "✅ Closed"]
        values = [status_dist.get(s, 0) for s in stages]
        if any(values):
            fig = go.Figure(go.Funnel(
                y=stage_labels, x=values,
                textinfo="value+percent initial",
                marker=dict(color=["#1e90ff", "#ffa502", "#2ed573", "#ff6348", "#7bed9f"]),
            ))
            fig.update_layout(
                template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline data yet. Run the scraper first!")

    # Industry Distribution Pie
    with col_right:
        st.subheader("Industry Distribution")
        ind_dist = data["industry_distribution"]
        if ind_dist:
            fig = px.pie(
                names=list(ind_dist.keys()), values=list(ind_dist.values()),
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig.update_layout(
                template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No industry data yet.")

    # Daily trend line chart
    st.subheader("Leads Found Per Day")
    daily = data["daily_stats"]
    if daily:
        df_daily = pd.DataFrame(daily)
        fig = px.area(
            df_daily, x="date", y="leads_found",
            color_discrete_sequence=["#1e90ff"],
        )
        fig.update_layout(
            template="plotly_dark", height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="", yaxis_title="Leads",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run the scraper to start seeing daily trends.")


# ════════════════════════════════════════
# PAGE 2: HOT LEADS TABLE
# ════════════════════════════════════════
elif page == "🔴 Hot Leads":
    st.title("🔴 Hot Leads")
    hot = db.get_leads_by_category("HOT")
    if hot:
        df = pd.DataFrame(hot)
        display_cols = [
            "id", "name", "company", "job_title", "industry",
            "location", "email", "phone", "score", "status", "pattern_match",
        ]
        display_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[display_cols].style.background_gradient(subset=["score"], cmap="RdYlGn"),
            use_container_width=True, height=500,
        )

        # Score breakdown expander
        st.subheader("Score Breakdown")
        selected_id = st.selectbox("Select Lead ID", df["id"].tolist())
        if selected_id:
            from modules.scorer import LeadScorer
            scorer = LeadScorer()
            lead = db.get_lead_by_id(selected_id)
            if lead:
                result = scorer.score_lead(lead)
                bc1, bc2 = st.columns(2)
                with bc1:
                    for comp, score in result["breakdown"].items():
                        st.metric(comp.replace("_", " ").title(), f"{score}/{config.SCORING_WEIGHTS.get(comp, 0)}")
                with bc2:
                    for comp, expl in result["explanations"].items():
                        st.caption(f"**{comp.replace('_', ' ').title()}**: {expl}")

        # Status updater
        st.subheader("Update Lead Status")
        uc1, uc2, uc3 = st.columns(3)
        with uc1:
            update_id = st.number_input("Lead ID", min_value=1, step=1)
        with uc2:
            new_status = st.selectbox("New Status", ["new", "contacted", "replied", "meeting", "closed"])
        with uc3:
            st.write("")
            st.write("")
            if st.button("Update Status"):
                db.update_lead_status(int(update_id), new_status)
                st.success(f"Lead {update_id} → {new_status}")
                st.rerun()
    else:
        st.info("No HOT leads found yet. Run the scraper to find some!")


# ════════════════════════════════════════
# PAGE 3: ALL LEADS
# ════════════════════════════════════════
elif page == "📋 All Leads":
    st.title("📋 All Leads")
    all_leads = db.get_all_leads()
    if all_leads:
        df = pd.DataFrame(all_leads)

        # Filters
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            cat_filter = st.multiselect("Category", ["HOT", "WARM", "COLD"], default=["HOT", "WARM", "COLD"])
        with fc2:
            industries = sorted(df["industry"].dropna().unique().tolist())
            ind_filter = st.multiselect("Industry", industries)
        with fc3:
            locations = sorted(df["location"].dropna().unique().tolist())
            loc_filter = st.multiselect("Location", locations)
        with fc4:
            min_score = st.slider("Min Score", 0, 100, 0)

        filtered = df[df["category"].isin(cat_filter)]
        if ind_filter:
            filtered = filtered[filtered["industry"].isin(ind_filter)]
        if loc_filter:
            filtered = filtered[filtered["location"].isin(loc_filter)]
        filtered = filtered[filtered["score"] >= min_score]

        st.caption(f"Showing {len(filtered)} of {len(df)} leads")

        display_cols = [
            "id", "name", "company", "job_title", "industry", "location",
            "email", "phone", "score", "category", "status", "found_date",
        ]
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[display_cols], use_container_width=True, height=500)

        # Export button
        if st.button("📥 Export Filtered to CSV"):
            csv_data = filtered[display_cols].to_csv(index=False)
            st.download_button("Download CSV", csv_data, "filtered_leads.csv", "text/csv")
    else:
        st.info("No leads in database. Run the scraper first!")


# ════════════════════════════════════════
# PAGE 4: PATTERN INSIGHTS
# ════════════════════════════════════════
elif page == "💡 Pattern Insights":
    st.title("💡 Pattern Insights")
    st.caption("What your ideal customer looks like based on collected data")

    data = reporter.get_report_data()

    ic1, ic2 = st.columns(2)

    # Top industries pie
    with ic1:
        st.subheader("Top Industries")
        ind = data["industry_distribution"]
        if ind:
            fig = px.pie(names=list(ind.keys()), values=list(ind.values()), hole=0.35,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(template="plotly_dark", height=350,
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet.")

    # Top job titles bar
    with ic2:
        st.subheader("Top Job Titles")
        titles = data["title_distribution"]
        if titles:
            fig = px.bar(x=list(titles.values()), y=list(titles.keys()), orientation="h",
                         color_discrete_sequence=["#1e90ff"])
            fig.update_layout(template="plotly_dark", height=350,
                              paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet.")

    # Locations bar
    st.subheader("Top Locations")
    locs = data["location_distribution"]
    if locs:
        fig = px.bar(x=list(locs.keys()), y=list(locs.values()),
                     color_discrete_sequence=["#2ed573"])
        fig.update_layout(template="plotly_dark", height=300,
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Pattern match breakdown
    st.subheader("Pattern Match Distribution")
    all_leads = db.get_all_leads()
    if all_leads:
        match_counts = {"High": 0, "Medium": 0, "Low": 0}
        for l in all_leads:
            m = l.get("pattern_match", "Low")
            if m in match_counts:
                match_counts[m] += 1
        fig = px.pie(names=list(match_counts.keys()), values=list(match_counts.values()),
                     color=list(match_counts.keys()),
                     color_discrete_map={"High": "#2ed573", "Medium": "#ffa502", "Low": "#ff4757"},
                     hole=0.4)
        fig.update_layout(template="plotly_dark", height=300, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # ML Results section
    if len(all_leads) >= 50:
        st.subheader("🤖 ML Model Results")
        try:
            from modules.pattern_matcher import PatternMatcher
            matcher = PatternMatcher()
            ml = matcher.train_logistic_regression()
            if ml:
                st.metric("Model Accuracy", f"{ml['accuracy'] * 100:.1f}%")
                fi = ml["feature_importance"]
                fig = px.bar(x=list(fi.values()), y=list(fi.keys()), orientation="h",
                             color_discrete_sequence=["#ff6348"])
                fig.update_layout(template="plotly_dark", height=300,
                                  paper_bgcolor="rgba(0,0,0,0)", title="Feature Importance")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"ML not available: {e}")
    else:
        st.info(f"📊 Need 50+ leads for ML insights (currently {len(all_leads)}). Keep scraping!")


# ════════════════════════════════════════
# PAGE 5: SYSTEM CONTROL
# ════════════════════════════════════════
elif page == "⚙️ System Control":
    st.title("⚙️ System Control")

    sc1, sc2 = st.columns(2)

    with sc1:
        st.subheader("Run Scraper")
        if st.button("🚀 RUN SCRAPER NOW", type="primary", use_container_width=True):
            with st.spinner("Scraping in progress... This takes a few minutes."):
                try:
                    from modules.scraper import LeadScraper
                    from modules.scorer import LeadScorer
                    scraper = LeadScraper()
                    new_count = scraper.run_scraper(max_leads=30)
                    scorer = LeadScorer()
                    scorer.score_all_new_leads()
                    db.update_daily_stats()
                    st.success(f"✅ Found {new_count} new leads! Refresh to see results.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Scraper error: {e}")

    with sc2:
        st.subheader("Quick Actions")
        if st.button("📊 Score All Unscored Leads"):
            from modules.scorer import LeadScorer
            scorer = LeadScorer()
            n = scorer.score_all_new_leads()
            st.success(f"Scored {n} leads")
        if st.button("🔍 Enrich HOT Leads"):
            from modules.enricher import LeadEnricher
            enricher = LeadEnricher()
            n = enricher.enrich_leads_by_category(["HOT"])
            st.success(f"Enriched {n} leads")
        if st.button("📥 Export All to CSV"):
            db.export_to_csv()
            st.success(f"Exported to {config.CSV_PATH}")

    st.divider()

    # System stats
    st.subheader("System Stats")
    ss1, ss2, ss3 = st.columns(3)
    with ss1:
        st.metric("Total Searches", len(db.get_search_history()))
    with ss2:
        st.metric("Total Leads", db.get_total_count())
    with ss3:
        st.metric("Database Size", f"{os.path.getsize(config.DB_PATH) / 1024:.1f} KB" if os.path.exists(config.DB_PATH) else "0 KB")

    # Search history table
    st.subheader("Search History")
    history = db.get_search_history()
    if history:
        df_h = pd.DataFrame(history)
        st.dataframe(df_h[["query", "results_count", "timestamp"]], use_container_width=True, height=300)
    else:
        st.info("No searches run yet.")

# ── Auto-refresh ──
time.sleep(0.1)
