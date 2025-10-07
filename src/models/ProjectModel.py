from venv import create
from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from .enums.DataBaseEnum import DataBaseEnum
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client
        
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance
        
        
    async def create_project(self, project : Project):
        async with self.db_client() as session:            
            async with session.begin():
                session.add(project)
                await session.commit()
                await session.refresh(project)
        return project

    
    async def get_project_or_create_one(self, project_id: int):
        async with self.db_client() as session:            
            async with session.begin():
                project = await session.get(Project, project_id)
                if not project:
                    new_project = Project(project_id=project_id)
                    new_project = await self.create_project(new_project)
                    return new_project
                return project
    
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        
        async with self.db_client() as session:            
            async with session.begin():

                # So after this line, total_docs is a SQLAlchemy Result object, not a number yet
                total_docs = await session.execute(select(func.count()).select_from(Project))  # select(func.count()) → generates SQL like
                total_docs = total_docs.scalar_one() # Extract the actual count from the Result object
                total_pages = total_docs // page_size + (1 if total_docs % page_size > 0 else 0)
                query = select(Project).offset((page - 1) * page_size).limit(page_size) # SQLAlchemy ORM query
                projects = await session.execute(query).scalars().all() # Execute the query and fetch all results, So projects ends up as a list of Project objects for that page
                return projects, total_pages # Return the list of projects (list of Project objects) and total pages(int)
