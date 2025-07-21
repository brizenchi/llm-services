from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class NewsletterLogsRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_newsletter_log(self,email: str, log: str):
        """保存摘要"""
        try:
            # 将passage_ids排序并转换为逗号分隔的字符串
           
            query = """
                INSERT INTO newsletter_logs (email, log, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())
            """
            logger.info(f"Saving newsletter log for email: {email}")
            results = await self.db.execute_update(query, (email, log))
            logger.info(f"Saved newsletter log for {email}")
            return results
        except Exception as e:
            logger.error(f"Error saving newsletter log: {e}")
            raise
    