from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from models import Home
from database import get_db
from schemas import HomeBase, HomeResponse

router = APIRouter(
    prefix="/homes",
    tags=["Homes"]
)

@router.get("/", response_model=List[HomeResponse])
def list_homes(db: Session = Depends(get_db)):
    return db.query(Home).all()

@router.get("/{home_id}", response_model=HomeResponse)
def get_home(home_id: UUID, db: Session = Depends(get_db)):
    home = db.query(Home).filter(Home.id == home_id).first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found")
    return home

@router.post("/", response_model=HomeResponse, status_code=status.HTTP_201_CREATED)
def create_home(home_data: HomeBase, db: Session = Depends(get_db)):
    home = Home(**home_data.dict())
    db.add(home)
    db.commit()
    db.refresh(home)
    return home

@router.put("/{home_id}", response_model=HomeResponse)
def update_home(home_id: UUID, home_data: HomeBase, db: Session = Depends(get_db)):
    home = db.query(Home).filter(Home.id == home_id).first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found")
    for field, value in home_data.dict().items():
        setattr(home, field, value)
    db.commit()
    db.refresh(home)
    return home

@router.delete("/{home_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_home(home_id: UUID, db: Session = Depends(get_db)):
    home = db.query(Home).filter(Home.id == home_id).first()
    if not home:
        raise HTTPException(status_code=404, detail="Home not found")
    db.delete(home)
    db.commit()
    return
