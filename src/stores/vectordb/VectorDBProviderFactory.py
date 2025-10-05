from ..vectordb.providers.QdrantDB import QdrantDB
from ..vectordb.providers.FaissDB import FaissDB
from ..vectordb.VectorDBEnums import VectorDBEnums
from ...controllers import BaseController

class VectorDBProviderFactory:

    def __init__(self, config):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            db_path = self.base_controller.get_database_path(self.config.VECTOR_DB_PATH)
            distance_method = self.config.VECTOR_DB_DISTANCE_METHOD
            return QdrantDB(db_path=db_path, distance_method=distance_method)
        if provider == VectorDBEnums.FAISS.value:
            db_path = self.base_controller.get_database_path(self.config.VECTOR_DB_PATH)
            distance_method = self.config.VECTOR_DB_DISTANCE_METHOD
            return FaissDB(db_path=db_path, distance_method=distance_method)
        else:
            raise ValueError(f"Unsupported vector DB provider: {provider}")