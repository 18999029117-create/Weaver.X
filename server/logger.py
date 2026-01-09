
import time
import uuid
from typing import List, Dict, Any, Optional

class LogManager:
    """In-memory log manager for system monitoring."""
    
    def __init__(self, max_logs: int = 1000):
        self._logs: List[Dict[str, Any]] = []
        self._max_logs = max_logs

    def add_log(self, type: str, content: str, details: Any = None) -> None:
        """Add a new log entry.
        
        Args:
            type: Log type (e.g., "INFO", "AI_REQ", "AI_RES", "SQL")
            content: Brief description
            details: Detailed object (JSON or string)
        """
        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'type': type,
            'content': content,
            'details': details
        }
        self._logs.append(entry)
        
        # Keep size limit
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
            
    def get_logs(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs since a specific ID."""
        if not since_id:
            return self._logs
            
        # Find index of since_id
        start_idx = -1
        for i, log in enumerate(self._logs):
            if log['id'] == since_id:
                start_idx = i
                break
        
        if start_idx != -1:
            return self._logs[start_idx + 1:]
        
        # If ID not found (maybe cleared), return all or empty? 
        # Strategy: if ID provided but not found, assume client is out of sync or logs rotated.
        # Ideally return all to resync, or assume they are new. 
        # For simplicity, if id not found, return empty to avoid duplicates if client has old ID, 
        # unless it's way old. 
        # Better strategy for simple polling: just return all if not found might duplicate.
        # Let's return only if we find the anchor, otherwise return all (client reset)?
        # Safe approach: return all logs if since_id not found only if it was requested.
        # Actually, simpler: client sends last known ID. If found, send subsequent. If not found (rotated out), send all.
        return self._logs

# Global instance
_logger_instance: Optional[LogManager] = None

def get_logger() -> LogManager:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LogManager()
    return _logger_instance
