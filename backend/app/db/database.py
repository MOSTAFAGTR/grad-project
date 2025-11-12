from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- THIS IS THE FIX ---
# The hostname in the URL must match the service name in docker-compose.yml
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@main_db/scale_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()