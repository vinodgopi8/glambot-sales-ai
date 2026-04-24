from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from modules.scraper import LeadScraper
from modules.scorer import LeadScorer
from modules.messenger import MessageGenerator
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models import SessionLocal, LeadModel, init_db

# Initialize Database
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins=["*"] in FastAPI
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/run")
def run_system():
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
    return results

@app.get("/leads")
def get_historical_leads():
    db = SessionLocal()
    leads = db.query(LeadModel).order_by(LeadModel.score.desc()).all()
    db.close()
    # Format for frontend
    return [{"lead": {"name": l.name, "url": l.url, "location": l.location, "score": l.score, "description": l.description}, "message": l.message, "status": l.status} for l in leads]

# Mount the React build folder
frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

if os.path.exists(frontend_build_path):
    # Serve static assets
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_path, "static")), name="static")

    @app.get("/{catchall:path}")
    def serve_react_app(catchall: str):
        file_path = os.path.join(frontend_build_path, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_build_path, "index.html"))
