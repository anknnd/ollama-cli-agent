"""
Custom exception classes for Ollama CLI
"""

class OllamaCliError(Exception):
    """Base exception for all Ollama CLI errors"""
    pass

class ConfigurationError(OllamaCliError):
    """Raised when there's a configuration issue"""
    pass

class LLMError(OllamaCliError):
    """Base class for LLM-related errors"""
    pass

class LLMConnectionError(LLMError):
    """Raised when cannot connect to LLM service"""
    def __init__(self, url: str, original_error: Exception = None):
        self.url = url
        self.original_error = original_error
        super().__init__(f"Cannot connect to LLM at {url}: {original_error}")

class LLMTimeoutError(LLMError):
    """Raised when LLM request times out"""
    def __init__(self, timeout: int):
        self.timeout = timeout
        super().__init__(f"LLM request timed out after {timeout} seconds")

class LLMResponseError(LLMError):
    """Raised when LLM returns invalid response"""
    def __init__(self, message: str, response_data: dict = None):
        self.response_data = response_data
        super().__init__(message)

class ToolError(OllamaCliError):
    """Base class for tool-related errors"""
    pass

class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found"""
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found")

class ToolExecutionError(ToolError):
    """Raised when tool execution fails"""
    def __init__(self, tool_name: str, error_message: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.error_message = error_message
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {error_message}")

class ToolTimeoutError(ToolError):
    """Raised when tool execution times out"""
    def __init__(self, tool_name: str, timeout: int):
        self.tool_name = tool_name
        self.timeout = timeout
        super().__init__(f"Tool '{tool_name}' timed out after {timeout} seconds")

class ToolValidationError(ToolError):
    """Raised when tool arguments are invalid"""
    def __init__(self, tool_name: str, validation_message: str):
        self.tool_name = tool_name
        self.validation_message = validation_message
        super().__init__(f"Tool '{tool_name}' validation failed: {validation_message}")

class ConversationError(OllamaCliError):
    """Base class for conversation-related errors"""
    pass

class HistoryError(ConversationError):
    """Raised when there's an issue with conversation history"""
    pass

class SessionError(ConversationError):
    """Raised when there's an issue with session management"""
    pass
