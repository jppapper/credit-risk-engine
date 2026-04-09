import os
from datetime import date
from sqlalchemy import create_engine, Column, String, Float, Date, BigInteger
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/credit_risk")
engine = create_engine(DATABASE_URL)
