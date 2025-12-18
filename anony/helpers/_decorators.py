# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import logging
from collections import defaultdict
from functools import wraps
from time import time

# Use direct logging to avoid circular import
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting untuk prevent spam"""
    
    def __init__(self, max_calls: int = 5, period: int = 60):
        """
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)
        self.blocked_until = {}
    
    def is_allowed(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user is allowed to make a call
        
        Returns:
            tuple: (is_allowed: bool, retry_after: int)
        """
        now = time()
        
        # Check if user is temporarily blocked
        if user_id in self.blocked_until:
            if now < self.blocked_until[user_id]:
                retry_after = int(self.blocked_until[user_id] - now)
                return False, retry_after
            else:
                del self.blocked_until[user_id]
        
        # Remove old calls
        self.calls[user_id] = [
            call_time for call_time in self.calls[user_id]
            if now - call_time < self.period
        ]
        
        # Check if limit exceeded
        if len(self.calls[user_id]) >= self.max_calls:
            # Block user for the period
            self.blocked_until[user_id] = now + self.period
            retry_after = self.period
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False, retry_after
        
        # Allow the call
        self.calls[user_id].append(now)
        return True, 0
    
    def reset(self, user_id: int) -> None:
        """Reset rate limit for a user"""
        self.calls.pop(user_id, None)
        self.blocked_until.pop(user_id, None)
    
    def get_stats(self, user_id: int) -> dict:
        """Get rate limit stats for a user"""
        now = time()
        recent_calls = [
            call_time for call_time in self.calls.get(user_id, [])
            if now - call_time < self.period
        ]
        
        return {
            "calls_made": len(recent_calls),
            "calls_remaining": max(0, self.max_calls - len(recent_calls)),
            "reset_in": self.period - (now - recent_calls[0]) if recent_calls else 0,
            "is_blocked": user_id in self.blocked_until and now < self.blocked_until[user_id]
        }


def safe_execute(send_error: bool = True):
    """
    Decorator untuk safe execution dengan proper error handling
    
    Args:
        send_error: If True, send error message to user
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            try:
                return await func(client, message, *args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"Error in {func.__name__}: {error_msg}",
                    exc_info=True,
                    extra={
                        "user_id": message.from_user.id if message.from_user else None,
                        "chat_id": message.chat.id if message.chat else None,
                        "command": message.text[:50] if message.text else None
                    }
                )
                
                if send_error and hasattr(message, 'reply_text'):
                    try:
                        await message.reply_text(
                            f"❌ <b>Terjadi Kesalahan</b>\n\n"
                            f"<blockquote>Maaf, terjadi error saat memproses perintah Anda. "
                            f"Silakan coba lagi atau hubungi admin jika masalah berlanjut.</blockquote>",
                            parse_mode="HTML"
                        )
                    except:
                        pass
        
        return wrapper
    return decorator


def require_rate_limit(limiter: RateLimiter):
    """
    Decorator untuk apply rate limiting pada command
    
    Args:
        limiter: RateLimiter instance to use
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            user_id = message.from_user.id
            is_allowed, retry_after = limiter.is_allowed(user_id)
            
            if not is_allowed:
                return await message.reply_text(
                    f"⏱️ <b>Rate Limit Exceeded</b>\n\n"
                    f"<blockquote>Anda terlalu banyak mengirim perintah. "
                    f"Silakan tunggu <b>{retry_after} detik</b> sebelum mencoba lagi.</blockquote>",
                    parse_mode="HTML"
                )
            
            return await func(client, message, *args, **kwargs)
        
        return wrapper
    return decorator


# Global rate limiters
play_limiter = RateLimiter(max_calls=5, period=60)  # 5 plays per minute
search_limiter = RateLimiter(max_calls=10, period=60)  # 10 searches per minute
command_limiter = RateLimiter(max_calls=20, period=60)  # 20 commands per minute
