from enum import Enum

class ResponseSignal(Enum):
    """
    Enum for response signals.
    """
    FILE_TYPE_NOT_SUPPORTED = "Invalid file extension"
    FILE_SIZE_EXCEEDED = "File size exceeds the maximum limit"
    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    FILE_UPLOAD_FAILED = "File upload failed"
    FILE_PROCESSED_SUCCESSFULLY = "Processing successful"
    FILE_PROCESSING_FAILED = "Processing failed"
    ASSET_ALREADY_EXISTS = "Asset with this name already exists in the project"
    NO_FILES_TO_PROCESS = "No files available to process in the project"
