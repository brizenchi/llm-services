from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class UserFoldersRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def fetch_user_folders(self, user_id: str) -> Dict[str, Any]:
        query = """
        SELECT * FROM user_folders WHERE user_id = %s and deleted_at is null  order by folder_id 
        """
        result = await self.db.execute_query(query, (user_id,))
        return result
