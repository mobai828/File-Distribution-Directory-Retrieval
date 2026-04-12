import json
import os

DB_FILE = "database.json"

class MockDatabase:
    """
    模拟数据库，用于演示自动分件与路径回写的数据处理。
    加入了 JSON 文件持久化存储，防止服务重启后数据丢失。
    """
    def __init__(self):
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.records = data.get("records", [])
                self.next_id = data.get("next_id", 7)
        else:
            # 初始的数据库条目，假设是待上传扫描件的空记录
            self.records = [
                {"id": 1, "item_no": "KJ-JJ-2017-02-001", "status": "未挂接", "file_path": None, "title": "2017年科技基金项目书 (多页测试)"},
                {"id": 2, "item_no": "WS-2024-D10-0311", "status": "未挂接", "file_path": None, "title": "2024年工作报告 (点分隔测试)"},
                {"id": 3, "item_no": "WS-2024-D30-0156", "status": "未挂接", "file_path": None, "title": "2024年会议纪要 (点分隔测试)"},
                {"id": 4, "item_no": "WS-2024-D10-0313", "status": "未挂接", "file_path": None, "title": "2024年项目申报书 (自动新增)"},
                {"id": 5, "item_no": "HR-2020-Y10-0023", "status": "未挂接", "file_path": None, "title": "2020年人事任命书"},
                {"id": 6, "item_no": "FIN-2021-Y30-0112", "status": "未挂接", "file_path": None, "title": "2021年年度财务报表"}
            ]
            self.next_id = 7
            self._save()

    def _save(self):
        """将内存中的数据持久化保存到本地 JSON 文件中"""
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "next_id": self.next_id,
                "records": self.records
            }, f, ensure_ascii=False, indent=4)

    def find_record_by_item_no(self, item_no: str) -> dict:
        """
        根据档号查找对应的数据库记录
        例如：传入 WS-2019-D10-0001
        """
        for record in self.records:
            if record["item_no"] == item_no:
                return record
        return None

    def create_record(self, item_no: str, title: str = "自动创建档案") -> dict:
        """
        当数据库中找不到对应档号时，自动创建一条新的记录
        """
        new_record = {
            "id": self.next_id,
            "item_no": item_no,
            "status": "未挂接",
            "file_path": None,
            "title": title
        }
        self.records.append(new_record)
        self.next_id += 1
        self._save()
        return new_record

    def update_record_path(self, record_id: int, relative_path: str):
        """
        执行回写：系统向数据库发出更新指令，将相对路径永久写入该件档案的属性中。
        """
        # 模拟可能发生的数据库异常
        if "ERROR" in relative_path:
            raise Exception("数据库更新失败：模拟网络异常或事务冲突")

        for record in self.records:
            if record["id"] == record_id:
                record["file_path"] = relative_path
                record["status"] = "已数字化/可查阅"
                self._save()
                return True
        return False

    def sync_records_with_disk(self, root_dir_path):
        """
        全量同步：检查数据库中每一条已挂接的记录，其对应的物理文件夹是否还存在。
        如果物理文件夹被删除（例如用户手动删除了 archive_data），则重置状态为“未挂接”。
        """
        import os
        from pathlib import Path
        
        changed = False
        for record in self.records:
            if record["status"] != "未挂接" and record["file_path"]:
                # 去掉开头的斜杠以进行拼接
                clean_rel_path = record["file_path"].lstrip('/')
                absolute_dir = Path(root_dir_path) / clean_rel_path
                
                # 如果目录不存在，或者目录里面是空的（没有任何文件）
                if not absolute_dir.exists() or not any(absolute_dir.iterdir()):
                    record["status"] = "未挂接"
                    record["file_path"] = None
                    changed = True
                    
        if changed:
            self._save()
            
        return self.records

# 实例化全局单例数据库对象
db = MockDatabase()
