import ssl
import os
from elasticsearch import Elasticsearch
from typing import Dict, Any, List

# 1. 配置 Elastic Cloud 连接凭证
# 请将这里替换为您截图中的真实信息
ES_ENDPOINT = "https://my-elasticsearch-project-b3ad93.es.asia-southeast1.gcp.elastic.cloud:443"
ES_API_KEY = "eFNVZGdaMEJCdndMUkFXVlRDRlo6YlVianBxanJGRzFJMTlQUm5abTNtQQ=="
INDEX_NAME = "archives_index"

# 实例化 ES 客户端
try:
    # 针对部分 Serverless 实例，可能需要调整 SSL 验证或显式传递 headers
    es_client = Elasticsearch(
        ES_ENDPOINT,
        api_key=ES_API_KEY,
        request_timeout=60,
        verify_certs=True # 如果本地环境有问题，可暂时设为 False，但不推荐
    )
except Exception as e:
    print(f"ES 初始化失败: {e}")
    es_client = None

class ESService:
    @staticmethod
    def get_synonyms() -> List[str]:
        """
        从配置文件读取同义词规则
        """
        synonyms_path = os.path.join(os.path.dirname(__file__), "synonyms.txt")
        synonyms_list = []
        try:
            if os.path.exists(synonyms_path):
                with open(synonyms_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            synonyms_list.append(line)
        except Exception as e:
            print(f"读取同义词配置文件失败: {e}")
            
        if not synonyms_list:
            # 默认兜底规则
            synonyms_list = [
                "学生, 学校, 校园",
                "财务, 报表, 资金, 拨款",
                "工作, 总结, 汇报"
            ]
        return synonyms_list

    @staticmethod
    def init_index(force_recreate: bool = False):
        """
        初始化索引，配置“注入规则（同义词）”和高亮分词器。
        如果索引不存在则创建。force_recreate为True时会删掉重建，以应用最新规则。
        """
        if not es_client:
            return False
            
        try:
            if force_recreate and es_client.indices.exists(index=INDEX_NAME):
                es_client.indices.delete(index=INDEX_NAME)
                print(f"已删除旧索引: {INDEX_NAME}")

            if not es_client.indices.exists(index=INDEX_NAME):
                synonyms_list = ESService.get_synonyms()
                print(f"正在应用以下同义词规则: {synonyms_list}")
                
                # 定义索引结构 (Mapping) 和 分析器 (Settings)
                index_config = {
                    "settings": {
                        "analysis": {
                            "filter": {
                                # 定义同义词规则（查询扩展）
                                "my_synonym_filter": {
                                    "type": "synonym",
                                    "synonyms": synonyms_list
                                }
                            },
                            "analyzer": {
                                # 自定义分析器：应用同义词过滤器
                                "my_analyzer": {
                                    "tokenizer": "standard", # 在中文环境通常用 ik_max_word，这里用 standard 兜底
                                    "filter": ["lowercase", "my_synonym_filter"]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "item_no": {"type": "keyword"},
                            "year": {"type": "keyword"},
                            "retention": {"type": "keyword"},
                            "file_path": {"type": "keyword"},
                            "title": {"type": "text", "analyzer": "my_analyzer"},
                            "ocr_text": {"type": "text", "analyzer": "my_analyzer"}
                        }
                    }
                }
                es_client.indices.create(index=INDEX_NAME, body=index_config)
                print(f"成功创建 ES 索引: {INDEX_NAME}")
            return True
        except Exception as e:
            print(f"创建索引失败: {e}")
            return False

    @staticmethod
    def sync_document(record: Dict[str, Any], ocr_text: str = ""):
        """
        双写机制：将 MySQL 中的元数据和识别出的 OCR 长文本同步到 ES
        """
        if not es_client:
            return False
            
        doc = {
            "item_no": record.get("item_no"),
            "year": record.get("item_no", "").split("-")[1] if "-" in record.get("item_no", "") else "",
            "retention": record.get("item_no", "").split("-")[2] if "-" in record.get("item_no", "") else "",
            "file_path": record.get("file_path"),
            "title": record.get("title", ""),
            "ocr_text": ocr_text
        }
        
        try:
            # 以档号作为 ES 的主键文档 ID，实现幂等更新（相同档号多次同步会覆盖而不是新增）
            es_client.index(index=INDEX_NAME, id=record["item_no"], document=doc)
            return True
        except Exception as e:
            print(f"同步文档到 ES 失败: {e}")
            return False

    @staticmethod
    def search_archives(keyword: str, year: str = None, retention: str = None, exact_item_no: str = None) -> List[Dict]:
        """
        核心检索方法：支持关键字全文检索、高亮、以及基于年度/保管期限的过滤。
        """
        if not es_client:
            return []
            
        # 1. 构建 Bool Query
        query_body = {
            "bool": {
                "must": [],    # 全文检索条件
                "filter": []   # 精确过滤条件
            }
        }
        
        # 处理关键字检索（在 title、ocr_text 和 item_no 中搜索）
        if keyword:
            query_body["bool"]["must"].append({
                "bool": {
                    "should": [
                        # 1. 全文检索 (支持同义词，模糊分词)
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["title^2", "ocr_text"],
                                "analyzer": "my_analyzer"
                            }
                        },
                        # 2. 短语精确匹配，权重更高
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["title^4", "ocr_text^2"],
                                "type": "phrase"
                            }
                        },
                        # 3. 档号通配符模糊匹配
                        {
                            "wildcard": {
                                "item_no": {
                                    "value": f"*{keyword}*",
                                    "case_insensitive": True,
                                    "boost": 3.0
                                }
                            }
                        }
                    ]
                }
            })
        else:
            # 如果没有关键字，就匹配所有
            query_body["bool"]["must"].append({"match_all": {}})
            
        # 处理精确过滤条件（年度、期限、档号）
        if year:
            query_body["bool"]["filter"].append({"term": {"year": year}})
        if retention:
            query_body["bool"]["filter"].append({"term": {"retention": retention}})
        if exact_item_no:
            query_body["bool"]["filter"].append({"term": {"item_no": exact_item_no}})
            
        # 2. 组装最终请求，带上高亮配置
        search_request = {
            "query": query_body,
            "highlight": {
                "pre_tags": ["<em style='color: red; font-weight: bold; background-color: yellow;'>"],
                "post_tags": ["</em>"],
                "fields": {
                    "title": {},
                    "ocr_text": {},
                    "item_no": {}
                }
            }
        }
        
        try:
            res = es_client.search(index=INDEX_NAME, body=search_request)
            hits = res["hits"]["hits"]
            
            results = []
            for hit in hits:
                source = hit["_source"]
                highlight = hit.get("highlight", {})
                
                # 如果有高亮结果，就替换掉原来的文本
                display_title = highlight.get("title", [source.get("title")])[0]
                display_ocr = highlight.get("ocr_text", [source.get("ocr_text", "")])[0]
                display_item_no = highlight.get("item_no", [source.get("item_no")])[0]
                
                results.append({
                    "item_no": display_item_no,
                    "file_path": source.get("file_path"),
                    "title": display_title,
                    "ocr_text": display_ocr,
                    "score": hit["_score"]
                })
            return results
        except Exception as e:
            print(f"ES 检索失败: {e}")
            return []