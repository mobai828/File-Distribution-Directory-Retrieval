from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import shutil
from auto_filing.archive_logic import ArchiveParser, FileStorage, ARCHIVE_ROOT_DIR
from auto_filing.database import db
from search_engine.es_service import ESService

app = FastAPI(title="自动分件与全文检索系统")

# 确保全局根目录存在
ARCHIVE_ROOT_DIR.mkdir(parents=True, exist_ok=True)

# 启动时初始化 ES 索引
@app.on_event("startup")
async def startup_event():
    ESService.init_index()
    # 模拟把现有的数据库记录同步到 ES
    for record in db.records:
        # 将已挂接状态和未挂接状态的都同步进去，保证有数据可查
        mock_ocr = f"这是一份自动生成的 OCR 文本。档案题名为：{record['title']}。"
        if "财务" in record["title"]:
            mock_ocr += " 包含公司年度资金预算与教育拨款等关键信息。"
        elif "项目" in record["title"] or "工作" in record["title"]:
            mock_ocr += " 涉及大量学校、学生的科研工作总结。"
        ESService.sync_document(record, mock_ocr)

# 挂载静态目录，用于演示全文检索的“秒级开箱”
# 路径是前面回写的相对路径的开头
app.mount("/static_archive", StaticFiles(directory=str(ARCHIVE_ROOT_DIR)), name="archive")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "records": db.records})

@app.get("/api/search")
async def search_api(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    year: Optional[str] = Query(None, description="过滤年度"),
    retention: Optional[str] = Query(None, description="过滤保管期限"),
    exact_item_no: Optional[str] = Query(None, description="精确过滤档号")
):
    """
    全文检索接口，接收前端参数，转交 ES 服务处理
    """
    results = ESService.search_archives(keyword=keyword, year=year, retention=retention, exact_item_no=exact_item_no)
    return {"data": results}
@app.get("/api/records")
async def get_records():
    # 每次获取列表时，实时同步一次硬盘文件状态，保证页面上看到的是真实的“账物相符”
    records = db.sync_records_with_disk(ARCHIVE_ROOT_DIR)
    return {"data": records}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    支持多个文件同时上传
    遍历每个文件执行：触发与解析 -> 规则引擎推演 -> 物理落盘 -> 数据回写与状态流转
    """
    results = []
    
    for file in files:
        filename = file.filename
        absolute_file_path = ""
        
        try:
            # 1. 解析文件名
            try:
                metadata = ArchiveParser.parse_filename(filename)
            except ValueError as e:
                raise Exception(str(e))
                
            # 拼装出完整的档号用于数据库匹配，例如：WS-2019-D10-0001
            item_no_full = f"{metadata['category']}-{metadata['year']}-{metadata['retention']}-{metadata['item_no']}"
            
            # 查找数据库中是否存在这条未挂接记录
            record = db.find_record_by_item_no(item_no_full)
            if not record:
                # 如果数据库中没有该档号，系统可以自动创建一条新记录，这叫“以物建账”
                record = db.create_record(item_no_full, f"新上传档案 ({item_no_full})")
                
            # 2. 规则引擎推演：计算相对路径
            relative_path = ArchiveParser.calculate_relative_path(metadata)
            
            # 如果档案已被数字化，我们仍然允许它落盘，但不再重复更新数据库（认为是追加页码）
            is_new_link = (record["status"] == "未挂接")
            
            # 3. 物理落盘
            file_content = await file.read()
            try:
                # 采用异步 I/O 进行文件写入，防止大批量文件上传时拖垮服务器性能
                absolute_file_path = await FileStorage.save_file_async(relative_path, filename, file_content)
            except Exception as e:
                raise Exception(f"文件落盘失败：{str(e)}")
                
            # 4. 数据回写与状态流转（事务处理）
            if is_new_link:
                try:
                    # 执行回写：系统向数据库发出更新指令，将相对路径永久写入该件档案的属性中
                    if "ERROR" in filename:
                        db.update_record_path(record["id"], relative_path + "-ERROR")
                    else:
                        db.update_record_path(record["id"], relative_path)
                        
                except Exception as e:
                    # 发生异常，数据库事务回滚
                    FileStorage.delete_file(absolute_file_path)
                    raise Exception(f"回写数据库失败，已清理落盘文件。错误详情：{str(e)}")

                # 在此处增加：双写到 Elasticsearch 以便建立全文索引
                # 这里为了演示，我们给它生成一段模拟的 OCR 文本
                mock_ocr_text = f"这是在文件 {filename} 上传时通过 OCR 自动识别出来的正文内容。其中包含：年度{metadata['year']}，以及可能提到学生、学校、拨款、财务等关键词。"
                ESService.sync_document(record, mock_ocr_text)

                results.append({
                    "filename": filename,
                    "status": "success",
                    "message": f"文件 {filename} 自动分件与路径回写成功！",
                    "relative_path": relative_path,
                    "record_updated": True
                })
            else:
                # 已经是已挂接状态，说明这是同一件档案的其他页，直接追加落盘即可，无需重复回写数据库
                results.append({
                    "filename": filename,
                    "status": "success",
                    "message": f"文件 {filename} 追加归档成功（数据库路径已存在）。",
                    "relative_path": relative_path,
                    "record_updated": False
                })
            
        except Exception as e:
            results.append({
                "filename": filename,
                "status": "error",
                "detail": str(e)
            })

    return {"results": results}
