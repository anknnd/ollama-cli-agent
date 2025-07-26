"""
Tests for LLM client functionality
"""

import pytest
from unittest.mock import Mock, patch
import requests

from src.llm.client import OllamaClient
from src.core.exceptions import LLMConnectionError, LLMTimeoutError, LLMResponseError

class TestOllamaClient:
    """Test LLM client functionality"""
    
    def test_chat_success(self, mock_config, mock_requests):
        """Test successful chat request"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            client = OllamaClient()
            
            messages = [{"role": "user", "content": "Test message"}]
            response = client.chat(messages)
            
            assert response.message.content == "Mock LLM response"
            assert response.message.role == "assistant"
            assert response.timing > 0
            assert response.model == "test-model"
    
    def test_chat_with_tools(self, mock_config, mock_requests):
        """Test chat request with tools"""
        mock_requests.return_value.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "Tool response",
                "tool_calls": [
                    {
                        "function": {
                            "name": "test_tool",
                            "arguments": {"arg": "value"}
                        }
                    }
                ]
            }
        }
        
        with patch('src.llm.client.get_config', return_value=mock_config):
            client = OllamaClient()
            
            messages = [{"role": "user", "content": "Use a tool"}]
            tools = [{"type": "function", "function": {"name": "test_tool"}}]
            
            response = client.chat(messages, tools)
            
            assert response.message.tool_calls is not None
            assert len(response.message.tool_calls) == 1
            assert response.message.tool_calls[0]["function"]["name"] == "test_tool"
    
    def test_connection_error(self, mock_config):
        """Test connection error handling"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.post', side_effect=requests.ConnectionError("Connection failed")):
                client = OllamaClient()
                
                with pytest.raises(LLMConnectionError):
                    client.chat([{"role": "user", "content": "test"}])
    
    def test_timeout_error(self, mock_config):
        """Test timeout error handling"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.post', side_effect=requests.Timeout("Request timed out")):
                client = OllamaClient()
                
                with pytest.raises(LLMTimeoutError):
                    client.chat([{"role": "user", "content": "test"}])
    
    def test_http_error(self, mock_config):
        """Test HTTP error handling"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response
                
                client = OllamaClient()
                
                with pytest.raises(LLMResponseError):
                    client.chat([{"role": "user", "content": "test"}])
    
    def test_invalid_response(self, mock_config):
        """Test invalid response handling"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.post') as mock_post:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {"invalid": "response"}  # Missing 'message'
                mock_post.return_value = mock_response
                
                client = OllamaClient()
                
                with pytest.raises(LLMResponseError):
                    client.chat([{"role": "user", "content": "test"}])
    
    def test_health_check_success(self, mock_config):
        """Test successful health check"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.get') as mock_get:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                client = OllamaClient()
                assert client.health_check() is True
    
    def test_health_check_failure(self, mock_config):
        """Test failed health check"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.get', side_effect=requests.ConnectionError("Connection failed")):
                client = OllamaClient()
                assert client.health_check() is False
    
    def test_list_models(self, mock_config):
        """Test model listing"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            with patch('requests.Session.get') as mock_get:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {
                    "models": [
                        {"name": "model1"},
                        {"name": "model2"}
                    ]
                }
                mock_get.return_value = mock_response
                
                client = OllamaClient()
                models = client.list_models()
                
                assert models == ["model1", "model2"]
    
    def test_legacy_compatibility(self, mock_config, mock_requests):
        """Test backward compatibility with old API"""
        with patch('src.llm.client.get_config', return_value=mock_config):
            client = OllamaClient()
            
            messages = [{"role": "user", "content": "Test"}]
            tools = [{"type": "function"}]
            
            message_dict, timing = client.chat_with_tools(messages, tools)
            
            assert message_dict["content"] == "Mock LLM response"
            assert message_dict["role"] == "assistant"
            assert timing > 0
