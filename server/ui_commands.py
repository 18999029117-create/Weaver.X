"""
UI Command Queue - 管理前端 UI 命令的队列
用于后端 AI 生成的 UI 命令传递给前端执行
"""

from typing import Any, Dict, List, Optional
import uuid
import time


class UICommandQueue:
    """UI 命令队列 - 单例模式"""
    
    def __init__(self):
        self.pending: List[Dict[str, Any]] = []
        self.executed: List[Dict[str, Any]] = []
        self.max_history = 100
    
    def add(self, command: Dict[str, Any]) -> str:
        """添加一条 UI 命令到队列
        
        Args:
            command: UI 命令字典，必须包含 'action' 字段
            
        Returns:
            命令 ID
        """
        cmd_id = str(uuid.uuid4())[:8]
        entry = {
            'id': cmd_id,
            'timestamp': time.time(),
            **command
        }
        self.pending.append(entry)
        return cmd_id
    
    def add_batch(self, commands: List[Dict[str, Any]]) -> List[str]:
        """批量添加 UI 命令
        
        Args:
            commands: UI 命令列表
            
        Returns:
            命令 ID 列表
        """
        return [self.add(cmd) for cmd in commands]
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """获取并清空待执行的命令
        
        Returns:
            待执行的命令列表
        """
        cmds = self.pending.copy()
        # 将已获取的命令移到历史记录
        self.executed.extend(cmds)
        self.pending.clear()
        
        # 限制历史记录大小
        if len(self.executed) > self.max_history:
            self.executed = self.executed[-self.max_history:]
        
        return cmds
    
    def peek_pending(self) -> List[Dict[str, Any]]:
        """查看待执行的命令（不清空）
        
        Returns:
            待执行的命令列表
        """
        return self.pending.copy()
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近执行的命令历史
        
        Args:
            limit: 返回的最大数量
            
        Returns:
            命令历史列表
        """
        return self.executed[-limit:]
    
    def clear(self):
        """清空所有命令"""
        self.pending.clear()
        self.executed.clear()


# 全局单例
_queue_instance: Optional[UICommandQueue] = None


def get_ui_queue() -> UICommandQueue:
    """获取全局 UI 命令队列实例"""
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = UICommandQueue()
    return _queue_instance
