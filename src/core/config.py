"""
Configuration management system for Ollama CLI
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class Config:
    """Application configuration with environment variable support"""
    
    # LLM Settings
    ollama_url: str = "http://localhost:11434/api/chat"
    model: str = "llama3.1:8b"
    timeout: int = 30
    
    # Agent Settings
    max_history: int = 10
    verbosity: str = "info"
    
    # Directories
    log_dir: str = "logs"
    sessions_dir: str = "sessions"
    tool_dir: str = "plugins"
    
    # Tool Settings
    tool_timeout: int = 10
    max_tool_calls: int = 5
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables"""
        return cls(
            ollama_url=os.getenv('OLLAMA_URL', cls.ollama_url),
            model=os.getenv('OLLAMA_MODEL', cls.model),
            timeout=int(os.getenv('OLLAMA_TIMEOUT', cls.timeout)),
            max_history=int(os.getenv('MAX_HISTORY', cls.max_history)),
            verbosity=os.getenv('VERBOSITY', cls.verbosity),
            log_dir=os.getenv('LOG_DIR', cls.log_dir),
            sessions_dir=os.getenv('SESSIONS_DIR', cls.sessions_dir),
            tool_dir=os.getenv('TOOL_DIR', cls.tool_dir),
            tool_timeout=int(os.getenv('TOOL_TIMEOUT', cls.tool_timeout)),
            max_tool_calls=int(os.getenv('MAX_TOOL_CALLS', cls.max_tool_calls)),
        )
    
    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> 'Config':
        """Load config from .agentrc file"""
        if config_path is None:
            config_path = Path.cwd() / ".agentrc"
        
        config = cls.from_env()  # Start with env vars
        
        if Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Override with file values
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                    else:
                        config.custom[key] = value
                        
            except Exception as e:
                # Don't fail on config errors, just use defaults
                print(f"Warning: Could not load config file {config_path}: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with fallback to custom settings"""
        if hasattr(self, key):
            return getattr(self, key)
        return self.custom.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if field_name != 'custom':
                result[field_name] = value
        result.update(self.custom)
        return result

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_file()
    return _config

def reload_config(config_path: Optional[str] = None) -> Config:
    """Reload configuration from file"""
    global _config
    _config = Config.from_file(config_path)
    return _config
