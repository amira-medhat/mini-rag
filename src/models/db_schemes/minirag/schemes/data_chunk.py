from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from pydantic import BaseModel, Field

class DataChunk(SQLAlchemyBase):
    __tablename__ = "data_chunks"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    chunk_asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=False)
    chunk_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)  # Additional metadata in JSON format

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    asset = relationship("Asset", back_populates="data_chunks")
    project = relationship("Project", back_populates="data_chunks")

    __table_args__ = (
        Index("idx_chunk_asset_id", "chunk_asset_id"),
        Index("idx_chunk_project_id", "chunk_project_id"),
    )

class RetrievedDocument(BaseModel):
    
    similarity_score: float = Field(..., gt=0)
    text: str
