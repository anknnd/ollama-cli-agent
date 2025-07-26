"""
Chat agent with separated responsibilities
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.config import get_config
from src.core.exceptions import ToolError, LLMError, ToolNotFoundError
from src.llm.client import get_client, ChatMessage
from src.utils.logging import get_logger

class PromptBuilder:
    """Handles system prompt generation"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
    
    def build_system_prompt(self) -> str:
        """Build dynamic system prompt based on available tools"""
        try:
            # Import here to avoid circular imports
            from src.tools import get_registry
            
            registry = get_registry()
            categories = registry.get_tools_by_category()
            
            # Build tool list organized by category
            tool_sections = []
            for category, tool_infos in sorted(categories.items()):
                category_title = category.replace('_', ' ').title()
                tool_list = "\n".join(f"  - {tool_info.name}: {tool_info.description}" for tool_info in tool_infos)
                tool_sections.append(f"**{category_title} Tools:**\n{tool_list}")
            
            tool_overview = "\n\n".join(tool_sections)
            
            return f"""You are an AI assistant with access to tools organized by category:

{tool_overview}

CORE PRINCIPLES:
- When users request actions that require tools, select and use the appropriate tools
- Tool results are the source of truth - never fabricate information
- If a tool fails, explain the error clearly to the user
- Maintain conversation context and topic awareness

TOOL SELECTION STRATEGY:
- Use the most appropriate tool for each task
- Prefer combined tools for multi-step operations
- Use specific tools for focused tasks

OPERATION GUIDELINES:
- **Single operations**: Use individual tools for simple tasks
- **Multiple operations**: Prefer combined tools when available (more reliable)
- **File operations**: Use current directory '.' when path not specified
- **Content handling**: Use exact content from tool results when saving files

RESPONSE STYLE:
- Interpret tool outputs clearly in natural language
- Summarize what was accomplished
- Suggest logical next steps when appropriate
- Be concise and friendly
- Format responses suitable for CLI output unless specified otherwise

Choose tools based on what the user actually requests, not assumptions."""
            
        except Exception as e:
            self.logger.error("Failed to build system prompt", error=str(e))
            # Fallback to basic prompt
            return "You are a helpful AI assistant with access to tools. Use tools when needed and provide clear responses."

class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.history: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add message to history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add optional fields
        for key, value in kwargs.items():
            if value is not None:
                message[key] = value
        
        self.history.append(message)
        
        # Trim history if too long
        if len(self.history) > self.config.max_history * 2:  # Keep some buffer
            # Keep system message and recent messages
            system_msgs = [msg for msg in self.history if msg.get('role') == 'system']
            recent_msgs = self.history[-self.config.max_history:]
            self.history = system_msgs + recent_msgs
    
    def get_context_messages(self, system_prompt: str) -> List[Dict[str, Any]]:
        """Get messages for LLM context"""
        context = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history
        for msg in self.history[-self.config.max_history:]:
            if msg["role"] in ["user", "assistant", "tool"]:
                context_msg = {"role": msg["role"], "content": msg["content"]}
                
                # Add tool-specific fields
                if "tool_calls" in msg:
                    context_msg["tool_calls"] = msg["tool_calls"]
                if "tool_name" in msg:
                    context_msg["tool_name"] = msg["tool_name"]
                
                context.append(context_msg)
        
        return context
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.history.clear()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.history.copy()

class ChatAgent:
    """Main chat agent with focused responsibilities"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        
        # Initialize components
        self.llm_client = get_client()
        self.prompt_builder = PromptBuilder()
        self.conversation = ConversationManager()
    
    def process_message(self, user_input: str) -> Optional[str]:
        """Process a user message and return response"""
        try:
            # Add user message to history
            self.conversation.add_message("user", user_input)
            
            # Build context for LLM
            system_prompt = self.prompt_builder.build_system_prompt()
            context_messages = self.conversation.get_context_messages(system_prompt)
            
            self.logger.info("Processing user message", length=len(user_input))
            
            # Get tools schema for LLM
            from src.tools import get_tools_schema
            tools_schema = get_tools_schema()
            
            # Call LLM
            response = self.llm_client.chat(context_messages, tools_schema)
            self.logger.print_timing("LLM response", response.timing)
            
            # Handle tool calls if any
            if response.message.tool_calls:
                return self._handle_tool_calls(response, context_messages, tools_schema)
            else:
                # No tool calls, just add response to history
                self.conversation.add_message("assistant", response.message.content)
                self.logger.print_message(f"Assistant: {response.message.content}")
                return response.message.content
                
        except LLMError as e:
            error_msg = f"LLM Error: {e}"
            self.logger.error(error_msg)
            self.conversation.add_message("error", error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.conversation.add_message("error", error_msg)
            return error_msg
    
    def _handle_tool_calls(self, response, context_messages, tools_schema) -> str:
        """Handle tool calls and get final response"""
        tool_calls = response.message.tool_calls
        
        # Add assistant message with tool calls to history
        self.conversation.add_message(
            "assistant", 
            response.message.content,
            tool_calls=tool_calls
        )
        
        self.logger.info(f"Executing {len(tool_calls)} tool(s)")
        
        # Execute tools
        tool_results = self._execute_tools(tool_calls)
        
        # Add tool results to context and conversation
        for result in tool_results:
            context_messages.append(result)
            self.conversation.add_message(
                "tool", 
                result['content'], 
                tool_name=result['tool_name']
            )
        
        # Get final response from LLM
        final_response = self.llm_client.chat(context_messages)
        self.logger.print_timing("Final response", final_response.timing)
        
        # Check for additional tool calls (chaining)
        if final_response.message.tool_calls:
            self.logger.info("Additional tool calls detected")
            return self._handle_tool_calls(final_response, context_messages, tools_schema)
        else:
            # Add final response to history
            self.conversation.add_message("assistant", final_response.message.content)
            self.logger.print_message(f"Assistant: {final_response.message.content}")
            return final_response.message.content
    
    def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """Execute tool calls safely"""
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                function_data = tool_call.get('function', {})
                tool_name = function_data.get('name')
                arguments = function_data.get('arguments', {})
                
                if not tool_name:
                    raise ToolError("Missing tool name in tool call")
                
                # Get the tool registry
                from src.tools import get_registry
                registry = get_registry()
                
                self.logger.print_tool_call(tool_name, arguments)
                
                # Execute tool with timeout
                start_time = time.time()
                try:
                    result = registry.execute_tool(tool_name, **arguments)
                except ToolNotFoundError:
                    raise ToolError(f"Tool '{tool_name}' not found")
                duration = time.time() - start_time
                
                self.logger.print_tool_result(tool_name, str(result), True)
                self.logger.print_timing(f"Tool {tool_name}", duration)
                
                results.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_name": tool_name
                })
                
            except Exception as e:
                error_msg = f"Tool execution failed: {e}"
                self.logger.print_tool_result(tool_name or "unknown", error_msg, False)
                
                results.append({
                    "role": "tool",
                    "content": error_msg,
                    "tool_name": tool_name or "unknown"
                })
        
        return results
    
    def load_history(self, history: List[Dict[str, Any]]) -> None:
        """Load conversation history"""
        self.conversation.history = history.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation.get_history()
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation.clear_history()
