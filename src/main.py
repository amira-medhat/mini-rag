from fastapi import FastAPI
from .routes.base import base_router
from .routes.data import data_router
from motor.motor_asyncio import AsyncIOMotorClient
from .helpers.config import get_settings, Settings
# from dotenv import load_dotenv
# load_dotenv("src/.env")

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    app_settings: Settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(app_settings.MONGODB_URL)
    app.db_client = app.mongo_conn[app_settings.MONGODB_DATABASE]
    
@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(base_router)
app.include_router(data_router)

