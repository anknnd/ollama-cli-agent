"""
Data models for requests, responses, and conversation management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

class MessageRole(Enum):
    """Message roles in conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ToolCallStatus(Enum):
    """Status of tool call execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class ToolCall:
    """Represents a tool call request"""
    id: str
    function_name: str
    arguments: Dict[str, Any]
    status: ToolCallStatus = ToolCallStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility"""
        return {
            "id": self.id,
            "function": {
                "name": self.function_name,
                "arguments": self.arguments
            }
        }

@dataclass
class ToolResult:
    """Represents the result of a tool execution"""
    tool_call_id: str
    tool_name: str
    content: str
    success: bool = True
    execution_time: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility"""
        return {
            "role": "tool",
            "content": self.content,
            "tool_name": self.tool_name
        }

@dataclass
class Message:
    """Represents a conversation message"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility"""
        result = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        
        if self.tool_results:
            result["tool_results"] = [tr.to_dict() for tr in self.tool_results]
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        role = MessageRole(data["role"])
        content = data["content"]
        timestamp = datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat()))
        
        # Parse tool calls
        tool_calls = []
        if "tool_calls" in data:
            for tc_data in data["tool_calls"]:
                tool_call = ToolCall(
                    id=tc_data.get("id", ""),
                    function_name=tc_data["function"]["name"],
                    arguments=tc_data["function"]["arguments"]
                )
                tool_calls.append(tool_call)
        
        # Parse tool results
        tool_results = []
        if "tool_results" in data:
            for tr_data in data["tool_results"]:
                tool_result = ToolResult(
                    tool_call_id="",  # Legacy compatibility
                    tool_name=tr_data.get("tool_name", ""),
                    content=tr_data["content"]
                )
                tool_results.append(tool_result)
        
        return cls(
            role=role,
            content=content,
            timestamp=timestamp,
            tool_calls=tool_calls,
            tool_results=tool_results,
            metadata=data.get("metadata", {})
        )

@dataclass
class Conversation:
    """Represents a conversation with messages and metadata"""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages up to limit"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def get_context_for_llm(self, system_prompt: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get messages formatted for LLM API"""
        context = []
        
        if system_prompt:
            context.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add recent messages
        recent_messages = self.get_recent_messages(limit)
        for message in recent_messages:
            msg_dict = {
                "role": message.role.value,
                "content": message.content
            }
            
            # Add tool calls if present
            if message.tool_calls:
                msg_dict["tool_calls"] = [tc.to_dict() for tc in message.tool_calls]
            
            context.append(msg_dict)
            
            # Add tool results as separate messages
            for tool_result in message.tool_results:
                context.append(tool_result.to_dict())
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary"""
        messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]
        
        return cls(
            id=data["id"],
            messages=messages,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            metadata=data.get("metadata", {})
        )

@dataclass
class LLMRequest:
    """Represents a request to the LLM"""
    messages: List[Dict[str, Any]]
    model: str
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        result = {
            "model": self.model,
            "messages": self.messages,
            "stream": self.stream,
            "temperature": self.temperature
        }
        
        if self.tools:
            result["tools"] = self.tools
        
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
        
        return result

@dataclass
class LLMResponse:
    """Represents a response from the LLM"""
    message: Message
    model: str
    timing: float
    total_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any], timing: float) -> 'LLMResponse':
        """Create from API response data"""
        message_data = data["message"]
        
        # Parse tool calls from API response
        tool_calls = []
        if "tool_calls" in message_data:
            for tc_data in message_data["tool_calls"]:
                tool_call = ToolCall(
                    id=tc_data.get("id", ""),
                    function_name=tc_data["function"]["name"],
                    arguments=tc_data["function"]["arguments"]
                )
                tool_calls.append(tool_call)
        
        message = Message(
            role=MessageRole(message_data["role"]),
            content=message_data.get("content", ""),
            tool_calls=tool_calls
        )
        
        return cls(
            message=message,
            model=data.get("model", "unknown"),
            timing=timing,
            total_tokens=data.get("total_tokens"),
            prompt_tokens=data.get("prompt_tokens"),
            completion_tokens=data.get("completion_tokens")
        )
