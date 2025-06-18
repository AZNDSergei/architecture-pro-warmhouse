from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from database import Base, engine           
from kafka import shutdown_kafka            
import models                              


from routers.users                import router as users_router
from routers.homes                import router as homes_router
from routers.rooms                import router as rooms_router
from routers.devices              import router as devices_router
from routers.sensor_data          import router as sensor_data_router
from routers.automation_scenarios import router as automation_scenarios_router


app = FastAPI(
    title="Smart Home API",
    version="2.0",
    description="REST & Kafka gateway for the smart-home platform",
)

Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
async def _shutdown() -> None:
    """Закрываем AIOKafkaProducer при остановке приложения."""
    await shutdown_kafka()

API_PREFIX = "/api/v2.0"

app.include_router(users_router,                prefix=API_PREFIX)
app.include_router(homes_router,                prefix=API_PREFIX)
app.include_router(rooms_router,                prefix=API_PREFIX)
app.include_router(devices_router,              prefix=API_PREFIX)
app.include_router(sensor_data_router,          prefix=API_PREFIX)
app.include_router(automation_scenarios_router, prefix=API_PREFIX)


@app.get("/openapi.json", include_in_schema=False)
def custom_openapi():   
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
