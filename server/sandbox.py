"""
AI-Sheet-Pro 安全沙箱
限制 AI 生成代码的执行范围，确保安全性
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import contextmanager
import traceback
from logger import get_logger


class SandboxError(Exception):
    """沙箱执行错误"""
    pass


class CodeSandbox:
    """代码执行安全沙箱"""
    
    # 禁止的模块列表
    BLOCKED_MODULES = {
        'os.system', 'subprocess', 'shutil.rmtree', 
        'socket', 'urllib', 'requests', 'httpx',
        'ftplib', 'smtplib', 'telnetlib',
        '__builtins__.exec', '__builtins__.eval',
        'ctypes', 'multiprocessing',
    }
    
    # 允许的模块列表
    ALLOWED_MODULES = {
        'pandas', 'numpy', 'duckdb', 'math', 'statistics',
        'datetime', 'json', 're', 'collections', 'itertools',
        'functools', 'operator', 'decimal', 'fractions',
    }
    
    def __init__(self, temp_dir: str = None, max_memory_mb: int = 512):
        """初始化沙箱
        
        Args:
            temp_dir: 临时文件目录（代码只能在此目录内操作文件）
            max_memory_mb: 最大内存限制（MB）
        """
        if temp_dir:
            self.temp_dir = Path(temp_dir).resolve()
        else:
            self.temp_dir = Path(__file__).parent / 'temp'
        
        self.temp_dir.mkdir(exist_ok=True)
        self.max_memory_mb = max_memory_mb
        self.execution_history = []
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """验证代码安全性
        
        Args:
            code: 要验证的代码
            
        Returns:
            (是否安全, 错误信息)
        """
        # 检查危险关键字
        dangerous_patterns = [
            'import os',
            'from os import',
            'import subprocess',
            'from subprocess',
            'import socket',
            'from socket',
            '__import__',
            'eval(',
            'exec(',
            'compile(',
            'open(',  # 需要在沙箱内重新定义
            'os.system',
            'os.popen',
            'os.remove',
            'os.unlink',
            'shutil.rmtree',
            'sys.exit',
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                # 特殊处理：允许 pandas/duckdb 的安全 open 操作
                if pattern == 'open(' and ('pd.read' in code or 'duckdb' in code):
                    continue
                return False, f"检测到危险代码模式: {pattern}"
        
        return True, ""
    
    def create_safe_globals(self, db_connection=None) -> dict:
        """创建安全的全局变量环境"""
        import pandas as pd
        import numpy as np
        import duckdb
        import math
        import json
        import re
        from datetime import datetime, date, timedelta
        from collections import Counter, defaultdict
        
        # 安全的文件操作（仅限 temp 目录）
        def safe_open(path, mode='r', *args, **kwargs):
            abs_path = Path(path).resolve()
            if not str(abs_path).startswith(str(self.temp_dir)):
                raise SandboxError(f"文件操作被拒绝：只能访问 {self.temp_dir} 目录")
            return open(abs_path, mode, *args, **kwargs)
        
        safe_globals = {
            # 数据处理库
            'pd': pd,
            'pandas': pd,
            'np': np,
            'numpy': np,
            'duckdb': duckdb,
            
            # 数学和统计
            'math': math,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'len': len,
            'sorted': sorted,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            
            # 类型和工具
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'type': type,
            'isinstance': isinstance,
            
            # 日期时间
            'datetime': datetime,
            'date': date,
            'timedelta': timedelta,
            
            # JSON
            'json': json,
            
            # 正则
            're': re,
            
            # 集合工具
            'Counter': Counter,
            'defaultdict': defaultdict,
            
            # 安全文件操作
            'open': safe_open,
            
            # 打印（用于调试）
            'print': print,
            
            # 数据库连接（如果提供）
            'db': db_connection,
        }
        
        return safe_globals
    
    def execute(self, code: str, local_vars: dict = None, db_connection=None) -> Dict[str, Any]:
        """在沙箱中执行代码
        
        Args:
            code: 要执行的 Python 代码
            local_vars: 本地变量
            db_connection: DuckDB 连接
            
        Returns:
            执行结果字典
        """
        # 验证代码安全性
        is_safe, error_msg = self.validate_code(code)
        if not is_safe:
            return {
                'success': False,
                'error': error_msg,
                'result': None
            }
        
        # 创建安全环境
        safe_globals = self.create_safe_globals(db_connection)
        local_namespace = local_vars.copy() if local_vars else {}
        
        # 记录执行历史
        execution_record = {
            'code': code,
            'timestamp': str(Path(__file__)),
        }
        
        try:
            # 执行代码
            exec(code, safe_globals, local_namespace)
            
            # 获取结果（约定：结果存储在 'result' 变量中）
            result = local_namespace.get('result', None)
            
            # 如果结果是 DataFrame，转换为可序列化格式
            import pandas as pd
            if isinstance(result, pd.DataFrame):
                result = {
                    'type': 'dataframe',
                    'data': result.to_dict(orient='records'),
                    'columns': list(result.columns),
                    'shape': result.shape
                }
            
            execution_record['success'] = True
            execution_record['result'] = result
            self.execution_history.append(execution_record)
            
            return {
                'success': True,
                'result': result,
                'error': None,
                'local_vars': {k: str(v)[:100] for k, v in local_namespace.items() 
                              if not k.startswith('_')}
            }
            
        except Exception as e:
            error_trace = traceback.format_exc()
            execution_record['success'] = False
            execution_record['error'] = str(e)
            self.execution_history.append(execution_record)
            
            # 记录到系统日志 (便于调试 SyntaxError)
            get_logger().add_log("ERROR", f"Execution failed: {str(e)}", details={
                "code": code,
                "traceback": error_trace
            })
            
            return {
                'success': False,
                'result': None,
                'error': f"{type(e).__name__}: {str(e)}",
                'traceback': error_trace
            }
    
    def get_temp_path(self, filename: str) -> Path:
        """获取 temp 目录下的文件路径"""
        return self.temp_dir / filename
    
    def cleanup_temp(self, max_age_hours: int = 24):
        """清理过期的临时文件"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()


# 全局沙箱实例
_sandbox_instance: Optional[CodeSandbox] = None


def get_sandbox() -> CodeSandbox:
    """获取全局沙箱实例"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = CodeSandbox()
    return _sandbox_instance
