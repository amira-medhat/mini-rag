from fastapi import FastAPI, APIRouter, Depends
import os
from ..helpers.config import get_settings, Settings

base_router = APIRouter(prefix="/api/v1", tags=["base"])

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    
    # app_settings = get_settings()
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
    app_env = app_settings.APP_ENV
    
    
    # app_name = os.getenv("APP_NAME")
    # app_version = os.getenv("APP_VERSION")
    # app_env = os.getenv("APP_ENV")
    
    return {"message": "Welcome to mini-rag!",
            "app_name": app_name,
            "app_version": app_version,
            "app_env": app_env}