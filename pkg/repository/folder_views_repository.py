from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class FolderViewsRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_viewpoint(self, language: str, folder_id: str, viewpoint: str,start_at: str, end_at: str):
        """保存摘要"""
        try:
            # 将passage_ids排序并转换为逗号分隔的字符串
           
            query = """
                INSERT INTO folder_views (folder_id, viewpoint, start_at,end_at,language) VALUES (%s, %s,%s,%s,%s)
            """
            logger.info(f"Saving summary for folder: {folder_id}")
            results = await self.db.execute_update(query, (folder_id, viewpoint,start_at,end_at,language))
            logger.info(f"Saved summary for {folder_id} folder")
            return results
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise
    async def query_viewpoint(self, language: str, folder_id : str, start_at: str, end_at: str):
      
        try:
            query = f"SELECT * FROM folder_views WHERE folder_id = %s AND start_at = %s AND end_at = %s AND language = %s"
                        
            logger.info(f"Querying viewpoint for folder: {folder_id} and start_at: {start_at} and end_at: {end_at}")
            results = await self.db.execute_query(query,  (folder_id,start_at,end_at,language))
            logger.info(f"Successfully queried viewpoint for {len(results)} folder")
            return results
        except Exception as e:
            logger.error(f"Error query viewpoint: {e}")
            raise
   