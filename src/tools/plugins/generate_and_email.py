"""
Generate content and send mock email tool
"""

from .. import tool
from ..shared import generate_content_with_llm


@tool(
    description="Generate content based on a prompt and send it as a mock email",
    category="combined",
    schema={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic to generate content for"
            },
            "to": {
                "type": "string",
                "description": "The recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "The email subject line"
            }
        },
        "required": ["topic", "to", "subject"]
    }
)
def generate_and_email(topic: str, to: str, subject: str) -> str:
    """Generate content and send it as a mock email
    
    Args:
        topic: The topic to generate content for
        to: The recipient email address
        subject: The email subject line
    
    Returns:
        Mock email confirmation
    """
    try:
        # Generate content using shared LLM function
        prompt = f"Generate appropriate content for: {topic}"
        generated_content = generate_content_with_llm(
            prompt,
            "You are a helpful assistant that generates content for emails."
        )
        
        # Create mock email
        email_result = f"[MOCK EMAIL]\nTo: {to}\nSubject: {subject}\nContent: {generated_content}\n(Email not actually sent.)"
        
        return f"Generated content and sent mock email to {to}.\n\n{email_result}"
        
    except Exception as e:
        return f"Error generating content for email: {e}"
