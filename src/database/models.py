import os
from datetime import date
from sqlalchemy import create_engine, Column, String, Float, Date, BigInteger
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class EODMark(Base):
    __tablename__ = "eod_marks"
    
    instrument_id = Column(String, primary_key=True)
    mark_date = Column(Date, primary_key=True)
    product = Column(String)
    spread_bps = Column(Float)
    rate = Column(Float)
    dirty_price = Column(Float)
    upfront = Column(Float)
    cs01 = Column(Float)
    dv01 = Column(Float)
    notional = Column(BigInteger)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgres/credit_risk")
engine = create_engine(DATABASE_URL)


def init_db():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized")