from fastapi import FastAPI
from .routes.base import base_router
from .routes.data import data_router
from motor.motor_asyncio import AsyncIOMotorClient
from .helpers.config import get_settings, Settings
from stores.llm.LLMProviderFactory import LLMProviderFactory

# from dotenv import load_dotenv
# load_dotenv("src/.env")

app = FastAPI()


async def startup_db_client():
    app_settings: Settings = get_settings()
    app.mongo_conn = AsyncIOMotorClient(app_settings.MONGODB_URL)
    app.db_client = app.mongo_conn[app_settings.MONGODB_DATABASE]
    llm_factory = LLMProviderFactory(app_settings)
    app.generation_client = llm_factory.create(app_settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(app_settings.GENERATION_MODEL)
    app.embedding_client = llm_factory.create(app_settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        app_settings.EMBEDDING_MODEL, app_settings.EMBEDDING_SIZE
    )


async def shutdown_db_client():
    app.mongodb_client.close()


app.router.lifespan.on_startup.append(startup_db_client)
app.router.lifespan.on_shutdown.append(shutdown_db_client)

app.include_router(base_router)
app.include_router(data_router)
