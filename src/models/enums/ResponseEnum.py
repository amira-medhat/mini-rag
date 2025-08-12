from enum import Enum

class ResponseSignal(Enum):
    """
    Enum for response signals.
    """
    FILE_TYPE_NOT_SUPPORTED = "Invalid file extension"
    FILE_SIZE_EXCEEDED = "File size exceeds the maximum limit"
    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    FILE_UPLOAD_FAILED = "File upload failed"
