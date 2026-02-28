# backend/app/db/session.py

# ------------------------------------------------------------

# SQLAlchemy engine + SessionLocal for PostgreSQL

# Reads DATABASE_URL from environment (.env recommended).

# Example: postgresql://postgres:YOURPASSWORD@localhost:5432/stock_trading

# ------------------------------------------------------------

 

import os

from sqlalchemy import create_engine, text

from sqlalchemy.orm import sessionmaker, declarative_base

from dotenv import load_dotenv

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))



 

# Load .env if present

load_dotenv(ENV_PATH)

 

# You can keep using this default during local dev.

DATABASE_URL = os.getenv(

    "DATABASE_URL",

    "postgresql://postgres:YOURPASSWORD@localhost:5432/stock_trading"

)

 

# Create engine

engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    future=True,

)

 

# Session factory

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine,

    future=True,

)

 

# Base for ORM models

Base = declarative_base()

 

def set_search_path_to_trading(db):

    """

    Ensure queries run with `trading` schema first,

    consistent with your schema_v0_8.sql.

    Call this once per request/operation.

    """

    db.execute(text("SET search_path TO trading, public;"))

