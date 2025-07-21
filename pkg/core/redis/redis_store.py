import redis
import unittest

class RedisStore:
    def __init__(self, host='47.116.173.33', port=6379, db=0, password='Wv0ghh4KnDSshj7K'):
        self.client = redis.StrictRedis(host=host, port=port, db=db, password=password)

    def set_value(self, key: str, value: str):
        """设置键值对"""
        self.client.set(key, value)

    def get_value(self, key: str) -> str:
        """获取键的值"""
        return self.client.get(key)

# 测试类
class TestRedisStore(unittest.TestCase):
    def setUp(self):
        self.store = RedisStore()

    def test_set_and_get_value(self):
        self.store.set_value('test_key', 'test_value')
        value = self.store.get_value('test_key')
        self.assertEqual(value.decode('utf-8'), 'test_value')  # 解码字节为字符串

if __name__ == '__main__':
    unittest.main()  # 运行测试