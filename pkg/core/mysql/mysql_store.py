import logging
from typing import Optional, List, Dict, Any
import aiomysql
from pkg.core.mysql.mysql_config import MySQLConfig
from pkg.core.context.context_vars import get_trace_id
import asyncio

logger = logging.getLogger(__name__)

class MySQLStore:
    _instances = {}
    _pool_lock = asyncio.Lock()

    def __new__(cls, source_name: str = 'default'):
        if source_name not in cls._instances:
            cls._instances[source_name] = super().__new__(cls)
        return cls._instances[source_name]

    def __init__(self, source_name: str = 'default'):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.source_name = source_name
            self.config = MySQLConfig(source_name)
            self.pool: Optional[aiomysql.Pool] = None
            self._creating_pool = False

    async def get_pool(self) -> aiomysql.Pool:
        """获取数据库连接池，使用锁防止并发创建多个连接池"""
        try:
            if self.pool is None or self.pool._closed:
                async with self._pool_lock:
                    # Double check after acquiring lock
                    if self.pool is None or self.pool._closed:
                        logger.info(f"Creating new connection pool for {self.source_name}")
                        self.pool = await aiomysql.create_pool(
                            host=self.config.host,
                            port=self.config.port,
                            user=self.config.user,
                            password=self.config.password,
                            db=self.config.database,
                            charset=self.config.charset,
                            autocommit=True,
                            maxsize=self.config.pool_size,
                            minsize=1,
                            pool_recycle=3600  # 每小时回收连接
                        )
                        logger.info(f"Connection pool created successfully for {self.source_name}")
            return self.pool
        except Exception as e:
            logger.error(f"Error getting connection pool: {e}")
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
                self.pool = None
            raise

    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行异步查询"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                pool = await self.get_pool()
                trace_id = get_trace_id()
                
                if params:
                    actual_sql = query
                    for param in params:
                        actual_sql = actual_sql.replace('%s', repr(param), 1)
                    logger.debug(f"Executing SQL: {actual_sql} trace_id: {trace_id}")
                else:
                    logger.debug(f"Executing SQL: {query} trace_id: {trace_id}")
                
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(query, params)
                        results = await cursor.fetchall()
                        logger.debug(f"Query returned {len(results)} rows")
                        return results
                        
            except (aiomysql.OperationalError, aiomysql.InternalError) as e:
                retry_count += 1
                logger.warning(f"Database error occurred (attempt {retry_count}/{max_retries}): {e}")
                
                if self.pool:
                    self.pool.close()
                    await self.pool.wait_closed()
                    self.pool = None
                
                if retry_count < max_retries:
                    await asyncio.sleep(1)  # 等待1秒后重试
                else:
                    logger.error("Max retries reached, raising error")
                    raise
                    
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                raise

    async def execute_update(self, query: str, params: tuple = None) -> int:
        """执行异步更新操作"""
        pool = await self.get_pool()
        try:
            trace_id = get_trace_id()
            if params:
                actual_sql = query
                for param in params:
                    actual_sql = actual_sql.replace('%s', repr(param), 1)
                logger.debug(f"Executing SQL: {actual_sql} trace_id: {trace_id}")
            else:
                logger.debug(f"Executing SQL: {query} trace_id: {trace_id}")
            
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    affected_rows = await cursor.execute(query, params)
                    await conn.commit()
                    logger.debug(f"Update affected {affected_rows} rows")
                    return affected_rows
        except Exception as e:
            logger.error(f"Error executing update: {e}")
            raise

    async def get_table_count(self, table_name: str) -> int:
        """异步获取表的记录数"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = await self.execute_query(query)
        return result[0]['count']

    async def close(self):
        """关闭连接池"""
        if self.pool is not None:
            logger.info(f"Closing connection pool for {self.source_name}")
            try:
                self.pool.close()
                await self.pool.wait_closed()
                self.pool = None
                logger.info(f"Connection pool closed successfully for {self.source_name}")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
                raise

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


def main():
    try:
        # 创建 MySQL 和 ChromaDB 存储实例
        mysql_store = MySQLStore()
        mysql_store.__init__()
        # chroma_store = ChromaDBStore("test_collection")
        # chroma_store.__init__()

        while True:
            # 从 MySQL 读取 passages 内容
            # query = 'SELECT id,embedding, pure_content FROM passages WHERE (embedding IS NULL OR embedding!= 1) and pure_content!="" and pure_content is not null limit 100'
            query = 'SELECT id, embedding, pure_content FROM passages limit 100'
            results = mysql_store.execute_query(query)
            print(query)
            if not results:
                print("\nNo more passages to process")
                break

            # 准备数据
            contents = []
            ids = []
            metadatas = []
            
            for row in results:
                contents.append(row['pure_content'])
                ids.append(str(row['id']))
                metadatas.append({"source": "mysql_passages"})
                
            # 批量添加到 ChromaDB
            if contents:
                # ids = chroma_store.add_contents(
                #     contents=contents,
                #     ids=ids,
                #     metadatas=metadatas
                # )
                # print(ids)
                # print(f"\nSuccessfully added {len(contents)} passages to ChromaDB")
                
                # 更新 passages 的 embedding 字段为 1
                update_query = "UPDATE passages SET embedding = 1 WHERE id IN (%s)" % ",".join(ids)
                print(update_query)
                # mysql_store.execute_query(update_query)
                # mysql_store.connection.commit()  # 添加这行来提交事务

                print("Successfully updated embedding status")
            else:
                print("\nNo passages found to add")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if mysql_store.connection:
            mysql_store.connection.close()
if __name__ == '__main__':
    main()