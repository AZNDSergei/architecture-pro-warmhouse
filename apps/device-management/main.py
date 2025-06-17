from database import Base, engine
from fastapi import FastAPI
from kafka import get_kafka_producer, shutdown_kafka
from routers.users import router as users_router
from routers.homes import router as homes_router
from routers.rooms import router as rooms_router
from routers.devices import router as devices_router
from routers.sensor_data import router as sensor_data_router
from routers.automation_scenarios import router as automation_scenarios_router
from fastapi.openapi.utils import get_openapi
import models

app = FastAPI(title="Smart Home API")

models.Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    await get_kafka_producer()

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_kafka()

app.include_router(users_router, prefix="/v1.0")
app.include_router(homes_router, prefix="/v1.0")
app.include_router(rooms_router, prefix="/v1.0")
app.include_router(devices_router, prefix="/v1.0")
app.include_router(sensor_data_router, prefix="/v1.0")
app.include_router(automation_scenarios_router, prefix="/v1.0")

openapi_schema = get_openapi(
    title=app.title,
    version="1.0",
    routes=app.routes
)
