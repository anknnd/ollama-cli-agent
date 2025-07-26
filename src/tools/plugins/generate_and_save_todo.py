"""
Generate and save TODO list tool
"""

from src.core.config import get_config
from .. import tool
from ..shared import generate_content_with_llm


@tool(
    description="Generate a TODO list and save it to a file in one operation",
    category="combined",
    schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The description to generate a TODO list for"
            },
            "filename": {
                "type": "string", 
                "description": "The filename to save the TODO list to"
            }
        },
        "required": ["content", "filename"]
    }
)
def generate_and_save_todo(content: str, filename: str) -> str:
    """Generate a TODO list and save it to a file in one operation
    
    Args:
        content: The description to generate a TODO list for
        filename: The filename to save the TODO list to
    
    Returns:
        Success message with content preview
    """
    try:
        # Generate the todo using shared LLM function
        prompt = f"Generate a TODO list for: {content}\nFormat as a numbered list."
        generated_content = generate_content_with_llm(
            prompt, 
            "You are a helpful assistant that generates TODO lists."
        )
        
        # Save it to file
        with open(filename, "w") as f:
            f.write(generated_content)
            
        return f"Generated TODO list and saved to {filename} successfully.\n\nContent preview:\n{generated_content[:200]}..."
        
    except Exception as e:
        return f"Error in generate_and_save_todo: {e}"
