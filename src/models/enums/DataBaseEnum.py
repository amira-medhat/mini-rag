from enum import Enum

class DataBaseEnum(Enum):
    """
    Enum for database collections.
    """
    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_CHUNK_NAME = "chunks"