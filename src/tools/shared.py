"""
Shared utilities for tools
"""

import requests
from src.core.config import get_config
from src.core.exceptions import LLMError, LLMConnectionError, LLMTimeoutError

def generate_content_with_llm(prompt: str, system_message: str = "You are a helpful assistant.") -> str:
    """Common function to generate content using LLM
    
    Args:
        prompt: The user prompt
        system_message: The system message for context
    
    Returns:
        Generated content as string
    
    Raises:
        LLMError: If there's an error with the LLM request
    """
    config = get_config()
    
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            config.ollama_url,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()
        data = response.json()
        return data['message']['content'].strip()
        
    except requests.exceptions.ConnectionError as e:
        raise LLMConnectionError(config.ollama_url, e)
    except requests.exceptions.Timeout:
        raise LLMTimeoutError(config.timeout)
    except requests.exceptions.HTTPError as e:
        raise LLMError(f"HTTP error: {e}")
    except Exception as e:
        raise LLMError(f"Unexpected error: {e}")
