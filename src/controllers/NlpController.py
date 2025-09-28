import os
import re

from src.stores.llm.templates.locales import en
from .BaseController import BaseController
from ..models.db_schemes import Project, DataChunk
from ..stores.llm.LLMEnums import DocumentTypeEnums
from typing import List
import json
import logging

class NlpController(BaseController):
    
    def __init__(self, vector_db_client, generation_client, embedding_client, template_parser):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger(__name__)
    
    def create_collection_name(self, project_id: str) -> str:
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        if self.vector_db_client.is_collection_existed(collection_name=collection_name):
            return self.vector_db_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project) -> dict:
        collection_name = self.create_collection_name(project_id=project.project_id)
        if self.vector_db_client.is_collection_existed(collection_name=collection_name):
            collection_info = self.vector_db_client.get_collection_info(collection_name=collection_name)
            # return json.loads(json.dumps(collection_info, default=lambda x: x.__dict__))
            return collection_info

    def index_into_vector_db(self, project: Project, chunks: List[DataChunk], do_reset: bool = False):
        collection_name = self.create_collection_name(project_id=project.project_id)
        if do_reset:
            self.reset_vector_db_collection(project=project)
        if not self.vector_db_client.is_collection_existed(collection_name=collection_name):
            self.vector_db_client.create_collection(collection_name=collection_name, embedding_size=self.embedding_client.embedding_size)
        
        
        batch_size = 50
        if len(chunks) > batch_size:
            for i in range(0, len(chunks), batch_size):
                texts = [chunk.chunk_text for chunk in chunks[i:i+batch_size]]
                vectors = self.embedding_client.embed_text(text=texts, document_type=DocumentTypeEnums.DOCUMENT.value)
                metadatas = [chunk.chunk_metadata for chunk in chunks[i:i+batch_size]]
                record_ids = list(range(i, i + batch_size))
                inserted_count = self.vector_db_client.insert_many(
                    collection_name=collection_name,
                    texts=texts,
                    vectors=vectors,
                    metadata=metadatas,
                    record_ids = record_ids
                )
        return True

    def search_from_vector_db(self, project: Project, query: str, limit: int = 10):
        collection_name = self.create_collection_name(project_id=project.project_id)
        if not self.vector_db_client.is_collection_existed(collection_name=collection_name):
            self.logger.error(f"Collection '{collection_name}' does not exist")
            return False
        # This will now return a list containing one item: [[...]]
        list_of_vectors = self.embedding_client.embed_text(text=query, document_type=DocumentTypeEnums.QUERY.value)

        if not list_of_vectors:
            self.logger.error(f"Error embedding query: {query}")
            return False

        # FIX: Extract the single vector from the list
        query_vector = list_of_vectors[0]

        results = self.vector_db_client.search_by_vector(collection_name=collection_name, vector=query_vector, limit=limit)
        if results == None:
            self.logger.error(f"Error searching in Vector DB: {query}")
            return False
        return results

    def answer_rag_question(self, project: Project, question: str, limit : int = 10):
        answer, full_prompt, chat_history = None, None, None
        search_results = self.search_from_vector_db(project=project, query=question, limit=limit)
        if not search_results:
            self.logger.error(f"No search results found for question: {question}")
            return answer, full_prompt, chat_history

        # Create the system prompt for the generation model
        system_prompt = self.template_parser.load_template(group = "rag", key = "system_prompt")

        # Create the document prompt for the retrieved documents
        context_documents = [
            self.template_parser.load_template(group = "rag", key = "document_prompt", vars={"doc_index": idx + 1, "document_text": doc.text})
            for idx, doc in enumerate(search_results)
        ]
        context_prompt = "\n\n".join(context_documents)

        footer_prompt = self.template_parser.load_template(group = "rag", key = "footer_prompt", vars={"query": question})

        chat_history = [
            self.generation_client.construct_prompt(system_prompt, self.generation_client.enums.SYSTEM.value),
        ]

        full_prompt = "\n\n".join([context_prompt, footer_prompt])
        
        # Generate the answer using the generation client

        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )
        return answer, full_prompt, chat_history

