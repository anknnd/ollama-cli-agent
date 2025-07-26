"""
Content generation tools
"""

import requests
from ...core.config import get_config
from .. import tool

@tool(
    description="Generate a TODO list from a description",
    category="generation",
    schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The description to generate a TODO list for"
            }
        },
        "required": ["content"]
    }
)
def generate_todo(content: str) -> str:
    """Generate a TODO list from a description
    
    Args:
        content: The description to generate a TODO list for
    
    Returns:
        Generated TODO list as text
    """
    config = get_config()
    ollama_url = config.ollama_url
    model = config.model
    
    prompt = f"Generate a TODO list for: {content}\nFormat as a numbered list."
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates TODO lists."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=config.timeout)
        response.raise_for_status()
        data = response.json()
        return data['message']['content'].strip()
    except Exception as e:
        return f"Error generating TODO list: {e}"
