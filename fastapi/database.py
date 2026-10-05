import os

from sqlmodel import Session, create_engine

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session
