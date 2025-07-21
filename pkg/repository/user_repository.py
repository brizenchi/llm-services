from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def fetch_newsletter_members(self) -> Dict[str, Any]:
        query = """
        SELECT * FROM users WHERE enable_news_letter = 1
        """
        result = await self.db.execute_query(query)
        return result
