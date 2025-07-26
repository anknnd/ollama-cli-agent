"""
Tool system infrastructure and registry
"""

import os
import importlib.util
import glob
from typing import Dict, Callable, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from src.core.config import get_config
from src.core.exceptions import ToolError, ToolNotFoundError, ToolValidationError
from src.utils.logging import get_logger

@dataclass
class ToolInfo:
    """Information about a registered tool"""
    name: str
    function: Callable
    description: str
    category: str
    schema: Dict[str, Any]

class ToolRegistry:
    """Centralized tool registry with discovery and validation"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self._tools: Dict[str, Callable] = {}
        self._tool_info: Dict[str, ToolInfo] = {}
        self._loaded_plugins: List[str] = []
    
    def register_tool(self, name: str, function: Callable, description: str = None, 
                     category: str = None, schema: Dict[str, Any] = None):
        """Register a tool with the registry"""
        if name in self._tools:
            self.logger.warning(f"Tool '{name}' already registered, overwriting")
        
        # Auto-generate description if not provided
        if description is None:
            description = function.__doc__ or f"{name}()"
        
        # Auto-categorize if not provided
        if category is None:
            category = self._auto_categorize(name)
        
        # Auto-generate schema if not provided
        if schema is None:
            schema = self._auto_generate_schema(function)
        
        # Register tool
        self._tools[name] = function
        self._tool_info[name] = ToolInfo(
            name=name,
            function=function,
            description=description,
            category=category,
            schema=schema
        )
        
        self.logger.debug(f"Registered tool '{name}' in category '{category}'")
    
    def _auto_categorize(self, name: str) -> str:
        """Auto-categorize tool based on naming patterns"""
        name_lower = name.lower()
        
        if 'generate' in name_lower:
            return 'generation'
        elif any(word in name_lower for word in ['save', 'write', 'store']):
            return 'storage'
        elif any(word in name_lower for word in ['search', 'find', 'query']):
            return 'search'
        elif any(word in name_lower for word in ['read', 'list', 'get', 'fetch']):
            return 'retrieval'
        elif any(word in name_lower for word in ['email', 'send', 'message']):
            return 'communication'
        elif '_and_' in name_lower:
            return 'combined'
        elif any(word in name_lower for word in ['calculate', 'math', 'compute']):
            return 'calculation'
        elif any(word in name_lower for word in ['password', 'encrypt', 'hash']):
            return 'security'
        else:
            return 'utility'
    
    def _auto_generate_schema(self, function: Callable) -> Dict[str, Any]:
        """Auto-generate OpenAPI schema from function signature"""
        import inspect
        
        sig = inspect.signature(function)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            
            # Default type is string
            param_schema = {"type": "string"}
            
            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_schema["type"] = "integer"
                elif param.annotation == float:
                    param_schema["type"] = "number"
                elif param.annotation == bool:
                    param_schema["type"] = "boolean"
                elif param.annotation == list:
                    param_schema["type"] = "array"
                elif param.annotation == dict:
                    param_schema["type"] = "object"
            
            # Add description from docstring if available
            if function.__doc__:
                # Simple heuristic to extract parameter descriptions
                doc_lines = function.__doc__.split('\n')
                for line in doc_lines:
                    if param_name in line and ':' in line:
                        desc = line.split(':', 1)[1].strip()
                        if desc:
                            param_schema["description"] = desc
                        break
            
            properties[param_name] = param_schema
            
            # Required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def get_tool(self, name: str) -> Callable:
        """Get a tool by name"""
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool with validation"""
        if name not in self._tools:
            raise ToolNotFoundError(name)
        
        try:
            # TODO: Add schema validation here
            result = self._tools[name](**kwargs)
            return result
        except TypeError as e:
            raise ToolValidationError(name, str(e))
        except Exception as e:
            raise ToolError(f"Tool '{name}' execution failed: {e}")
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
    
    def get_tools_by_category(self) -> Dict[str, List[ToolInfo]]:
        """Get tools organized by category"""
        categories = {}
        for tool_info in self._tool_info.values():
            if tool_info.category not in categories:
                categories[tool_info.category] = []
            categories[tool_info.category].append(tool_info)
        return categories
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get tool descriptions for legacy compatibility"""
        return {name: info.description for name, info in self._tool_info.items()}
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Generate tools schema for LLM API"""
        tools = []
        for tool_info in self._tool_info.values():
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_info.name,
                    "description": tool_info.description,
                    "parameters": tool_info.schema
                }
            }
            tools.append(tool_def)
        return tools
    
    def load_plugins(self, plugin_dir: str = None):
        """Load plugins from directory"""
        if plugin_dir is None:
            plugin_dir = self.config.tool_dir
        
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            self.logger.warning(f"Plugin directory '{plugin_dir}' does not exist")
            return
        
        # Load Python files as plugins
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith('__'):
                continue
            
            self._load_plugin_file(plugin_file)
    
    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file"""
        try:
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                
                # Execute module to register tools
                spec.loader.exec_module(module)
                
                self._loaded_plugins.append(str(plugin_file))
                self.logger.debug(f"Loaded plugin: {plugin_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_file}: {e}")

# Global registry instance
_registry: Optional[ToolRegistry] = None

def get_registry() -> ToolRegistry:
    """Get the global tool registry"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

