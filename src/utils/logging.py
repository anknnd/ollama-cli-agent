"""
Logging infrastructure for Ollama CLI
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler

from src.core.config import get_config

class OllamaLogger:
    """Centralized logging for Ollama CLI"""
    
    def __init__(self, name: str = "ollama-cli"):
        self.name = name
        self.config = get_config()
        self.console = Console()
        self._logger: Optional[logging.Logger] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self._logger = logging.getLogger(self.name)
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Set level based on verbosity
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR
        }
        level = level_map.get(self.config.verbosity.lower(), logging.INFO)
        self._logger.setLevel(level)
        
        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(level)
        
        # Format for console
        console_format = "%(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
        
        self._logger.addHandler(console_handler)
        
        # File handler for debug logs
        if self.config.verbosity.lower() == "debug":
            self._add_file_handler()
    
    def _add_file_handler(self):
        """Add file handler for persistent logging"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"ollama-cli-{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Detailed format for file
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        
        self._logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with structured context"""
        if kwargs:
            context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{message} [{context_str}]"
        
        self._logger.log(level, message)
    
    def print_message(self, message: str, style: str = "", level: str = "info"):
        """Print message to console with Rich formatting"""
        level_styles = {
            "debug": "dim",
            "info": "",
            "warn": "yellow",
            "error": "bold red"
        }
        
        final_style = style or level_styles.get(level, "")
        self.console.print(message, style=final_style)
    
    def print_tool_call(self, tool_name: str, args: dict):
        """Print tool call information"""
        self.console.print(f"[bold blue]🔧 Tool Call:[/bold blue] {tool_name}")
        if args:
            self.console.print(f"[dim]Args: {args}[/dim]")
    
    def print_tool_result(self, tool_name: str, result: str, success: bool = True):
        """Print tool result"""
        icon = "✅" if success else "❌"
        style = "green" if success else "red"
        self.console.print(f"[{style}]{icon} {tool_name}:[/{style}] {result[:100]}...")
    
    def print_timing(self, operation: str, duration: float):
        """Print timing information"""
        self.console.print(f"[dim]⏱️  {operation}: {duration:.2f}s[/dim]")

# Global logger instance
_logger: Optional[OllamaLogger] = None

def get_logger() -> OllamaLogger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        _logger = OllamaLogger()
    return _logger

def setup_logging(verbosity: str = None):
    """Setup logging with specified verbosity"""
    global _logger
    if verbosity:
        config = get_config()
        config.verbosity = verbosity
    _logger = OllamaLogger()
    return _logger
