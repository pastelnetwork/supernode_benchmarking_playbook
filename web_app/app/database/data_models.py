from pydantic import BaseModel
from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()

class RawBenchmarkSubscores(Base):
    __tablename__ = 'raw_benchmark_subscores'
    datetime = Column(DateTime, primary_key=True)
    hostname = Column(String)
    IP_address = Column(String)
    cpu_speed_test__events_per_second = Column(Float)
    fileio_test__reads_per_second = Column(Float)
    memory_speed_test__MiB_transferred = Column(Float)
    mutex_test__avg_latency = Column(Float)
    threads_test__avg_latency = Column(Float)

class OverallNormalizedScore(Base):
    __tablename__ = 'overall_normalized_score'
    datetime = Column(DateTime, primary_key=True)
    hostname = Column(String)
    IP_address = Column(String)
    overall_score = Column(Float)

# Pydantic Response Models
class HistoricalRawBenchmarkSubscoresResponse(BaseModel):
    id: Optional[int]
    datetime: datetime
    hostname: str
    IP_address: str
    cpu_speed_test__events_per_second: float
    fileio_test__reads_per_second: float
    memory_speed_test__MiB_transferred: float
    mutex_test__avg_latency: float
    threads_test__avg_latency: float
    class Config:
        from_attributes = True

class HistoricalOverallNormalizedScoresResponse(BaseModel):
    id: Optional[int]
    datetime: datetime
    hostname: str
    IP_address: str
    overall_score: float
    class Config:
        from_attributes = True
