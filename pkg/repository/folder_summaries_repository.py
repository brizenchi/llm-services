from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FolderSummariesRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_summary(self,language: str, folder_id: str, summary: str,start_at: str, end_at: str):
        """保存摘要"""
        try:
            # 将passage_ids排序并转换为逗号分隔的字符串
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           
            query = """
                INSERT INTO folder_summaries (folder_id, summary, start_at,end_at,language,created_at,updated_at) VALUES (%s, %s,%s,%s,%s,%s,%s)
            """
            logger.info(f"Saving summary for folder: {folder_id}")
            results = await self.db.execute_update(query, (folder_id, summary,start_at,end_at,language, now, now))
            logger.info(f"Saved summary for {folder_id} folder")
            return results
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise
    async def query_summary(self, language: str, folder_id : str, start_at: str, end_at: str):
      
        try:
            query = f"SELECT * FROM folder_summaries WHERE folder_id = %s AND start_at = %s AND end_at = %s AND language = %s"
                        
            logger.info(f"Querying summary for folder: {folder_id} and start_at: {start_at} and end_at: {end_at}")
            results = await self.db.execute_query(query,  (folder_id,start_at,end_at,language))
            logger.info(f"Successfully queried summary for {len(results)} folder")
            return results
        except Exception as e:
            logger.error(f"Error query summary: {e}")
            raise
   