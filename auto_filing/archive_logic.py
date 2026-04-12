import os
import re
import shutil
import aiofiles
from pathlib import Path

# 配置全局绝对根目录，为了演示，存放在当前项目下的 archive_data 目录
ARCHIVE_ROOT_DIR = Path(os.path.join(os.getcwd(), "archive_data"))

# 允许上传的文件扩展名白名单，提升系统安全性
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}

class ArchiveParser:
    """
    负责解析档案元数据和计算路径
    """
    @staticmethod
    def parse_filename(filename: str) -> dict:
        """
        从文件名中提取关键维度：类别（全宗）、年度、保管期限、件号
        兼容的实际项目文件名格式例如：KJ-JJ-2017-02-001-000.jpg 或 WS-2019-D10-0001.jpg
        或者使用 '·' 或 '-' 分隔的：WS·2024·D10-0311-001.jpg
        """
        # 1. 检查扩展名是否合法（防范木马或不支持的文件格式）
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}。仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

        # 移除扩展名
        base_name = os.path.splitext(filename)[0]
        
        # 将所有的分隔符（· 或 -）统一替换为 -，以简化正则匹配
        # 注意处理 '·' (中间点)
        normalized_name = re.sub(r'[·\-]', '-', base_name)
        
        # 兼容两种格式：
        # 1. 新格式: 类别1-类别2-年度-保管期限-件号(-页码) -> 例: KJ-JJ-2017-02-001(-000)
        # 2. 原格式: 类别-年度-保管期限-件号(-页码)     -> 例: WS-2019-D10-0001(-01) 
        # (因为前面替换了分隔符，WS·2024·D10-0311-001 也变成了 WS-2024-D10-0311-001)
        
        # 首先尝试匹配新格式 (5段核心 + 可选页码)
        pattern_new = r'^([A-Za-z0-9]+-[A-Za-z0-9]+)-(\d{4})-([A-Za-z0-9]+)-(\d+)(?:-\d+)?$'
        match_new = re.match(pattern_new, normalized_name)
        
        if match_new:
            category, year, retention, item_no = match_new.groups()
            return {
                "category": category,
                "year": year,
                "retention": retention,
                "item_no": item_no,
                "original_base": base_name # 保留原始文件名用于记录
            }
            
        # 再尝试匹配原格式 (4段核心 + 可选页码)
        pattern_old = r'^([A-Za-z0-9]+)-(\d{4})-([A-Za-z0-9]+)-(\d+)(?:-\d+)?$'
        match_old = re.match(pattern_old, normalized_name)
        
        if match_old:
            category, year, retention, item_no = match_old.groups()
            return {
                "category": category,
                "year": year,
                "retention": retention,
                "item_no": item_no,
                "original_base": base_name
            }
            
        raise ValueError(f"文件名格式不符合规范: {filename}，期望格式如 KJ-JJ-2017-02-001.jpg 或 WS·2024·D10-0311-001.jpg")

    @staticmethod
    def calculate_relative_path(metadata: dict) -> str:
        """
        将提取出的维度数据拼装成标准化的 4 级/5 级目录结构
        例如：/WS/2019/D10/0001
        """
        path_parts = [
            metadata["category"],
            metadata["year"],
            metadata["retention"],
            metadata["item_no"]
        ]
        # 使用正斜杠拼接相对路径，保持跨平台一致性（数据库中存储的相对路径）
        return "/" + "/".join(path_parts)


class FileStorage:
    """
    负责物理文件的存储操作
    """
    @staticmethod
    async def save_file_async(relative_path: str, filename: str, file_content: bytes) -> str:
        """
        异步方式落盘：防止在并发上传大文件时阻塞 FastAPI 主线程。
        """
        # 1. 组装绝对路径
        clean_rel_path = relative_path.lstrip('/')
        target_dir = ARCHIVE_ROOT_DIR / Path(clean_rel_path)
        
        # 2. 动态建树
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. 文件就位
        target_file_path = target_dir / filename
        
        # 4. 使用 aiofiles 进行异步非阻塞写入
        async with aiofiles.open(target_file_path, "wb") as f:
            await f.write(file_content)
            
        return str(target_file_path)

    @staticmethod
    def delete_file(absolute_path: str):
        """
        发生回写失败等异常时，清理“孤儿文件”
        """
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
