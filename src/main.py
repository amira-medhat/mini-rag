from fastapi import FastAPI
from .routes.base import base_router
from .routes.data import data_router
from dotenv import load_dotenv
load_dotenv("src/.env")

app = FastAPI()

app.include_router(base_router)
app.include_router(data_router)

