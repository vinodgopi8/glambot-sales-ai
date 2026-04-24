from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./sales_ai.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    url = Column(String, unique=True, index=True)
    description = Column(Text)
    location = Column(String)
    score = Column(Float)
    message = Column(Text)
    status = Column(String, default="generated")

def init_db():
    Base.metadata.create_all(bind=engine)
