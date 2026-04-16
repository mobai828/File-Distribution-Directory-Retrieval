from elasticsearch import Elasticsearch
import os

# 将您截图中的 `.cloud` 作为正确后缀进行测试
ES_ENDPOINT = os.getenv("ES_ENDPOINT")
ES_API_KEY = os.getenv("ES_API_KEY")

try:
    if not ES_ENDPOINT:
        raise ValueError("ES_ENDPOINT 未配置")
    print(f"尝试连接 ES: {ES_ENDPOINT}")
    kwargs = {"request_timeout": 10, "verify_certs": True}
    if ES_API_KEY:
        kwargs["api_key"] = ES_API_KEY

    es_client = Elasticsearch(ES_ENDPOINT, **kwargs)
    info = es_client.info()
    print("连接成功！ES 信息：")
    print(info)
except Exception as e:
    print(f"连接失败: {e}")
