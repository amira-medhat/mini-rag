from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
import aiofiles
from ..helpers.config import get_settings, Settings
from ..controllers import DataController, BaseController, ProjectController, ProcessController
from ..models.enums.ResponseEnum import ResponseSignal
import logging
from .schemes import ProcessRequest
from ..models.ProjectModel import ProjectModel
from ..models.ChunkModel import ChunkModel
from ..models.db_schemes import DataChunk

logger = logging.getLogger('uvicorn.error')
data_router = APIRouter(prefix="/api/v1/data", tags=["data"])

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, file: UploadFile, app_settings: Settings = Depends(get_settings), project_id: str = None):
    
    project_model = ProjectModel(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    # validate incoming file
    
    is_valid, result_signal = DataController().validate_uploaded_file(file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"{result_signal}"}
        )
    
    # get project path
    project_path = ProjectController().get_project_path(project_id)
    file_path = os.path.join(project_path, file.filename)
    file_id = file.filename

    try:    
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_CHUNK_SIZE):
                await out_file.write(chunk)
                
    except Exception as e:
        
        logger.error(f"Error uploading file: {e}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"{ResponseSignal.FILE_UPLOAD_FAILED.value}"}
        )
    
    return JSONResponse(
    content={"message": f"{result_signal}"
            ,"file_id": f"{file_id}"
            }
)


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, process_request: ProcessRequest, project_id: str = None):
    """
    Process the uploaded file.
    """
    project_model = ProjectModel(db_client=request.app.db_client)
    
    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    

    process_controller = ProcessController(project_id=project_id)
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
            chunk_order=index + 1,
            chunk_project_id=project.id
        ) for index, chunk in enumerate(file_chunks)
    ]
    
    chunk_model = ChunkModel(db_client=request.app.db_client)

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.id)
        
    no_records = await chunk_model.insert_many_chunks(chunks=file_chunks_records)
    return JSONResponse(
        content={"message": f"{ResponseSignal.FILE_PROCESSED_SUCCESSFULLY.value}"
                ,"file_id": f"{file_id}"
                ,"no_of_chunks": no_records
                }
    )