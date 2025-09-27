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
    PROJECT_NOT_FOUND = "Project not found"
    NO_CHUNKS_FOUND = "No chunks found for the project"
    INSERT_INTO_VECTORDB_ERROR = "Error inserting into vector database"
    PROJECT_INDEXED_SUCCESSFULLY = "Project indexed successfully"
    PROJECT_INDEX_INFO = "Project index info"
    SEARCH_IN_VECTORDB_ERROR = "Error searching in vector database"
    ANSWER_GENERATION_ERROR = "Error generating answer"
