from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class FoldersRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def get_folder_ids(self, type: str = "all"):
        try:
            query = """
                SELECT id FROM folders where type = %s
            """
            results = await self.db.execute_query(query, (type,))
            return [result['id'] for result in results]
        except Exception as e:
            logger.error(f"Error getting folder count: {e}")
            raise
    async def get_folder_info(self,folder_id: int):
        """获取文件夹名称"""
        try:
            # 将passage_ids排序并转换为逗号分隔的字符串
           
            query = """
                SELECT * FROM folders WHERE id = %s
            """ 
            logger.info(f"Getting folder info for folder_id: {folder_id}")
            results = await self.db.execute_query(query, (folder_id,))
            logger.info(f"Got folder info for {folder_id}")
            return results[0]
        except Exception as e:
            logger.error(f"Error getting folder info: {e}")
            raise