def tool(fn=None, *, description=None, category=None, schema=None):
    """Decorator for registering tools"""
    def decorator(f):
        registry = get_registry()
        registry.register_tool(
            name=f.__name__,
            function=f,
            description=description,
            category=category,
            schema=schema
        )
        return f
    
    if fn is None:
        return decorator
    return decorator(fn)

# Compatibility functions for existing code
def get_tools() -> Dict[str, Callable]:
    """Get all tools for legacy compatibility"""
    registry = get_registry()
    return registry._tools

def get_tool_descriptions() -> Dict[str, str]:
    """Get tool descriptions for legacy compatibility"""
    registry = get_registry()
    return registry.get_tool_descriptions()

def get_tools_schema() -> List[Dict[str, Any]]:
    """Get tools schema for legacy compatibility"""
    registry = get_registry()
    return registry.get_tools_schema()

def get_categorized_tools() -> Dict[str, List[Dict[str, str]]]:
    """Get categorized tools for legacy compatibility"""
    registry = get_registry()
    categories = registry.get_tools_by_category()
    
    # Convert to legacy format
    result = {}
    for category, tools in categories.items():
        result[category] = [
            {"name": tool.name, "description": tool.description}
            for tool in tools
        ]
    return result

def generate_tool_selection_strategy() -> str:
    """Generate tool selection strategy for legacy compatibility"""
    categories = get_categorized_tools()
    
    strategy_parts = []
    
    # Generation tools
    if 'generation' in categories:
        gen_tools = [t['name'] for t in categories['generation']]
        strategy_parts.append(f"- For content generation only: {', '.join(gen_tools)}")
    
    # Storage tools
    if 'storage' in categories:
        storage_tools = [t['name'] for t in categories['storage']]
        strategy_parts.append(f"- For saving/writing content: {', '.join(storage_tools)}")
    
    # Combined operation tools
    if 'combined' in categories:
        combined_tools = [t['name'] for t in categories['combined']]
        strategy_parts.append(f"- For combined operations (generate + save, search + save, etc.): {', '.join(combined_tools)}")
        strategy_parts.append("- **Prefer combined tools when user wants multiple operations** - they are more reliable")
    
    # Search tools
    if 'search' in categories:
        search_tools = [t['name'] for t in categories['search']]
        strategy_parts.append(f"- For searching: {', '.join(search_tools)}")
    
    # Communication tools
    if 'communication' in categories:
        comm_tools = [t['name'] for t in categories['communication']]
        strategy_parts.append(f"- For communication (email, messaging): {', '.join(comm_tools)}")
    
    return "\n".join(strategy_parts)
