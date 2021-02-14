import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = os.getenv("DB_CONN")
SQLALCHEMY_DATABASE_URL = "sqlite:///./xmeme.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# import databases
# database = databases.Database(SQLALCHEMY_DATABASE_URL)
# metadata = sqlalchemy.MetaData()

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ''' APP EVENT SETTING'''
# @app.on_event("startup")
# async def startup():
#     await database.connect()


# @app.on_event("shutdown")
# async def shutdown():
#     await database.disconnect()