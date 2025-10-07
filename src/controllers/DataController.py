from fastapi import UploadFile
from .BaseController import BaseController
from ..models.enums.ResponseEnum import ResponseSignal


class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
        
    def validate_uploaded_file(self, file: UploadFile):
        allowed_extensions = self.app_settings.FILE_ALLOWED_EXTENSIONS
        max_size_mb = self.app_settings.FILE_MAX_SIZE_MB
        
        # Check file extension
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        
        # Check file size
        if file.size > max_size_mb * 1024 * 1024:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value