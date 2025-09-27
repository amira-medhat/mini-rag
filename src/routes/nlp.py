from gc import collect
from fastapi import FastAPI, APIRouter, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
from typing import List
import os
import aiofiles

from src.routes.schemes import nlp
from src.stores.llm.templates import template_parser
from ..helpers.config import get_settings, Settings
from ..controllers import DataController, BaseController, ProjectController, ProcessController
from ..models.enums.ResponseEnum import ResponseSignal
from ..models.enums.AssetTypeEnum import AssetTypeEnum
import logging
from .schemes import ProcessRequest, PushRequest, SearchRequest
from ..models.ProjectModel import ProjectModel
from ..models.ChunkModel import ChunkModel
from ..models.AssetModel import AssetModel
from ..models.db_schemes import DataChunk
from ..models.db_schemes import Asset
from pymongo.errors import DuplicateKeyError
from ..controllers import NlpController

logger = logging.getLogger('uvicorn.error')
nlp_router = APIRouter(prefix="/api/v1/nlp", tags=["api_v1", "nlp"])

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.PROJECT_NOT_FOUND.value}"}
        )

    nlp_controller = NlpController(
        vector_db_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client)

    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
    chunks = await chunk_model.get_chunks_by_project_id(project_id=project.id)
    if not chunks:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.NO_CHUNKS_FOUND.value}"}
        )
    
    is_inserted = nlp_controller.index_into_vector_db(project=project, chunks=chunks, do_reset=push_request.do_reset)
    if not is_inserted:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value}", "inserted_items": f"{len(chunks)}"}
        )
    
    return JSONResponse(
        content={"message": f"{ResponseSignal.PROJECT_INDEXED_SUCCESSFULLY.value}"}
    )

@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.PROJECT_NOT_FOUND.value}"}
        )

    nlp_controller = NlpController(
    vector_db_client=request.app.vector_db_client,
    generation_client=request.app.generation_client,
    embedding_client=request.app.embedding_client)

    collection_info = nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(
        content={"collection_info": collection_info.dict()}
    )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NlpController(
    vector_db_client=request.app.vector_db_client,
    generation_client=request.app.generation_client,
    embedding_client=request.app.embedding_client,
    template_parser=request.app.template_parser)

    results = nlp_controller.search_from_vector_db(project=project, query=search_request.query, limit=search_request.top_k)
    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.SEARCH_IN_VECTORDB_ERROR.value}"}
        )
    results_as_dicts = [result.model_dump() for result in results]

    return JSONResponse(
        content={"results" : results_as_dicts}
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NlpController(
    vector_db_client=request.app.vector_db_client,
    generation_client=request.app.generation_client,
    embedding_client=request.app.embedding_client,
    template_parser=request.app.template_parser)

    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(project=project, question=search_request.query, limit=search_request.top_k)
    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.ANSWER_GENERATION_ERROR.value}"}
        )

    return JSONResponse(
        content={"answer" : answer, "full_prompt": full_prompt, "chat_history": chat_history}
    )