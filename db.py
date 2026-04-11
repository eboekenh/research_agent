import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy import JSON
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_agent.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Research(Base):
    __tablename__ = "researches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(Text, nullable=False)
    clarifications = Column(Text, default="")
    report = Column(Text, default="")
    report_path = Column(String(255), default="")
    sources = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(engine)


def save_research(topic: str, clarifications: str, report: str, report_path: str, sources: list[dict]) -> str:
    with SessionLocal() as session:
        research = Research(
            topic=topic,
            clarifications=clarifications,
            report=report,
            report_path=report_path,
            sources=sources,
        )
        session.add(research)
        session.commit()
        return str(research.id)


def get_all_researches() -> list[dict]:
    with SessionLocal() as session:
        rows = session.query(Research).order_by(Research.created_at.desc()).all()
        return [
            {
                "id": str(r.id),
                "topic": r.topic,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]


def get_research(research_id: str) -> dict | None:
    with SessionLocal() as session:
        r = session.get(Research, research_id)
        if not r:
            return None
        return {
            "id": str(r.id),
            "topic": r.topic,
            "clarifications": r.clarifications,
            "report": r.report,
            "report_path": r.report_path,
            "sources": r.sources,
            "created_at": r.created_at.isoformat(),
        }
