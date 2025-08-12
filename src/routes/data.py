from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
import aiofiles
from ..helpers.config import get_settings, Settings
from ..controllers import DataController, BaseController, ProjectController
from ..models.enums.ResponseEnum import ResponseSignal
import logging

logger = logging.getLogger('uvicorn.error')
data_router = APIRouter(prefix="/api/v1/data", tags=["data"])

@data_router.post("/upload/{project_id}")
async def upload_data(file: UploadFile, app_settings: Settings = Depends(get_settings), project_id: str = None):
    
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
    content={"message": f"{result_signal}"}
)