"""
AI-Sheet-Pro 后端服务
FastAPI + DuckDB + AI 代理（增强版）
"""

import os
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Optional, List
import tempfile

from db_engine import get_engine, DataEngine
from ai_agent import get_agent, reload_agent, AIAgent
from sandbox import get_sandbox
from logger import get_logger


app = FastAPI(
    title="AI-Sheet-Pro Backend",
    description="AI 驱动的表格处理服务",
    version="2.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 临时文件目录
TEMP_DIR = Path(__file__).parent / 'temp'
TEMP_DIR.mkdir(exist_ok=True)


# =============== 日志 API ===============

@app.get("/api/logs")
async def get_system_logs(since_id: Optional[str] = None):
    """获取系统日志"""
    return {
        "success": True,
        "data": get_logger().get_logs(since_id)
    }


# =============== UI 命令 API ===============

from ui_commands import get_ui_queue

@app.get("/api/ui/pending")
async def get_pending_ui_commands():
    """获取待执行的 UI 命令（前端轮询）"""
    commands = get_ui_queue().get_pending()
    return {
        "success": True,
        "commands": commands
    }

@app.get("/api/ui/history")
async def get_ui_command_history(limit: int = 20):
    """获取 UI 命令执行历史"""
    history = get_ui_queue().get_history(limit)
    return {
        "success": True,
        "history": history
    }

# =======================================


# =============== 数据模型 ===============

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class QueryRequest(BaseModel):
    query: str


class SQLRequest(BaseModel):
    sql: str


class ViewRequest(BaseModel):
    table_name: str
    offset: int = 0
    limit: int = 100


class SemanticMappingRequest(BaseModel):
    table_a: str
    table_b: str


# =============== 基础 API ===============

@app.get("/api/health")
async def health_check():
    engine = get_engine()
    return {
        "status": "ok",
        "service": "AI-Sheet-Pro Backend",
        "version": "2.1.0",
        "tables_loaded": len(engine.get_all_tables()),
        "tables": engine.get_all_tables()
    }


@app.get("/api/tables", response_model=APIResponse)
async def list_tables():
    engine = get_engine()
    tables = engine.get_all_tables()
    table_info = engine.get_table_info()
    return APIResponse(
        success=True,
        message=f"共 {len(tables)} 个表",
        data=table_info
    )


# =============== 多表导入 API ===============

@app.post("/api/upload", response_model=APIResponse)
async def upload_file(
    file: UploadFile = File(...),
    table_name: Optional[str] = Form(None)
):
    """上传文件并指定表名"""
    engine = get_engine()
    
    try:
        filename = file.filename.lower()
        if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
            return APIResponse(success=False, message="仅支持 Excel (.xlsx, .xls) 和 CSV 文件")
        
        temp_path = TEMP_DIR / file.filename
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        if filename.endswith('.csv'):
            result = engine.load_csv(str(temp_path), table_name)
        else:
            result = engine.load_excel(str(temp_path), table_name)
        
        use_shadow = result['rows'] > engine.SHADOW_THRESHOLD
        
        return APIResponse(
            success=True,
            message=f"文件加载成功：{result['table_name']}，共 {result['rows']} 行 {result['columns']} 列",
            data={**result, 'use_shadow_mode': use_shadow}
        )
        
    except Exception as e:
        return APIResponse(success=False, message=f"上传失败: {str(e)}")


@app.post("/api/upload/table-a", response_model=APIResponse)
async def upload_table_a(file: UploadFile = File(...)):
    """专用：导入 A 表"""
    engine = get_engine()
    
    try:
        filename = file.filename.lower()
        temp_path = TEMP_DIR / file.filename
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        if filename.endswith('.csv'):
            result = engine.load_csv(str(temp_path), 'table_a')
        else:
            result = engine.load_excel(str(temp_path), 'table_a')
        
        return APIResponse(success=True, message=f"A 表导入成功，共 {result['rows']} 行", data=result)
    except Exception as e:
        return APIResponse(success=False, message=f"A 表导入失败: {str(e)}")


@app.post("/api/upload/table-b", response_model=APIResponse)
async def upload_table_b(file: UploadFile = File(...)):
    """专用：导入 B 表"""
    engine = get_engine()
    
    try:
        filename = file.filename.lower()
        temp_path = TEMP_DIR / file.filename
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        if filename.endswith('.csv'):
            result = engine.load_csv(str(temp_path), 'table_b')
        else:
            result = engine.load_excel(str(temp_path), 'table_b')
        
        return APIResponse(success=True, message=f"B 表导入成功，共 {result['rows']} 行", data=result)
    except Exception as e:
        return APIResponse(success=False, message=f"B 表导入失败: {str(e)}")


# =============== 语义映射 API ===============

@app.post("/api/semantic/mapping", response_model=APIResponse)
async def find_semantic_mapping(request: SemanticMappingRequest):
    """识别两个表之间的语义映射（同义异名列）"""
    agent = get_agent()
    
    try:
        result = agent.find_semantic_mappings(request.table_a, request.table_b)
        
        if 'error' in result:
            return APIResponse(success=False, message=result['error'])
        
        return APIResponse(
            success=True,
            message=f"找到 {len(result.get('mappings', []))} 个语义映射",
            data=result
        )
    except Exception as e:
        return APIResponse(success=False, message=f"语义映射失败: {str(e)}")


@app.get("/api/semantic/auto-detect", response_model=APIResponse)
async def auto_detect_mapping():
    """自动检测已加载表的语义映射"""
    engine = get_engine()
    agent = get_agent()
    
    tables = engine.get_all_tables()
    if len(tables) < 2:
        return APIResponse(success=False, message="需要至少两个表才能进行语义映射")
    
    # 使用前两个表
    result = agent.find_semantic_mappings(tables[0], tables[1])
    return APIResponse(
        success=True,
        message=f"自动检测 {tables[0]} 和 {tables[1]} 的映射",
        data=result
    )


# =============== 删除表格 API ===============

@app.delete("/api/table/{table_name}", response_model=APIResponse)
async def delete_table(table_name: str):
    """删除指定表格"""
    engine = get_engine()
    
    try:
        # 1. 检查是否存在（内存字典）
        if table_name not in engine.tables:
            # 尝试从数据库直接检查，防止字典不同步
            pass 
        
        # 2. 从 DuckDB 获取对象类型 (BASE TABLE 或 VIEW)
        # DuckDB 的 information_schema 是标准的
        res = engine.conn.execute(
            "SELECT table_type FROM information_schema.tables WHERE table_name = ?", 
            [table_name]
        ).fetchone()
        
        if res:
            table_type = res[0] # 'BASE TABLE' or 'VIEW'
            if table_type == 'VIEW':
                engine.conn.execute(f'DROP VIEW IF EXISTS "{table_name}"')
            else:
                engine.conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        else:
            # 如果元数据里没有，尝试盲删（防御性）
            try:
                engine.conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            except:
                engine.conn.execute(f'DROP VIEW IF EXISTS "{table_name}"')

        # 3. 从内部字典删除
        if table_name in engine.tables:
            del engine.tables[table_name]
        
        return APIResponse(
            success=True,
            message=f"表 '{table_name}' 已删除",
            data={"deleted_table": table_name}
        )
    except Exception as e:
        import traceback
        traceback.print_exc() # 在服务端打印堆栈以便调试
        return APIResponse(success=False, message=f"删除失败: {str(e)}")


# =============== 导出表格 API ===============

@app.get("/api/export/{table_name}")
async def export_table(table_name: str):
    """导出表格为 Excel 文件"""
    engine = get_engine()
    
    try:
        # 创建临时文件
        temp_dir = Path(tempfile.gettempdir())
        output_filename = f"{table_name}_export.xlsx"
        output_path = temp_dir / output_filename
        
        # 导出
        engine.export_table_as_excel(table_name, str(output_path))
        
        # 返回文件
        return FileResponse(
            path=output_path, 
            filename=output_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============== 撤回 API ===============

from undo_manager import get_undo_manager

@app.post("/api/undo", response_model=APIResponse)
async def undo_last_operation():
    """撤回上一次的 AI 操作"""
    manager = get_undo_manager()
    result = manager.undo()
    return APIResponse(
        success=result['success'],
        message=result['message'],
        data=result.get('restored_tables')
    )


# =============== AI 查询 API（带预览确认） ===============

@app.post("/api/ai/preview", response_model=APIResponse)
async def ai_preview(request: QueryRequest):
    """AI 查询预览（不执行，返回待确认信息）"""
    agent = get_agent()
    
    try:
        if not request.query.strip():
            return APIResponse(success=False, message="查询内容为空")
        
        result = agent.preview_query(request.query)
        
        return APIResponse(
            success=True,
            message="请确认以下操作",
            data={
                'query': result['query'],
                'generated_code': result['generated_code'],
                'explanation': result['explanation'],
                'llm_used': result.get('llm_used', False),
                'requires_confirmation': True
            }
        )
    except Exception as e:
        return APIResponse(success=False, message=f"预览失败: {str(e)}")


@app.post("/api/ai/confirm", response_model=APIResponse)
async def ai_confirm():
    """确认并执行预览的 AI 操作"""
    agent = get_agent()
    
    try:
        result = agent.confirm_and_execute()
        
        if result['success']:
            return APIResponse(
                success=True,
                message="执行成功",
                data={
                    'query': result['query'],
                    'generated_code': result['generated_code'],
                    'explanation': result['explanation'],
                    'result': result['execution_result']['result']
                }
            )
        else:
            return APIResponse(
                success=False,
                message=f"执行失败: {result.get('error', result['execution_result'].get('error', '未知错误'))}",
                data=result
            )
    except Exception as e:
        return APIResponse(success=False, message=f"确认执行失败: {str(e)}")


@app.post("/api/ai/query", response_model=APIResponse)
async def ai_query(request: QueryRequest):
    """直接执行 AI 查询（跳过确认）"""
    agent = get_agent()
    
    try:
        if not request.query.strip():
            return APIResponse(success=False, message="查询内容为空")
        
        result = agent.execute_query(request.query)
        
        if result['success']:
            return APIResponse(
                success=True,
                message="查询成功",
                data={
                    'query': result['query'],
                    'generated_code': result['generated_code'],
                    'explanation': result.get('explanation', ''),
                    'result': result['execution_result']['result'],
                    'llm_used': result.get('llm_used', False),
                    # 🆕 新增字段：AI 响应分类
                    'response_type': result.get('response_type', 'answer'),
                    'answer': result.get('answer', result.get('explanation', '')),
                    'temp_table': result.get('temp_table') # 🆕 传递 temp_table
                }
            )
        else:
            return APIResponse(
                success=False,
                message=f"执行失败: {result['execution_result'].get('error', '未知错误')}"
            )
    except Exception as e:
        return APIResponse(success=False, message=f"AI 查询失败: {str(e)}")


# =============== 数据视图 API ===============

@app.post("/api/data/view", response_model=APIResponse)
async def get_data_view(request: ViewRequest):
    """获取表格分页视图"""
    engine = get_engine()
    
    try:
        view_data = engine.get_view_window(request.table_name, request.offset, request.limit)
        return APIResponse(success=True, message=f"获取 {len(view_data['data'])} 行", data=view_data)
    except Exception as e:
        return APIResponse(success=False, message=f"获取失败: {str(e)}")


@app.get("/api/data/full/{table_name}", response_model=APIResponse)
async def get_full_data(table_name: str):
    """获取完整表数据"""
    engine = get_engine()
    
    try:
        info = engine.get_table_info(table_name)
        if info[table_name]['rows'] > engine.SHADOW_THRESHOLD:
            return APIResponse(success=False, message=f"数据量超过 {engine.SHADOW_THRESHOLD} 行")
        
        data, columns = engine.execute_sql(f"SELECT * FROM {table_name}")
        return APIResponse(success=True, message="获取成功", data={'data': data, 'columns': columns})
    except Exception as e:
        return APIResponse(success=False, message=f"获取失败: {str(e)}")


@app.post("/api/query/sql", response_model=APIResponse)
async def execute_sql(request: SQLRequest):
    """执行 SQL 查询"""
    engine = get_engine()
    
    try:
        data, columns = engine.execute_sql(request.sql)
        return APIResponse(success=True, message=f"返回 {len(data)} 行", data={'data': data, 'columns': columns})
    except Exception as e:
        return APIResponse(success=False, message=f"查询失败: {str(e)}")


# =============== 表管理 API ===============

@app.delete("/api/table/{table_name}", response_model=APIResponse)
async def delete_table(table_name: str):
    engine = get_engine()
    if engine.drop_table(table_name):
        return APIResponse(success=True, message=f"表 {table_name} 已删除")
    return APIResponse(success=False, message=f"表 {table_name} 不存在")


@app.get("/api/table/{table_name}/info", response_model=APIResponse)
async def get_table_info(table_name: str):
    engine = get_engine()
    try:
        info = engine.get_table_info(table_name)
        desc = engine.describe_table(table_name)
        return APIResponse(success=True, message="获取成功", data={**info[table_name], 'description': desc})
    except ValueError as e:
        return APIResponse(success=False, message=str(e))


# =============== 配置 API ===============

@app.post("/api/config/reload", response_model=APIResponse)
async def reload_config():
    """重新加载 AI 代理配置"""
    try:
        reload_agent()
        return APIResponse(success=True, message="配置已重新加载")
    except Exception as e:
        return APIResponse(success=False, message=f"重载失败: {str(e)}")


class TableOpRequest(BaseModel):
    source_table: str
    target_name: str

@app.post("/api/table/rename", response_model=APIResponse)
async def rename_table(request: TableOpRequest):
    """重命名表格 (用于另存为)"""
    try:
        engine = get_db_engine()
        # 简单防 SQL 注入检查
        if not request.target_name.isidentifier():
             return APIResponse(success=False, message="表名不合法")
             
        engine.conn.execute(f"ALTER TABLE {request.source_table} RENAME TO {request.target_name}")
        # 更新元数据
        if request.source_table in engine.tables:
             del engine.tables[request.source_table]
        engine.tables[request.target_name] = {'rows': 0, 'columns': []} # 下次 refresh 会更新
        
        return APIResponse(success=True, message=f"已保存为 {request.target_name}")
    except Exception as e:
        return APIResponse(success=False, message=f"重命名失败: {str(e)}")

@app.post("/api/table/overwrite", response_model=APIResponse)
async def overwrite_table(request: TableOpRequest):
    """覆盖表格 (Drop Old -> Rename New)"""
    try:
        engine = get_db_engine()
        # 1. 删除旧表
        engine.conn.execute(f"DROP TABLE IF EXISTS {request.target_name}")
        # 2. 重命名新表
        engine.conn.execute(f"ALTER TABLE {request.source_table} RENAME TO {request.target_name}")
        
        # 更新表格列表
        if request.source_table in engine.tables:
            del engine.tables[request.source_table]
        # target_name 将在下次 refresh 时更新
        
        return APIResponse(success=True, message=f"已覆盖表格 {request.target_name}")
    except Exception as e:
        return APIResponse(success=False, message=f"覆盖失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
