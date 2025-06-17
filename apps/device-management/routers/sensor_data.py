from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from models import SensorData
from database import get_db
from schemas import SensorDataBase, SensorDataResponse

router = APIRouter(
    prefix="/sensor-data",
    tags=["SensorData"]
)

@router.get("/", response_model=List[SensorDataResponse])
def list_sensor_data(db: Session = Depends(get_db)):
    return db.query(SensorData).all()

@router.get("/{data_id}", response_model=SensorDataResponse)
def get_sensor_data(data_id: UUID, db: Session = Depends(get_db)):
    data = db.query(SensorData).filter(SensorData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    return data

@router.post("/", response_model=SensorDataResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_data(data: SensorDataBase, db: Session = Depends(get_db)):
    new_data = SensorData(**data.dict())
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    return new_data

@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor_data(data_id: UUID, db: Session = Depends(get_db)):
    data = db.query(SensorData).filter(SensorData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="Sensor data not found")
    db.delete(data)
    db.commit()
    return
