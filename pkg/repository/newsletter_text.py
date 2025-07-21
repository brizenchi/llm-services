from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class NewsletterTextRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_newsletter_text(self,date: str, language: str,folder_id: int, content: str):
        """保存邮件摘要"""
        try:           
            query = """
                INSERT INTO newsletter_text (date, language,folder_id, content, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            logger.info(f"Saving newsletter text for date: {date}")
            results = await self.db.execute_update(query, (date, language,folder_id, content))
            logger.info(f"Saved newsletter text for {date}")
            return results
        except Exception as e:
            logger.error(f"Error saving newsletter text: {e}")
            raise
    async def query_newsletter_text(self,date: str, language: str,folder_id: int):
        """查询邮件摘要"""
        try:
            query = """
                SELECT * FROM newsletter_text WHERE date = %s AND language = %s AND folder_id = %s
            """
            results = await self.db.execute_query(query, (date, language,folder_id))
            logger.info(f"Found newsletter text for {date}")
            return results
        except Exception as e:
            logger.error(f"Error querying newsletter text: {e}")
            raise
