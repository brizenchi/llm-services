from typing import List, Dict, Any
from pkg.core.mysql.mysql_factory import MySQLFactory
import logging

logger = logging.getLogger(__name__)

class PassageRepository:
    def __init__(self, source_name: str = "default"):
        self.db = MySQLFactory.get_instance(source_name)
    
    async def fetch_unprocessed_passages(self, limit: int = 100):
        """获取未处理的文章"""
        try:
            query = """
                SELECT id, title, content, created_at 
                FROM passages 
                WHERE (embedding IS NULL OR embedding != 1) 
                LIMIT %s
            """
            logger.info(f"Fetching unprocessed passages with limit {limit}")
            results = await self.db.execute_query(query, (limit,))
            logger.info(f"Found {len(results)} unprocessed passages")
            return results
        except Exception as e:
            logger.error(f"Error fetching unprocessed passages: {e}")
            raise
    
    async def update_embedding_status(self, passage_ids: List[int], status: int = 1):
        """批量更新文章的嵌入状态
        
        Args:
            passage_ids: 文章ID列表
            status: 嵌入状态，默认为1（成功）
        """
        try:
            # 构建批量更新的SQL
            placeholders = ','.join(['%s'] * len(passage_ids))
            query = f"UPDATE passages SET embedding = %s WHERE id IN ({placeholders})"
            
            # 构建参数列表，第一个是status，后面是所有的passage_ids
            params = [status] + passage_ids
            
            logger.info(f"Batch updating embedding status for {len(passage_ids)} passages to {status}")
            await self.db.execute_update(query, tuple(params))
            logger.info(f"Successfully updated embedding status for {len(passage_ids)} passages")
        except Exception as e:
            logger.error(f"Error batch updating embedding status: {e}")
            raise
    async def fetch_unsummaried_passages(self, folder_id: int, limit: int = 100,date: str = "2025-03-01"):
        """获取未处理的新闻"""
        interval_hour = 8
        try:
            # 第一步：获取文件夹下的所有feed_id
            feed_query = """
            SELECT feed_id 
            FROM feed_folders
            WHERE folder_id = %s
            """
            feed_results = await self.db.execute_query(feed_query, (folder_id,))
            
            if not feed_results:
                logger.info(f"No feeds found for folder_id {folder_id}")
                return []
                
            # 提取所有feed_id
            feed_ids = [result['feed_id'] for result in feed_results]
            feed_placeholders = ','.join(['%s'] * len(feed_ids))
            
            # 第二步：根据feed_ids获取文章
            passage_query = f"""
            SELECT p.id, p.title, p.description, p.content, p.created_at, p.published,p.summary
            FROM passages p
            Left join feeds f
            on f.id=p.feed_id
            WHERE p.feed_id IN ({feed_placeholders})
            AND p.published BETWEEN 
                CAST(%s - INTERVAL 1 DAY AS DATETIME) + INTERVAL %s HOUR 
                AND 
                CAST(%s AS DATETIME) + INTERVAL %s HOUR
            AND (p.summary IS NULL OR p.summary = '')
            ORDER BY p.published DESC
            LIMIT %s
            """
            
            # 构建参数列表：feed_ids + interval_hour + interval_hour + limit
            params = feed_ids + [date, interval_hour, date, interval_hour, limit]
            results = await self.db.execute_query(passage_query, tuple(params))
            
            logger.info(f"Found {len(results)} subscribed passages")
            return results
        except Exception as e:
            logger.error(f"Error fetching subscribed passages: {e}")
            raise

    async def fetch_passages_by_date(self, folder_id: int, limit: int = 100,date: str = "2025-03-01"):
        """获取未处理的新闻"""
        interval_hour = 8
        try:
            # 第一步：获取文件夹下的所有feed_id
            feed_query = """
            SELECT feed_id 
            FROM feed_folders
            WHERE folder_id = %s
            """
            feed_results = await self.db.execute_query(feed_query, (folder_id,))
            
            if not feed_results:
                logger.info(f"No feeds found for folder_id {folder_id}")
                return []
                
            # 提取所有feed_id
            feed_ids = [result['feed_id'] for result in feed_results]
            feed_placeholders = ','.join(['%s'] * len(feed_ids))
            
            # 第二步：根据feed_ids获取文章
            passage_query = f"""
            SELECT p.id, p.title, p.description, p.created_at, p.published, p.link, p.image_url, f.cover_image feed_cover_image,f.link as feed_homepage,f.title as feed_title
            FROM passages p
            Left join feeds f
            on f.id=p.feed_id
            WHERE p.feed_id IN ({feed_placeholders})
            AND p.published BETWEEN 
                CAST(%s - INTERVAL 1 DAY AS DATETIME) + INTERVAL %s HOUR 
                AND 
                CAST(%s AS DATETIME) + INTERVAL %s HOUR
            ORDER BY p.published DESC
            LIMIT %s
            """
            
            # 构建参数列表：feed_ids + interval_hour + interval_hour + limit
            params = feed_ids + [date, interval_hour, date, interval_hour, limit]
            results = await self.db.execute_query(passage_query, tuple(params))
            
            logger.info(f"Found {len(results)} subscribed passages")
            return results
        except Exception as e:
            logger.error(f"Error fetching subscribed passages: {e}")
            raise