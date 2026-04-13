import sys
import os
sys.path.append("/workspace")

from search_engine.es_service import ESService

def main():
    print("=== 测试 1: 从 synonyms.txt 初始化并重建索引 ===")
    ESService.init_index(force_recreate=True)
    
    print("\n=== 测试 2: 同步测试文档 ===")
    test_docs = [
        {
            "item_no": "WS-2024-D10-001",
            "file_path": "/WS/2024/D10/001",
            "title": "关于优秀学生表彰的决定",
            "status": "已挂接"
        },
        {
            "item_no": "WS-2024-D10-002",
            "file_path": "/WS/2024/D10/002",
            "title": "2024年度项目预算与拨款通知",
            "status": "已挂接"
        },
        {
            "item_no": "WS-2024-D30-003",
            "file_path": "/WS/2024/D30/003",
            "title": "校园安全工作计划",
            "status": "已挂接"
        }
    ]
    
    for doc in test_docs:
        ocr_text = "这是一份测试用的正文内容。这里可能包含一些关键词。"
        ESService.sync_document(doc, ocr_text)
        print(f"已同步文档: {doc['title']} ({doc['item_no']})")
        
    print("\n=== 测试 3: 检索规则测试 (等待1秒让ES刷新索引) ===")
    import time
    time.sleep(1.5)
    
    print("\n-- 搜索 '学校' (测试同义词规则: 学生, 学校, 校园, 班级) --")
    res1 = ESService.search_archives(keyword="学校")
    for r in res1:
        print(f"找到: {r['title']} (相关度: {r['score']})")
        
    print("\n-- 搜索 '财务' (测试同义词规则: 财务, 报表, 资金, 拨款, 预算) --")
    res2 = ESService.search_archives(keyword="财务")
    for r in res2:
        print(f"找到: {r['title']} (相关度: {r['score']})")

    print("\n-- 测试精确过滤档号: 'WS-2024-D10-001' --")
    res3 = ESService.search_archives(keyword="", exact_item_no="WS-2024-D10-001")
    for r in res3:
        print(f"找到: {r['title']} (档号: {r['item_no']})")

if __name__ == "__main__":
    main()
