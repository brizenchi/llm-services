from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class NewsletterWechatRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_newsletter_wechat(self,date: str, language: str,folder_id: int, content: str):
        """保存邮件wechat"""
        try:           
            query = """
                INSERT INTO newsletter_wechat (date, language,folder_id, content, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            logger.info(f"Saving newsletter wechat for date: {date}")
            results = await self.db.execute_update(query, (date, language,folder_id, content))
            logger.info(f"Saved newsletter wechat for {date}")
            return results
        except Exception as e:
            logger.error(f"Error saving newsletter wechat: {e}")
            raise
    async def query_newsletter_wechat(self,date: str, language: str,folder_id: int):
        """查询邮件wechat"""
        try:
            query = """
                SELECT * FROM newsletter_wechat WHERE date = %s AND language = %s AND folder_id = %s
            """
            results = await self.db.execute_query(query, (date, language,folder_id))
            logger.info(f"Found newsletter wechat for {date}")
            return results
        except Exception as e:
            logger.error(f"Error querying newsletter wechat: {e}")
            raise
