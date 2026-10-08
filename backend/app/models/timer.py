"""Timer database model."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimerModel(Base):
    """Timer state persistence model."""
    
    __tablename__ = "timers"
    
    game_id = Column(String, primary_key=True, index=True)
    phase = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    remaining_seconds = Column(Integer, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_paused = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
