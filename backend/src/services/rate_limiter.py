"""
Rate limiting service for preventing spam and brute force attempts.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AttemptRecord:
    """Record of an access attempt for rate limiting."""
    timestamp: datetime
    device_id: str
    user_id: str
    command: str
    success: bool


class RateLimiter:
    """In-memory rate limiter for access control commands."""
    
    def __init__(self):
        # Import here to avoid circular imports
        from config.settings import settings
        
        # Store attempts in memory - cleared when server restarts
        self.attempts: List[AttemptRecord] = []
        
        # Configuration loaded from settings
        self.max_attempts_per_minute = settings.rate_limit_max_attempts_per_minute
        self.max_failed_attempts = settings.rate_limit_max_failed_attempts
        self.lockout_duration_minutes = settings.rate_limit_lockout_duration_minutes
        self.cleanup_interval_minutes = settings.rate_limit_cleanup_interval_minutes
        
        self.last_cleanup = datetime.now()
        
        logger.info(f"Rate limiter initialized with config: "
                   f"max_attempts_per_minute={self.max_attempts_per_minute}, "
                   f"max_failed_attempts={self.max_failed_attempts}, "
                   f"lockout_duration_minutes={self.lockout_duration_minutes}")
    
    def check_rate_limit(self, device_id: str, user_id: str, command: str) -> Tuple[bool, str]:
        """
        Check if the request should be rate limited.
        
        Args:
            device_id: ID of the device
            user_id: ID of the user making the request
            command: The command being attempted
            
        Returns:
            Tuple of (is_allowed, reason_if_denied)
        """
        now = datetime.now()
        
        # Clean up old records periodically
        if (now - self.last_cleanup).total_seconds() > (self.cleanup_interval_minutes * 60):
            self._cleanup_old_attempts()
        
        # Check for recent failed attempts (brute force protection)
        recent_failed = self._get_recent_failed_attempts(device_id, user_id, now)
        if len(recent_failed) >= self.max_failed_attempts:
            last_failed = recent_failed[-1].timestamp
            lockout_expires = last_failed + timedelta(minutes=self.lockout_duration_minutes)
            
            if now < lockout_expires:
                remaining_seconds = int((lockout_expires - now).total_seconds())
                return False, f"Too many failed attempts. Locked out for {remaining_seconds} seconds"
        
        # Check for general rate limiting (all attempts)
        recent_attempts = self._get_recent_attempts(device_id, user_id, now)
        if len(recent_attempts) >= self.max_attempts_per_minute:
            return False, f"Rate limit exceeded. Max {self.max_attempts_per_minute} attempts per minute"
        
        return True, "Rate limit check passed"
    
    def record_attempt(self, device_id: str, user_id: str, command: str, success: bool) -> None:
        """
        Record an access attempt for rate limiting purposes.
        
        Args:
            device_id: ID of the device
            user_id: ID of the user
            command: The command that was attempted
            success: Whether the attempt was successful
        """
        attempt = AttemptRecord(
            timestamp=datetime.now(),
            device_id=device_id,
            user_id=user_id,
            command=command,
            success=success
        )
        
        self.attempts.append(attempt)
        logger.debug(f"Recorded attempt: {user_id} -> {device_id} ({command}) = {'SUCCESS' if success else 'FAILED'}")
    
    def _get_recent_attempts(self, device_id: str, user_id: str, now: datetime) -> List[AttemptRecord]:
        """Get recent attempts (last minute) for a user/device combination."""
        cutoff = now - timedelta(minutes=1)
        return [
            attempt for attempt in self.attempts
            if (attempt.device_id == device_id and 
                attempt.user_id == user_id and 
                attempt.timestamp >= cutoff)
        ]
    
    def _get_recent_failed_attempts(self, device_id: str, user_id: str, now: datetime) -> List[AttemptRecord]:
        """Get recent failed attempts for brute force detection."""
        cutoff = now - timedelta(minutes=self.lockout_duration_minutes)
        failed_attempts = [
            attempt for attempt in self.attempts
            if (attempt.device_id == device_id and 
                attempt.user_id == user_id and 
                attempt.timestamp >= cutoff and 
                not attempt.success)
        ]
        return sorted(failed_attempts, key=lambda x: x.timestamp)
    
    def _cleanup_old_attempts(self) -> None:
        """Remove old attempts to prevent memory bloat."""
        cutoff = datetime.now() - timedelta(hours=24)  # Keep last 24 hours
        original_count = len(self.attempts)
        
        self.attempts = [
            attempt for attempt in self.attempts
            if attempt.timestamp >= cutoff
        ]
        
        cleaned_count = original_count - len(self.attempts)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old rate limit attempts")
        
        self.last_cleanup = datetime.now()
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics."""
        now = datetime.now()
        
        # Count attempts in last hour
        last_hour = now - timedelta(hours=1)
        recent_attempts = [a for a in self.attempts if a.timestamp >= last_hour]
        
        # Count by success/failure
        successful = len([a for a in recent_attempts if a.success])
        failed = len([a for a in recent_attempts if not a.success])
        
        # Count unique users/devices
        unique_users = len(set(a.user_id for a in recent_attempts))
        unique_devices = len(set(a.device_id for a in recent_attempts))
        
        return {
            "total_attempts_last_hour": len(recent_attempts),
            "successful_attempts": successful,
            "failed_attempts": failed,
            "unique_users": unique_users,
            "unique_devices": unique_devices,
            "total_records": len(self.attempts),
            "config": {
                "max_attempts_per_minute": self.max_attempts_per_minute,
                "max_failed_attempts": self.max_failed_attempts,
                "lockout_duration_minutes": self.lockout_duration_minutes
            }
        }
    
    def get_user_status(self, device_id: str, user_id: str) -> Dict:
        """Get rate limiting status for a specific user/device combination."""
        now = datetime.now()
        
        recent_attempts = self._get_recent_attempts(device_id, user_id, now)
        recent_failed = self._get_recent_failed_attempts(device_id, user_id, now)
        
        # Check if currently locked out
        is_locked_out = False
        lockout_expires = None
        
        if len(recent_failed) >= self.max_failed_attempts:
            last_failed = recent_failed[-1].timestamp
            lockout_expires = last_failed + timedelta(minutes=self.lockout_duration_minutes)
            is_locked_out = now < lockout_expires
        
        return {
            "user_id": user_id,
            "device_id": device_id,
            "attempts_last_minute": len(recent_attempts),
            "failed_attempts_recent": len(recent_failed),
            "is_locked_out": is_locked_out,
            "lockout_expires": lockout_expires.isoformat() if lockout_expires else None,
            "remaining_lockout_seconds": int((lockout_expires - now).total_seconds()) if is_locked_out else 0
        }


# Global rate limiter instance
rate_limiter = RateLimiter()