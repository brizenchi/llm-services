from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class PassageSummariesRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def save_summary(self, passage_ids: List[int], summary: str):
        """保存摘要"""
        try:
            # 将passage_ids排序并转换为逗号分隔的字符串
            sorted_ids = sorted(passage_ids)
            ids_str = '_'.join(str(id) for id in sorted_ids)
            
            query = """
                UPDATE passages SET summary = %s WHERE id = (%s)
            """
            logger.info(f"Saving summary for passage_ids: {ids_str}")
            results = await self.db.execute_update(query, (summary, ids_str))
            logger.info(f"Saved summary for {len(passage_ids)} passages")
            return results
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise
    async def query_summary(self, passage_ids: List[int]):
        
        try:
            # 构建批量更新的SQL
            placeholders = '_'.join(['%s'] * len(passage_ids))
            query = f"SELECT * FROM passage_summaries WHERE passage_ids = %s"
            
            # 构建参数列表，第一个是status，后面是所有的passage_ids
            params = passage_ids
            
            logger.info(f"Querying summary for passage_ids: {passage_ids}")
            results = await self.db.execute_query(query, tuple(params))
            logger.info(f"Successfully queried summary for {len(passage_ids)} passages")
            return results
        except Exception as e:
            logger.error(f"Error query summary: {e}")
            raise
   