from fastapi import APIRouter
from app.models import ServiceRequest

router = APIRouter()

@router.post("/request")
async def create_request(data: ServiceRequest):
    await data.create()
    return {"id": str(data.id)}

@router.get("/requests")
async def list_requests():
    return await ServiceRequest.find_all().to_list()
