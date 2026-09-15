from sqlalchemy.orm import Session

from app.models import Farmer, User
from app.schemas.farmer import FarmerCreate


def create_farmer(db: Session, farmer_data: FarmerCreate):
    existing_user = (
        db.query(User)
        .filter(User.email == farmer_data.email)
        .first()
    )

    if existing_user:
        raise ValueError("A user with this email already exists.")

    user = User(
        full_name=farmer_data.full_name,
        email=farmer_data.email,
        hashed_password="NOT_SET",
        role="FARMER",
        is_active=True,
    )

    db.add(user)
    db.flush()

    farmer = Farmer(
        user_id=user.id,
        phone=farmer_data.phone,
    )

    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    return farmer


def get_farmers(db: Session):
    return db.query(Farmer).all()


def get_farmer(db: Session, farmer_id: int):
    return (
        db.query(Farmer)
        .filter(Farmer.id == farmer_id)
        .first()
    )
