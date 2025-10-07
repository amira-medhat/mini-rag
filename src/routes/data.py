from fastapi import FastAPI, APIRouter, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
from typing import List
import os
import aiofiles
from ..helpers.config import get_settings, Settings
from ..controllers import DataController, BaseController, ProjectController, ProcessController
from ..models.enums.ResponseEnum import ResponseSignal
from ..models.enums.AssetTypeEnum import AssetTypeEnum
import logging
from .schemes import ProcessRequest
from ..models.ProjectModel import ProjectModel
from ..models.ChunkModel import ChunkModel
from ..models.AssetModel import AssetModel
from ..models.db_schemes import DataChunk, Asset
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger('uvicorn.error')
data_router = APIRouter(prefix="/api/v1/data", tags=["data"])

@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    files: List[UploadFile] = File(...),
    app_settings: Settings = Depends(get_settings),
    project_id: int = None
):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

    results = []  # collect results for all files

    for file in files:
        # validate each file
        is_valid, result_signal = DataController().validate_uploaded_file(file)
        if not is_valid:
            results.append({
                "file_name": file.filename,
                "status": "failed",
                "message": result_signal
            })
            continue

        # save file to disk
        project_path = ProjectController().get_project_path(project_id)
        file_path = os.path.join(project_path, file.filename)
        file_id = file.filename

        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                    await out_file.write(chunk)
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {e}")
            results.append({
                "file_name": file.filename,
                "status": "failed",
                "message": ResponseSignal.FILE_UPLOAD_FAILED.value
            })
            continue

        # store the asset record in DB
        asset_resource = Asset(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.TYPE_FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )

        try:
            asset_record = await asset_model.create_asset(asset=asset_resource)
            results.append({
                "file_name": file.filename,
                "status": "success",
                "message": result_signal,
                "file_id": str(asset_record.asset_id)
            })
        except DuplicateKeyError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"{ResponseSignal.ASSET_ALREADY_EXISTS.value}: {file.filename}"}
            )
            # results.append({
            #     "file_name": file.filename,
            #     "status": "failed",
            #     "message": ResponseSignal.ASSET_ALREADY_EXISTS.value
            # })

    return JSONResponse(content={"results": results})

@data_router.get("/reset_stored_data/{project_id}")
async def reset_data_by_project_id(request: Request, project_id: int = None):
    """
    Delete all uploaded assets in the database and locally for a project and also their assosiated chunks.
    """
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
    
    # Delete all chunks associated with this project
    deleted_chunks_count = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)
    
    # Get all assets associated with this project and delete them from the database
    project_assets = await asset_model.get_all_project_assets(asset_project_id=project.project_id, asset_type=AssetTypeEnum.TYPE_FILE.value)
    
    deleted_files_count = 0
    for asset in project_assets:
        file_path = os.path.join(ProjectController().get_project_path(project.project_id), asset.asset_name)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files_count += 1
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
    
    # Delete asset records from the database
    deleted_assets_count = await asset_model.delete_assets_by_project_id(project_id=project.project_id, asset_type=AssetTypeEnum.TYPE_FILE.value)
    
    return JSONResponse(
        content={"message": f"{ResponseSignal.PROJECT_DATA_RESET_SUCCESSFULLY.value}",
                "deleted_chunks": deleted_chunks_count,
                "deleted_files": deleted_files_count,
                "deleted_assets": deleted_assets_count
                }
    )

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, process_request: ProcessRequest, project_id: int = None):
    """
    Process the uploaded file.
    """
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    # file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    project_file_ids = []
    if process_request.file_id:
        project_file_ids = [process_request.file_id]
    else:
        asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
        project_assets = await asset_model.get_all_project_assets(asset_project_id=project.project_id, asset_type=AssetTypeEnum.TYPE_FILE.value)
        project_file_ids = [asset.asset_name for asset in project_assets]
        
    if not project_file_ids or len(project_file_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{ResponseSignal.NO_FILES_TO_PROCESS.value}"}
        )
    
    process_controller = ProcessController(project_id=project_id)
    no_records = 0
    no_files = 0
    
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    
    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)
    

    for file_id in project_file_ids:
        
        # Get asset record for this file
        asset_record = await asset_model.get_asset_record(asset_project_id=project.project_id, asset_name=file_id)
        if not asset_record:
            continue
            
        file_content = process_controller.get_file_content(file_id=file_id)
        
        file_chunks = process_controller.process_file_content(
            file_id=file_id,
            file_content=file_content,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )
        
        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": f"{ResponseSignal.FILE_PROCESSING_FAILED.value}"}
            )
            
        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_asset_id=asset_record.asset_id,
                chunk_project_id=project.project_id
            ) for index, chunk in enumerate(file_chunks)
        ]
        

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1
    return JSONResponse(
        content={"message": f"{ResponseSignal.FILE_PROCESSED_SUCCESSFULLY.value}"
                ,"inserted_chunks": no_records,
                "processed_files": no_files
                }
    )