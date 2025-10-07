from .BaseDataModel import BaseDataModel
from .db_schemes import Asset
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from sqlalchemy.future import select
from sqlalchemy import func, delete


class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client
        
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance
        
    async def create_asset(self, asset : Asset):
        async with self.db_client() as session:            
            async with session.begin():
                session.add(asset)
                await session.flush()
                await session.refresh(asset)
        return asset

    async def get_all_project_assets(self, asset_project_id: int, asset_type: str = None):
        async with self.db_client() as session:            
            async with session.begin():
                if asset_type:
                    assets = await session.execute(select(Asset).where(Asset.asset_project_id == asset_project_id, Asset.asset_type == asset_type))
                else:
                    assets = await session.execute(select(Asset).where(Asset.asset_project_id == asset_project_id))
                assets = assets.scalars().all()
        return assets


    async def get_asset_record(self, asset_project_id: int, asset_name: str):
        async with self.db_client() as session:            
            async with session.begin():
                asset = await session.execute(select(Asset).where(Asset.asset_project_id == asset_project_id, Asset.asset_name == asset_name))
                asset = asset.scalars().first()
        return asset

    async def delete_assets_by_project_id(self, project_id: int, asset_type: str = None):
        async with self.db_client() as session:
            async with session.begin():
                stmt = delete(Asset).where(Asset.asset_project_id == project_id, Asset.asset_type == asset_type) if asset_type else delete(Asset).where(Asset.asset_project_id == project_id)
                result = await session.execute(stmt)
                await session.commit()
        return result.rowcount  # Return the number of rows deleted
