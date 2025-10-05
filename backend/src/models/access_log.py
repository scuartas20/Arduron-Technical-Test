"""
Access log models for tracking access events for various devices.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel



class AccessStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    
class AccessCommand(str, Enum):
    OPEN = "open"
    CLOSE = "close"
    LOCK = "lock"
    UNLOCK = "unlock"

class AccessAttemptIn(BaseModel):
    device_id: str
    user_id: str
    command: AccessCommand

class AccessEvent(BaseModel):
    timestamp: datetime
    device_id: str
    user_id: str
    command: AccessCommand
    status: AccessStatus
    message: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "device_id": self.device_id,
            "user_id": self.user_id,
            "command": self.command,
            "status": self.status,
            "message": self.message
        }


class AccessLogRegistry:
    """In-memory registry of all access events."""
    
    def __init__(self):
        self.logs: List[AccessEvent] = []
    
    def add_log(self, event: AccessEvent) -> None:
        self.logs.append(event)
    
    def get_logs(self, limit: int = 100) -> List[AccessEvent]:
        return sorted(
            self.logs,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
    
    def get_logs_by_device(self, device_id: str, limit: int = 50) -> List[AccessEvent]:
        return sorted(
            [log for log in self.logs if log.device_id == device_id],
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]