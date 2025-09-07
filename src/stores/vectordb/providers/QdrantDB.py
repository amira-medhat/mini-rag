from os import path
from turtle import mode
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from qdrant_client import models, QdrantClient
import logging
from typing import List


class QdrantDB(VectorDBInterface):
    
    def __init__(self, db_path: str, distance_method: str):
        self.db_path = db_path
        self.distance_method = None
        self.client = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.EUCLIDEAN.value:
            self.distance_method = models.Distance.EUCLIDEAN 
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        
        self.logger = logging.getLogger(__name__)

    def connect(self):
        try:
            self.client = QdrantClient(path=self.db_path)
            self.logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {e}")

    def disconnect(self):
        self.client = None
        self.logger.info("Disconnected from Qdrant")

    def is_collection_existed(self, collection_name: str) -> bool:
        try:
            return self.client.collection_exists(collection_name=collection_name)
        except Exception as e:
            self.logger.error(f"Error checking collection existence: {e}")

    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        try:
            if do_reset and self.is_collection_existed(collection_name):
                _ = self.delete_collection(collection_name)
            if not self.is_collection_existed(collection_name):
                _ =  self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=embedding_size, distance=self.distance_method),
                )
                return True
            else:
                self.logger.info(f"Collection '{collection_name}' already exists")
                return False
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")

    def list_all_collections(self) -> List:
        try:
            return self.client.get_collections()
        except Exception as e:
            self.logger.error(f"Error listing collections: {e}")

    def get_collection_info(self, collection_name: str) -> dict:
        try:
            return self.client.get_collection(collection_name=collection_name)
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")


    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            try:
                return self.client.delete_collection(collection_name="{collection_name}")
            except Exception as e:
                self.logger.error(f"Error deleting collection: {e}")
        else:
            self.logger.warning(f"Collection '{collection_name}' does not exist")

    def insert_one(self, collection_name: str, text: str, vector: list, metadata: dict = None
    , record_id: str = None) -> str:
        try:
            if not self.is_collection_existed(collection_name):
                self.logger.error(f"Collection '{collection_name}' does not exist")
                return False

            _ = self.client.upload_points(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        # id=record_id,
                        vector=vector,
                        payload={"text": text, "metadata": metadata},
                    )
                ],
            )
            return True
        except Exception as e:
            self.logger.error(f"Error inserting point: {e}")
            return False

    def insert_many(self, collection_name: str, texts: list, vectors: list, metadata: list = None
    , record_ids: list = None, batch_size: int = 50):
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = [None] * len(texts)

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            batch_metadata = metadata[i:i + batch_size]
            batch_record_ids = record_ids[i:i + batch_size]

            for x in range(len(batch_texts)):
                points = [
                    models.PointStruct(
                        # id=batch_record_ids[x],
                        vector=batch_vectors[x],
                        payload={"text": batch_texts[x], "metadata": batch_metadata[x]},
                    )
                ]

            try:
                _ = self.client.upload_points(
                    collection_name=collection_name,
                    points=points,
                )
                return True
            except Exception as e:
                self.logger.error(f"Error inserting points batch: {e}")
                return False

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 10):
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
        )
