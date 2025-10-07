from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class Asset(SQLAlchemyBase):
    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(100), nullable=False)
    asset_size = Column(Integer, nullable=True)  # Size in bytes
    asset_config = Column(JSONB, nullable=True)  # Additional metadata in JSON format

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project = relationship("Project", back_populates="assets")
    data_chunks = relationship("DataChunk", back_populates="asset")

    __table_args__ = (
        Index("idx_asset_project_id", "asset_project_id"),
        Index("idx_asset_type", "asset_type"),
    )