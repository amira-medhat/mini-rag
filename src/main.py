from fastapi import FastAPI
from .routes.base import base_router
from .routes.data import data_router
from .routes.nlp import nlp_router
from motor.motor_asyncio import AsyncIOMotorClient
from .helpers.config import get_settings, Settings
from .stores.llm.LLMProviderFactory import LLMProviderFactory
from .stores.llm.templates.template_parser import TemplateParser
from .stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# from dotenv import load_dotenv
# load_dotenv("src/.env")

app = FastAPI()


async def startup_span():
    app_settings: Settings = get_settings()
    postgres_conn = f"postgresql+asyncpg://{app_settings.POSTGRES_USERNAME}:{app_settings.POSTGRES_PASSWORD}@{app_settings.POSTGRES_HOST}:{app_settings.POSTGRES_PORT}/{app_settings.POSTGRES_MAIN_DB}"
    app.db_engine = create_async_engine(postgres_conn, echo=True)
    app.async_session = sessionmaker(
        app.db_engine, expire_on_commit=False, class_=AsyncSession
    )
    # app.mongo_conn = AsyncIOMotorClient(app_settings.MONGODB_URL)
    # app.db_client = app.mongo_conn[app_settings.MONGODB_DATABASE]
    app.db_client = app.async_session
    llm_factory = LLMProviderFactory(app_settings)
    app.generation_client = llm_factory.create(app_settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(app_settings.GENERATION_MODEL)
    app.embedding_client = llm_factory.create(app_settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        app_settings.EMBEDDING_MODEL, app_settings.EMBEDDING_SIZE
    )
    vectordb_factory = VectorDBProviderFactory(app_settings)
    app.vector_db_client = vectordb_factory.create(app_settings.VECTOR_DB_BACKEND)
    app.vector_db_client.connect()

    app.template_parser = TemplateParser(language=app_settings.DESIRED_LANGUAGE, default_language=app_settings.DEFAULT_LANGUAGE)


async def shutdown_span():
    # app.mongodb_client.close()
    await app.db_engine.dispose()
    app.vector_db_client.disconnect()


app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base_router)
app.include_router(data_router)
app.include_router(nlp_router)
