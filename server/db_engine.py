"""
AI-Sheet-Pro DuckDB 数据引擎
支持 Excel/CSV 文件加载、SQL 查询、分页视图
"""

import os
import duckdb
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class DataEngine:
    """DuckDB 内存数据库引擎"""
    
    # 影子数据流阈值：超过此行数时启用分页
    SHADOW_THRESHOLD = 1000
    # 默认视图窗口大小
    DEFAULT_VIEW_SIZE = 100
    
    def __init__(self, temp_dir: str = None):
        """初始化数据引擎
        
        Args:
            temp_dir: 临时文件目录，用于安全沙箱
        """
        self.conn = duckdb.connect(':memory:')
        self.tables: Dict[str, dict] = {}  # 表元信息 {name: {rows, columns, schema}}
        
        # 设置临时目录
        if temp_dir:
            self.temp_dir = Path(temp_dir)
        else:
            self.temp_dir = Path(__file__).parent / 'temp'
        self.temp_dir.mkdir(exist_ok=True)
    
    def load_excel(self, file_path: str, table_name: str = None) -> dict:
        """加载 Excel 文件到内存表
        
        Args:
            file_path: Excel 文件路径
            table_name: 表名（可选，默认使用文件名）
            
        Returns:
            加载结果信息
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用文件名作为表名
        if not table_name:
            table_name = self._sanitize_table_name(path.stem)
        
        # 读取 Excel
        try:
            # 根据后缀选择引擎
            suffix = path.suffix.lower()
            if suffix == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"Excel加载尝试失败 ({str(e)}), 正在重试默认引擎...")
            # 失败后尝试自动检测
            df = pd.read_excel(file_path)
            
        return self._register_dataframe(df, table_name)
    
    def load_csv(self, file_path: str, table_name: str = None, encoding: str = 'utf-8') -> dict:
        """加载 CSV 文件到内存表
        
        Args:
            file_path: CSV 文件路径
            table_name: 表名（可选）
            encoding: 文件编码
            
        Returns:
            加载结果信息
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not table_name:
            table_name = self._sanitize_table_name(path.stem)
        
        # 尝试多种编码
        for enc in [encoding, 'utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"无法解析文件编码: {file_path}")
        
        return self._register_dataframe(df, table_name)
    
    def load_dataframe(self, df: pd.DataFrame, table_name: str) -> dict:
        """直接加载 DataFrame 到内存表"""
        table_name = self._sanitize_table_name(table_name)
        return self._register_dataframe(df, table_name)
    
    def _register_dataframe(self, df: pd.DataFrame, table_name: str) -> dict:
        """将 DataFrame 注册为 DuckDB 表"""
        # 确保表名唯一且安全
        # 注册表 (使用 CREATE TABLE AS 真正创建表，而不是 View，以便支持 UPDATE/DELETE)
        # 先注册个临时视图
        temp_view = f"_temp_view_{table_name}"
        self.conn.register(temp_view, df)
        
        # 然后创建实体表
        self.conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        self.conn.execute(f'CREATE TABLE "{table_name}" AS SELECT * FROM "{temp_view}"')
        
        # 清理临时视图
        self.conn.unregister(temp_view)
        
        # 获取表信息
        row_count = len(df)
        col_count = len(df.columns)
        schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        # 记录元信息
        self.tables[table_name] = {
            'rows': row_count,
            'columns': col_count,
            'schema': schema,
            'column_names': list(df.columns),
            'use_shadow': row_count > self.SHADOW_THRESHOLD
        }
        
        return {
            'table_name': table_name,
            'rows': row_count,
            'columns': col_count,
            'use_shadow': row_count > self.SHADOW_THRESHOLD,
            'schema': schema
        }
    
    def execute_sql(self, sql: str) -> Tuple[List[dict], List[str]]:
        """执行 SQL 查询
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            (数据行列表, 列名列表)
        """
        try:
            result = self.conn.execute(sql)
            df = result.fetchdf()
            columns = list(df.columns)
            data = df.to_dict(orient='records')
            return data, columns
        except Exception as e:
            raise RuntimeError(f"SQL 执行失败: {str(e)}")
    
    def get_view_window(self, table_name: str, offset: int = 0, limit: int = None) -> dict:
        """获取表格分页视图窗口
        
        Args:
            table_name: 表名
            offset: 起始行偏移
            limit: 返回行数
            
        Returns:
            视图数据
        """
        if table_name not in self.tables:
            raise ValueError(f"表不存在: {table_name}")
        
        if limit is None:
            limit = self.DEFAULT_VIEW_SIZE
        
        table_info = self.tables[table_name]
        sql = f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}"
        
        data, columns = self.execute_sql(sql)
        
        return {
            'table_name': table_name,
            'total_rows': table_info['rows'],
            'total_columns': table_info['columns'],
            'offset': offset,
            'limit': limit,
            'data': data,
            'columns': columns,
            'has_more': offset + limit < table_info['rows']
        }
    
    def get_table_info(self, table_name: str = None) -> dict:
        """获取表结构信息"""
        if table_name:
            if table_name not in self.tables:
                raise ValueError(f"表不存在: {table_name}")
            return {table_name: self.tables[table_name]}
        return self.tables.copy()
    
    def get_all_tables(self) -> List[str]:
        """获取所有已加载的表名"""
        return list(self.tables.keys())
    
    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        if table_name in self.tables:
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            del self.tables[table_name]
            return True
            return True
        return False

    def refresh_metadata(self) -> None:
        """强制刷新所有表的元数据（主要是行数）"""
        for table_name in list(self.tables.keys()):
            try:
                # 获取最新行数
                res = self.conn.execute(f'SELECT count(*) FROM "{table_name}"').fetchone()
                if res:
                    self.tables[table_name]['rows'] = res[0]
            except Exception as e:
                print(f"Error refreshing metadata for {table_name}: {e}")
    
    def _sanitize_table_name(self, name: str) -> str:
        """清理表名，确保符合 SQL 命名规范"""
        # 替换非法字符
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', name)
        # 确保不以数字开头
        if clean_name and clean_name[0].isdigit():
            clean_name = 't_' + clean_name
        return clean_name or 'unnamed_table'
    
    def get_sample_data(self, table_name: str, n: int = 5) -> List[dict]:
        """获取表的样本数据"""
        sql = f"SELECT * FROM {table_name} LIMIT {n}"
        data, _ = self.execute_sql(sql)
        return data
    

    def describe_table(self, table_name: str) -> str:
        """生成表的描述文本（用于 AI 上下文）"""
        if table_name not in self.tables:
            raise ValueError(f"表不存在: {table_name}")
        
        info = self.tables[table_name]
        desc = f"表名: {table_name}\n"
        desc += f"行数: {info['rows']}, 列数: {info['columns']}\n"
        desc += "列信息:\n"
        for col, dtype in info['schema'].items():
            desc += f"  - {col}: {dtype}\n"
        
        # 添加样本数据
        sample = self.get_sample_data(table_name, 3)
        if sample:
            desc += "\n前3行样本:\n"
            for i, row in enumerate(sample):
                desc += f"  {i+1}: {row}\n"
        
        return desc
    
    def inspect_column(self, table_name: str, column_name: str, n: int = 10) -> List[Any]:
        """探查某列的唯一值（用于 AI 确认枚举值）"""
        if table_name not in self.tables:
            raise ValueError(f"表不存在: {table_name}")
            
        # 安全检查列名
        clean_col = self._sanitize_table_name(column_name)
        # 注意：这里不能简单 sanitize，因为列名可能包含非 ASCII 字符，但 DuckDB 支持双引号包裹
        # 我们假设调用方传入的 column_name 是合法的或已经在 AI 上下文中存在
        
        # 1. 检查列是否存在
        info = self.tables[table_name]
        if column_name not in info['schema']:
            # 尝试不区分大小写查找
            found = False
            for real_col in info['schema']:
                if real_col.lower() == column_name.lower():
                    column_name = real_col
                    found = True
                    break
            if not found:
                raise ValueError(f"表 {table_name} 中不存在列 {column_name}")

        try:
            # 2. 查询 Distinct 值
            # 限制数据量，防止对超大表进行全表扫描（虽然 DuckDB 很快，但还是防御一下）
            # 如果行数 > 50000，先采样？DuckDB 的 DISTINCT 优化很好，直接查通常没问题。
            
            sql = f'SELECT DISTINCT "{column_name}" FROM "{table_name}" LIMIT {n}'
            res = self.conn.execute(sql).fetchall()
            return [r[0] for r in res]
        except Exception as e:
            raise RuntimeError(f"探查列失败: {str(e)}")



    def export_table_as_excel(self, table_name: str, output_path: str) -> str:
        """将表导出为 Excel 文件
        
        Args:
            table_name: 表名
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        if table_name not in self.tables:
            raise ValueError(f"表不存在: {table_name}")
            
        # SQL 查询全量数据
        sql = f"SELECT * FROM {table_name}"
        result = self.conn.execute(sql)
        df = result.fetchdf()
        
        # 导出为 Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        return output_path

# 全局单例
_engine_instance: Optional[DataEngine] = None



def get_engine() -> DataEngine:
    """获取全局数据引擎实例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DataEngine()
    return _engine_instance
