from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.field import FieldCreate, FieldUpdate, FieldResponse
from app.services.field_service import (
    create_field,
    get_fields,
    get_field,
    update_field,
    delete_field,
)

router = APIRouter(
    prefix="/fields",
    tags=["Fields"],
)


@router.post(
    "",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_field_endpoint(
    field_data: FieldCreate,
    db: Session = Depends(get_db),
):
    return create_field(db, field_data)


@router.get(
    "",
    response_model=list[FieldResponse],
)
def get_fields_endpoint(
    db: Session = Depends(get_db),
):
    return get_fields(db)


@router.get(
    "/{field_id}",
    response_model=FieldResponse,
)
def get_field_endpoint(
    field_id: int,
    db: Session = Depends(get_db),
):
    return get_field(db, field_id)


@router.put(
    "/{field_id}",
    response_model=FieldResponse,
)
def update_field_endpoint(
    field_id: int,
    field_data: FieldUpdate,
    db: Session = Depends(get_db),
):
    return update_field(db, field_id, field_data)


@router.delete(
    "/{field_id}",
)
def delete_field_endpoint(
    field_id: int,
    db: Session = Depends(get_db),
):
    return delete_field(db, field_id)
