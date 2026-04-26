import streamlit as st
from backend.modules.scraper import LeadScraper
from backend.modules.scorer import LeadScorer
from backend.modules.messenger import MessageGenerator
from backend.models import SessionLocal, LeadModel, init_db
import os
from dotenv import load_dotenv

load_dotenv()
init_db()

st.title("Glambot Sales AI")

if st.button("Run Lead Generation"):
    scraper = LeadScraper()
    scorer = LeadScorer()
    messenger = MessageGenerator()

    leads = scraper.get_leads()
    leads = scorer.score(leads)

    db = SessionLocal()
    results = []

    for lead in leads:
        # Check if lead already exists to avoid duplicates
        existing = db.query(LeadModel).filter(LeadModel.url == lead.get('url')).first()

        if not existing:
            msg = messenger.generate(lead)
            db_lead = LeadModel(
                name=lead['name'],
                url=lead.get('url'),
                description=lead.get('description'),
                location=lead.get('location'),
                score=lead['score'],
                message=msg
            )
            db.add(db_lead)
            results.append({"lead": lead, "message": msg})
        else:
            results.append({"lead": lead, "message": existing.message})

    db.commit()
    db.close()
    st.success("Leads generated and stored!")
    st.json(results)

st.header("Historical Leads")
db = SessionLocal()
leads = db.query(LeadModel).order_by(LeadModel.score.desc()).all()
db.close()

if leads:
    st.table([{"Name": l.name, "URL": l.url, "Location": l.location, "Score": l.score, "Description": l.description, "Message": l.message} for l in leads])
else:
    st.write("No leads yet. Click 'Run Lead Generation' to start.")