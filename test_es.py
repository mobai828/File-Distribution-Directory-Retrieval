from elasticsearch import Elasticsearch

# 将您截图中的 `.cloud` 作为正确后缀进行测试
ES_ENDPOINT = "https://my-elasticsearch-project-b3ad93.es.asia-southeast1.gcp.elastic.cloud:443"
ES_API_KEY = "eFNVZGdaMEJCdndMUkFXVlRDRlo6YlVianBxanJGRzFJMTlQUm5abTNtQQ=="

try:
    print(f"尝试连接 ES: {ES_ENDPOINT}")
    es_client = Elasticsearch(
        ES_ENDPOINT,
        api_key=ES_API_KEY,
        request_timeout=10,
        verify_certs=True
    )
    info = es_client.info()
    print("连接成功！ES 信息：")
    print(info)
except Exception as e:
    print(f"连接失败: {e}")
