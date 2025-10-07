import os
import faiss
import pickle
import numpy as np
import threading
from typing import List, Optional, Tuple
import uuid
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from ....models.db_schemes import RetrievedDocument
import logging
import shutil

class FaissDB(VectorDBInterface):
    def __init__(self, db_path: str, distance_method: str):
        self.db_path = db_path
        self.distance_method = distance_method
        self.index = None
        self.id_map = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.metric = faiss.METRIC_INNER_PRODUCT
        elif distance_method == DistanceMethodEnums.EUCLIDEAN.value:
            self.metric = faiss.METRIC_L2
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.metric = faiss.METRIC_INNER_PRODUCT
        else:
            raise ValueError(f"Unsupported distance method: {distance_method}")

    def connect(self):
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
        self.logger.info(f"Connected to FaissDB at path {self.db_path}")

    def disconnect(self):
        self.index = None
        self.id_map = {}
        self.logger.info("Disconnected from FaissDB")

    def is_collection_existed(self, collection_name: str) -> bool:
        collection_path = os.path.join(self.db_path, collection_name)
        return os.path.exists(collection_path)

    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        collection_path = os.path.join(self.db_path, collection_name)
        index_path = os.path.join(collection_path, f"{collection_name}.index")
        id_map_path = os.path.join(collection_path, f"{collection_name}_id_map.pkl")

        if do_reset and self.is_collection_existed(collection_name):
            shutil.rmtree(collection_path)
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(id_map_path):
                os.remove(id_map_path)

        if not self.is_collection_existed(collection_name):
            os.makedirs(collection_path, exist_ok=True)
            with self.lock:
                if self.distance_method == DistanceMethodEnums.COSINE.value or self.distance_method == DistanceMethodEnums.DOT.value:
                    base_index = faiss.IndexFlatIP(embedding_size)
                elif self.distance_method == DistanceMethodEnums.EUCLIDEAN.value:
                    base_index = faiss.IndexFlatL2(embedding_size)
                else:
                    raise ValueError(f"Unsupported distance method: {self.distance_method}")
                
                # Wrap with IndexIDMap to support add_with_ids
                faiss_index = faiss.IndexIDMap(base_index)

                faiss.write_index(faiss_index, index_path)
                with open(id_map_path, 'wb') as f:
                    pickle.dump({}, f)

    def list_all_collections(self):
        collections = os.listdir(self.db_path)
        return [col[:-6] for col in collections if col.endswith(".index")]
        # Alternatively, if you want to list directories instead of index files:

        # collections = []
        # for file in os.listdir(self.db_path):
        #     if file.endswith(".index"):
        #         collections.append(file[:-6])  # Remove .index extension
        # return collections

    def get_collection_info(self, collection_name: str) -> dict:
        collection_path = os.path.join(self.db_path, collection_name)
        index_path = os.path.join(collection_path, f"{collection_name}.index")
        if not self.is_collection_existed(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist")

        index = faiss.read_index(index_path)
        return {
            "collection_name": collection_name,
            "embedding_size": index.d,
            "num_vectors": index.ntotal,
            "distance_method": self.distance_method
        }
    
    def delete_collection(self, collection_name: str):
        collection_path = os.path.join(self.db_path, collection_name)
        index_path = os.path.join(collection_path, f"{collection_name}.index")
        id_map_path = os.path.join(collection_path, f"{collection_name}_id_map.pkl")

        if self.is_collection_existed(collection_name):
            shutil.rmtree(collection_path)
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(id_map_path):
                os.remove(id_map_path)
            self.logger.info(f"Collection '{collection_name}' deleted")
        else:
            self.logger.warning(f"Collection '{collection_name}' does not exist")

    def insert_one(self, collection_name, text, vector, metadata = None, record_id = None):
        
        try:
            if not self.is_collection_existed(collection_name):
                self.logger.error(f"Collection '{collection_name}' does not exist")
                return False
            with self.lock:
                # Convert vector to numpy
                vec = np.array([vector], dtype='float32')  # shape (1, dim)
                # If you're using cosine similarity, you may normalize:
                if self.distance_method == DistanceMethodEnums.COSINE.value:
                    faiss.normalize_L2(vec)

                # Add to FAISS index (with ID)
                # We assume self.index is an IndexIDMap (or supports add_with_ids)
                self.index.add_with_ids(vec, np.array([record_id], dtype='int64'))

                # Store metadata
                self.id_to_meta[record_id] = {
                    "text": text,
                    "metadata": metadata
                }
                return True
        except Exception as e:
            self.logger.error(f"Error inserting vector: {e}")
            return False

    def insert_many(self, collection_name: str, texts: list, vectors: list, metadata: list = None, record_ids: list = None, batch_size: int = 50):
        try:
            if not self.is_collection_existed(collection_name):
                self.logger.error(f"Collection '{collection_name}' does not exist")
                return False
            if metadata is None:
                    metadata = [None] * len(texts)
            if record_ids is None:
                record_ids = [None] * len(texts)

            num = len(texts)
            # Convert vectors to float32 numpy array once (for all) if you like
            # But here we’ll batch convert per batch
            
            # Load index and metadata
            collection_path = os.path.join(self.db_path, collection_name)
            index_path = os.path.join(collection_path, f"{collection_name}.index")
            id_map_path = os.path.join(collection_path, f"{collection_name}_id_map.pkl")
            
            index = faiss.read_index(index_path)
            with open(id_map_path, 'rb') as f:
                id_to_meta = pickle.load(f)
            
            if record_ids is None:
                record_ids = list(range(len(id_to_meta), len(id_to_meta) + len(texts)))

            # Prepare numpy array
            arr = np.array(vectors, dtype='float32')
            if self.distance_method == DistanceMethodEnums.COSINE.value:
                faiss.normalize_L2(arr)

            with self.lock:
                # Convert record_ids to numpy int64
                ids_np = np.array(record_ids, dtype='int64')

                # Add vectors to FAISS index
                index.add_with_ids(arr, ids_np)

                # Store metadata
                for vid, txt, meta in zip(record_ids, texts, metadata):
                    id_to_meta[vid] = {
                        "text": txt,
                        "metadata": meta
                    }
                
                # Save updated index and metadata
                faiss.write_index(index, index_path)
                with open(id_map_path, 'wb') as f:
                    pickle.dump(id_to_meta, f)

            return True
        except Exception as e:
            self.logger.error(f"Error inserting vectors: {e}")
            return False

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 10) -> List[RetrievedDocument]:

        q = np.array([vector], dtype='float32')

        # If your distance method is cosine, normalize the query vector
        if self.distance_method == DistanceMethodEnums.COSINE.value:
            faiss.normalize_L2(q)

        # Perform search: returns (distances, ids)
        # distances: shape (1, limit)
        # ids: shape (1, limit)
        # Load index and metadata
        collection_path = os.path.join(self.db_path, collection_name)
        index_path = os.path.join(collection_path, f"{collection_name}.index")
        id_map_path = os.path.join(collection_path, f"{collection_name}_id_map.pkl")
        
        index = faiss.read_index(index_path)
        with open(id_map_path, 'rb') as f:
            id_to_meta = pickle.load(f)
            
        D, I = index.search(q, limit)

        # If no results or all invalid IDs
        if I is None or len(I[0]) == 0:
            return None

        results = []
        for dist, vid in zip(D[0], I[0]):
            if vid < 0:
                # FAISS uses -1 or negative id to represent “no more results”
                continue

            # Get metadata / payload
            meta = id_to_meta.get(int(vid))
            if meta is None:
                # If for some reason you have no metadata for that id, skip or handle
                continue

            text = meta.get("text", "")
            other_meta = meta.get("metadata", None)

            # similarity_score: depends on your distance method. For Euclidean, maybe you want to convert
            score = float(dist)

            # If using inner product / cosine, dist is similarity; if using L2, smaller is better.
            # You might convert Euclidean distance to “score = 1 / (1 + dist)” or something, depending.
            results.append(
                RetrievedDocument(
                    similarity_score=score,
                    text=text
                )
            )

        if not results:
            return None

        return results
