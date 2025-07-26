"""
LLM API client with proper error handling and retry logic
"""

import time
import requests
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

from ..core.config import get_config
from src.core.config import get_config
from src.core.exceptions import (
    LLMError, 
    LLMConnectionError, 
    LLMTimeoutError, 
    LLMResponseError
)
from src.utils.logging import get_logger
from ..utils.logging import get_logger

@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_name: Optional[str] = None

@dataclass
class LLMResponse:
    """Represents an LLM response"""
    message: ChatMessage
    timing: float
    model: str
    total_tokens: Optional[int] = None

class OllamaClient:
    """Robust Ollama API client with error handling"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.base_url = self.config.ollama_url.replace('/api/chat', '')
        self.chat_url = f"{self.base_url}/api/chat"
        self.session = requests.Session()
        
        # Set default timeout
        self.session.timeout = self.config.timeout
    
    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Send chat request to Ollama"""
        start_time = time.time()
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            self.logger.debug("Sending chat request", 
                            model=self.config.model, 
                            message_count=len(messages),
                            has_tools=bool(tools))
            
            response = self.session.post(
                self.chat_url,
                json=payload,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            
            duration = time.time() - start_time
            
            # Validate response structure
            if 'message' not in data:
                raise LLMResponseError("Invalid response: missing 'message' field", data)
            
            message_data = data['message']
            if 'content' not in message_data:
                raise LLMResponseError("Invalid response: missing 'content' in message", data)
            
            # Extract message details
            chat_message = ChatMessage(
                role=message_data.get('role', 'assistant'),
                content=message_data.get('content', ''),
                tool_calls=message_data.get('tool_calls'),
                tool_name=message_data.get('tool_name')
            )
            
            llm_response = LLMResponse(
                message=chat_message,
                timing=duration,
                model=self.config.model,
                total_tokens=data.get('total_tokens')
            )
            
            self.logger.debug("Chat request completed", 
                            duration=duration,
                            has_tool_calls=bool(chat_message.tool_calls))
            
            return llm_response
            
        except requests.exceptions.ConnectionError as e:
            raise LLMConnectionError(self.chat_url, e)
        
        except requests.exceptions.Timeout as e:
            raise LLMTimeoutError(self.config.timeout)
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            if e.response.text:
                error_msg += f": {e.response.text}"
            raise LLMResponseError(error_msg, {"status_code": e.response.status_code})
        
        except Exception as e:
            raise LLMResponseError(f"Unexpected error: {e}")
    
    def chat_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict]) -> Tuple[Dict, float]:
        """Legacy method for backward compatibility"""
        response = self.chat(messages, tools)
        
        # Convert back to old format for compatibility
        message_dict = {
            'role': response.message.role,
            'content': response.message.content
        }
        
        if response.message.tool_calls:
            message_dict['tool_calls'] = response.message.tool_calls
        
        return message_dict, response.timing
    
    def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            self.logger.debug("Health check passed")
            return True
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get('models', []):
                models.append(model.get('name', ''))
            
            return models
        except Exception as e:
            self.logger.error("Failed to list models", error=str(e))
            return []

# Global client instance
_client: Optional[OllamaClient] = None

def get_client() -> OllamaClient:
    """Get the global Ollama client instance"""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
