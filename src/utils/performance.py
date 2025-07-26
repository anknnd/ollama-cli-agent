"""
Performance optimization utilities for Ollama CLI
"""

import time
import functools
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from threading import Lock

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    value: Any
    timestamp: float
    ttl: float
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > self.ttl

class TTLCache:
    """Simple TTL-based cache for performance optimization"""
    
    def __init__(self, default_ttl: float = 300):  # 5 minutes default
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    return entry.value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache with TTL"""
        with self.lock:
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )
            self.cache[key] = entry
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)

class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, logger=None):
        self.operation_name = operation_name
        self.logger = logger
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if self.logger:
            self.logger.print_timing(self.operation_name, duration)
    
    @property
    def duration(self) -> Optional[float]:
        """Get the duration if timing is complete"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

def cached(ttl: float = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        cache = TTLCache(default_ttl=ttl)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_info = lambda: {
            "hits": len(cache.cache),
            "misses": 0,  # Would need more complex tracking
            "currsize": len(cache.cache)
        }
        return wrapper
    return decorator

def optimize_imports():
    """Lazy import optimization for faster startup"""
    # This can be called to pre-load heavy modules
    import importlib
    
    # Pre-load commonly used modules
    modules = [
        'json', 'yaml', 'requests', 'rich.console', 
        'rich.panel', 'rich.progress'
    ]
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            pass

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_conversation_history(history: list, max_size: int = 10) -> list:
        """Optimize conversation history by keeping only recent messages"""
        if len(history) <= max_size:
            return history
        
        # Keep system message and recent messages
        system_msgs = [msg for msg in history if msg.get('role') == 'system']
        other_msgs = [msg for msg in history if msg.get('role') != 'system']
        
        # Keep most recent messages
        recent_msgs = other_msgs[-max_size:]
        
        return system_msgs + recent_msgs
    
    @staticmethod
    def cleanup_large_responses(response: str, max_length: int = 10000) -> str:
        """Truncate very large responses to save memory"""
        if len(response) > max_length:
            return response[:max_length] + "\n... [Response truncated for performance]"
        return response

# Global cache instance for shared use
_global_cache = TTLCache(default_ttl=300)

def get_global_cache() -> TTLCache:
    """Get the global cache instance"""
    return _global_cache
