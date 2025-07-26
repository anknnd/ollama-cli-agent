"""
Test configuration and fixtures
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import Config
from src.tools import ToolRegistry

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return Config(
        ollama_url="http://localhost:11434/api/chat",
        model="test-model",
        timeout=30,
        max_history=10,
        verbosity="debug",
        log_dir="test_logs",
        tool_dir="test_plugins"
    )

@pytest.fixture
def tool_registry():
    """Fresh tool registry for each test"""
    return ToolRegistry()

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "message": {
            "role": "assistant",
            "content": "Test response content"
        }
    }

@pytest.fixture
def mock_requests():
    """Mock requests module for HTTP testing"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant", 
                "content": "Mock LLM response"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        yield mock_post
