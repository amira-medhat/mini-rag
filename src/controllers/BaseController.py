from ..helpers.config import get_settings, Settings
import os

class BaseController:
    
    def __init__(self):
        self.app_settings: Settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir, "assets/files")
        self.database_dir = os.path.join(self.base_dir, "assets/database")

    def get_database_path(self, db_name: str) -> str:

        database_path = os.path.join(self.database_dir, db_name)

        if not os.path.exists(database_path):
            os.makedirs(database_path)

        return database_path

