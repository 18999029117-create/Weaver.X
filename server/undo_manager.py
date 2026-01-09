import uuid
from typing import List, Tuple, Dict
from db_engine import get_engine, DataEngine

class UndoManager:
    """管理表格操作的撤回 (基于 DuckDB 快照)"""
    
    def __init__(self):
        self.history_stack: List[Dict] = [] # 栈顶是最近的操作
        
    def create_snapshot(self, table_names: List[str]) -> str:
        """为指定表创建快照"""
        if not table_names:
            return None
            
        engine = get_engine()
        snapshot_id = str(uuid.uuid4())[:8]
        
        snapshot_info = {
            'id': snapshot_id,
            'tables': []
        }
        
        for table in table_names:
            if table in engine.tables:
                # 创建备份表: _snap_{id}_{table}
                snap_table_name = f"_snap_{snapshot_id}_{table}"
                try:
                    engine.conn.execute(f'CREATE TABLE "{snap_table_name}" AS SELECT * FROM "{table}"')
                    snapshot_info['tables'].append({
                        'original': table,
                        'backup': snap_table_name
                    })
                except Exception as e:
                    print(f"创建快照失败 {table}: {e}")
        
        if snapshot_info['tables']:
            self.history_stack.append(snapshot_info)
            # 限制历史记录数量防止内存爆炸 (例如 20 次)
            if len(self.history_stack) > 20:
                self._cleanup_snapshot(self.history_stack.pop(0))
            return snapshot_id
        return None
        
    def undo(self) -> Dict:
        """执行撤回操作"""
        if not self.history_stack:
            return {'success': False, 'message': '没有可撤回的操作'}
            
        # 弹出最近的快照
        snapshot = self.history_stack.pop()
        engine = get_engine()
        restored_tables = []
        
        try:
            for item in snapshot['tables']:
                original = item['original']
                backup = item['backup']
                
                # 1. 恢复表数据
                # 先删除当前的（可能已被修改的）表
                engine.conn.execute(f'DROP TABLE IF EXISTS "{original}"')
                # 将备份表重命名回原表名
                engine.conn.execute(f'ALTER TABLE "{backup}" RENAME TO "{original}"')
                
                # 2. 更新引擎元数据 (重新注册)
                # 使用 db_engine 的内部方法稍显麻烦，直接查一遍元数据
                # 或者调用 engine._register_dataframe? 不，直接读 SQL
                df = engine.conn.execute(f'SELECT * FROM "{original}"').fetchdf()
                engine._register_dataframe(df, original)
                
                restored_tables.append(original)
                
            return {
                'success': True, 
                'message': f"已撤回操作，恢复了: {', '.join(restored_tables)}",
                'restored_tables': restored_tables
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f"撤回失败: {str(e)}"}

    def _cleanup_snapshot(self, snapshot):
        """清理过期的快照表"""
        engine = get_engine()
        for item in snapshot['tables']:
            backup = item['backup']
            try:
                engine.conn.execute(f'DROP TABLE IF EXISTS "{backup}"')
            except:
                pass


# 全局单例
_undo_manager = None

def get_undo_manager() -> UndoManager:
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoManager()
    return _undo_manager
