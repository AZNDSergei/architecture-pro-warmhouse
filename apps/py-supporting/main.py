from fastapi import FastAPI
from app.database import init_db
from app.routes import router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(router)
