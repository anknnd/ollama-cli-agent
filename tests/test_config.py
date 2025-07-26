"""
Tests for configuration management
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.config import Config

class TestConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.ollama_url == "http://localhost:11434/api/chat"
        assert config.model == "llama3.1:8b"
        assert config.timeout == 30
        assert config.max_history == 10
        assert config.verbosity == "info"
    
    def test_from_env(self):
        """Test configuration from environment variables"""
        # Set environment variables
        os.environ['OLLAMA_URL'] = 'http://test:11434/api/chat'
        os.environ['OLLAMA_MODEL'] = 'test-model'
        os.environ['MAX_HISTORY'] = '20'
        
        try:
            config = Config.from_env()
            
            assert config.ollama_url == 'http://test:11434/api/chat'
            assert config.model == 'test-model'
            assert config.max_history == 20
            
        finally:
            # Clean up environment variables
            for key in ['OLLAMA_URL', 'OLLAMA_MODEL', 'MAX_HISTORY']:
                os.environ.pop(key, None)
    
    def test_from_file(self, temp_dir):
        """Test configuration from file"""
        config_file = temp_dir / ".agentrc"
        config_content = """
ollama_url: "http://file-config:11434/api/chat"
model: "file-model"
max_history: 15
custom_setting: "test_value"
"""
        config_file.write_text(config_content)
        
        config = Config.from_file(str(config_file))
        
        assert config.ollama_url == "http://file-config:11434/api/chat"
        assert config.model == "file-model"
        assert config.max_history == 15
        assert config.get("custom_setting") == "test_value"
    
    def test_get_method(self):
        """Test config.get() method"""
        config = Config()
        config.custom = {"test_key": "test_value"}
        
        # Test existing attribute
        assert config.get("model") == "llama3.1:8b"
        
        # Test custom setting
        assert config.get("test_key") == "test_value"
        
        # Test default value
        assert config.get("nonexistent", "default") == "default"
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = Config(model="test-model")
        config.custom = {"custom_key": "custom_value"}
        
        config_dict = config.to_dict()
        
        assert config_dict["model"] == "test-model"
        assert config_dict["custom_key"] == "custom_value"
        assert "custom" not in config_dict  # Should be flattened
