from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bd_app.config.settings import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
