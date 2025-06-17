from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime

class ServiceRequest(Document):
    customerId: int
    description: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "requests"
