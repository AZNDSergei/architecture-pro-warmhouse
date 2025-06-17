from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import ServiceRequest

async def init_db():
    client = AsyncIOMotorClient("mongodb://mongo:27017")
    await init_beanie(database=client["service_db"], document_models=[ServiceRequest])
