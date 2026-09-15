from app.core.database import Base, engine

from app.models import (
    User,
    Farmer,
    Farm,
    Field,
    SoilProfile,
)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("FarmIQ database tables created successfully.")


if __name__ == "__main__":
    init_db()
