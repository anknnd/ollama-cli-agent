"""
Communication tools for email and messaging
"""

from .. import tool

@tool(
    description="Mock sending an email",
    category="communication",
    schema={
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "The recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "The email subject"
            },
            "content": {
                "type": "string",
                "description": "The email content"
            }
        },
        "required": ["to", "subject", "content"]
    }
)
def send_email(to: str, subject: str, content: str) -> str:
    """Mock sending an email
    
    Args:
        to: The recipient email address
        subject: The email subject
        content: The email content
    
    Returns:
        Mock email confirmation
    """
    return f"[MOCK EMAIL]\nTo: {to}\nSubject: {subject}\nContent: {content}\n(Email not actually sent.)"
