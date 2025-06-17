import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime

from models import Device
from database import get_db
from schemas import DeviceBase, DeviceResponse
from kafka import get_kafka_producer
from aiokafka import AIOKafkaProducer


router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)
):
    return db.query(Device).all()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: UUID, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(device_data: DeviceBase, db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    device = Device(**device_data.dict())
    db.add(device)
    db.commit()
    db.refresh(device)

    try:
        await producer.send_and_wait(
            topic="newDeviceNotification",
            key=str(device.id).encode(),
            value=json.dumps({
                "id": str(device.id),
                "name": device.name,
                "type": device.type.value,
                "model": device.model,
                "firmware_version": device.firmware_version,
                "status": device.status,
                "home_id": str(device.home_id),
                "room_id": str(device.room_id),
                "is_activated": device.is_activated,
            }).encode("utf-8")
        )
        print("Message sent via aiokafka")
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

    return device


@router.post("/activate", response_model=DeviceResponse)
async def activate_device(activation_code: str, home_id: UUID, room_id: UUID, db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    device = db.query(Device).filter(Device.activation_code == activation_code).first()
    if not device:
        raise HTTPException(status_code=404, detail="Activation code not found")
    if device.is_activated:
        raise HTTPException(status_code=400, detail="Device already activated")

    device.home_id = home_id
    device.room_id = room_id
    device.is_activated = True
    device.activated_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    try:
        await producer.send_and_wait(
            topic="uiActivatedCommand",
            key=str(device.id).encode(),
            value=json.dumps({
                "id": str(device.id),
                "name": device.name,
                "type": device.type.value,
                "model": device.model,
                "firmware_version": device.firmware_version,
                "status": device.status,
                "home_id": str(device.home_id),
                "room_id": str(device.room_id),
                "is_activated": device.is_activated,
            }).encode("utf-8")
        )
        print("Message sent via aiokafka")
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: UUID, device_data: DeviceBase, db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for field, value in device_data.dict().items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    try:
        await producer.send_and_wait(
            topic="uiCommand",
            key=str(device.id).encode(),
            value=json.dumps({
                "id": str(device.id),
                "name": device.name,
                "type": device.type.value,
                "model": device.model,
                "firmware_version": device.firmware_version,
                "status": device.status,
                "home_id": str(device.home_id),
                "room_id": str(device.room_id),
                "is_activated": device.is_activated,
            }).encode("utf-8")
        )
        print("Message sent via aiokafka")
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: UUID, db: Session = Depends(get_db),
    producer: AIOKafkaProducer = Depends(get_kafka_producer)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()

    try:
        await producer.send_and_wait(
            topic="deleteDeviceNotification",
            key=str(device.id).encode(),
            value=json.dumps({
                "id": str(device.id),
            }).encode("utf-8")
        )
        print("Message sent via aiokafka")
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

    return
