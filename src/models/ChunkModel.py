from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import func, delete

class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client
        
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance
    
        
    async def create_chunk(self, chunk : DataChunk):
        async with self.db_client() as session:            
            async with session.begin():
                session.add(chunk)
                await session.commit()
                await session.refresh(chunk)
        return chunk
    
    async def get_chunk(self, chunk_id: int):
        
        async with self.db_client() as session:            
            async with session.begin():
                chunk = await session.get(DataChunk, chunk_id)
        return chunk
    
    async def insert_many_chunks(self, chunks: list, batch_size : int = 100):
        
        async with self.db_client() as session:            
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    session.add_all(batch)
                await session.commit()
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: int):
        async with self.db_client() as session:            
            async with session.begin():
                stmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(stmt)
                await session.commit()
        return result.rowcount  # Return the number of rows deleted

    async def get_chunks_by_project_id(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = select(DataChunk).where(DataChunk.chunk_project_id == project_id)
                result = await session.execute(query)
                chunks = result.scalars().all()
        return chunks
        