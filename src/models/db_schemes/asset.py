from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class Asset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    asset_project_id: Optional[ObjectId]
    asset_name: str = Field(..., min_length=1)
    asset_type: str = Field(..., min_length=1)
    asset_size: int = Field(ge=0, default=None)
    asset_config: dict = Field(default=None)
    asset_pushed_at: datetime = Field(default=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_indexes_scheme(cls):
        return [
            {"key": [("asset_project_id", 1)],
            "name": "idx_asset_project_id",
            "unique": False},
            {"key": [("asset_name", 1),
                    ("asset_project_id", 1)],
            "name": "idx_project_id_asset_name",
            "unique": True}
        ]