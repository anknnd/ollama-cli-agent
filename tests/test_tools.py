"""
Tests for tool registry and management
"""

import pytest
from unittest.mock import Mock

from src.tools import ToolRegistry, tool
from src.core.exceptions import ToolNotFoundError, ToolValidationError

class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_register_tool_basic(self, tool_registry):
        """Test basic tool registration"""
        def test_tool(arg1: str) -> str:
            """Test tool description"""
            return f"Result: {arg1}"
        
        tool_registry.register_tool(
            name="test_tool",
            function=test_tool,
            description="A test tool",
            category="test"
        )
        
        assert "test_tool" in tool_registry.list_tools()
        assert tool_registry.get_tool("test_tool") == test_tool
    
    def test_auto_categorization(self, tool_registry):
        """Test automatic tool categorization"""
        def generate_content():
            return "content"
        
        def save_file():
            return "saved"
        
        def search_data():
            return "found"
        
        tool_registry.register_tool("generate_content", generate_content)
        tool_registry.register_tool("save_file", save_file)
        tool_registry.register_tool("search_data", search_data)
        
        categories = tool_registry.get_tools_by_category()
        
        assert any(tool.name == "generate_content" for tool in categories["generation"])
        assert any(tool.name == "save_file" for tool in categories["storage"])
        assert any(tool.name == "search_data" for tool in categories["search"])
    
    def test_auto_schema_generation(self, tool_registry):
        """Test automatic schema generation from function signature"""
        def test_func(required_arg: str, optional_arg: int = 10) -> str:
            return f"{required_arg}-{optional_arg}"
        
        tool_registry.register_tool("test_func", test_func)
        
        schema = tool_registry._tool_info["test_func"].schema
        
        assert schema["type"] == "object"
        assert "required_arg" in schema["properties"]
        assert "optional_arg" in schema["properties"]
        assert schema["properties"]["required_arg"]["type"] == "string"
        assert schema["properties"]["optional_arg"]["type"] == "integer"
        assert "required_arg" in schema["required"]
        assert "optional_arg" not in schema["required"]
    
    def test_execute_tool_success(self, tool_registry):
        """Test successful tool execution"""
        def add_numbers(a: int, b: int) -> int:
            return int(a) + int(b)
        
        tool_registry.register_tool("add_numbers", add_numbers)
        
        result = tool_registry.execute_tool("add_numbers", a="5", b="3")
        assert result == 8
    
    def test_execute_tool_not_found(self, tool_registry):
        """Test tool execution with non-existent tool"""
        with pytest.raises(ToolNotFoundError):
            tool_registry.execute_tool("nonexistent_tool")
    
    def test_execute_tool_validation_error(self, tool_registry):
        """Test tool execution with invalid arguments"""
        def test_tool(required_arg: str) -> str:
            return required_arg
        
        tool_registry.register_tool("test_tool", test_tool)
        
        with pytest.raises(ToolValidationError):
            tool_registry.execute_tool("test_tool")  # Missing required argument
    
    def test_get_tools_schema(self, tool_registry):
        """Test OpenAPI schema generation"""
        def test_tool(arg: str) -> str:
            """Test tool for schema"""
            return arg
        
        tool_registry.register_tool(
            "test_tool", 
            test_tool, 
            description="Test description"
        )
        
        schema = tool_registry.get_tools_schema()
        
        assert len(schema) == 1
        assert schema[0]["type"] == "function"
        assert schema[0]["function"]["name"] == "test_tool"
        assert schema[0]["function"]["description"] == "Test description"
        assert "parameters" in schema[0]["function"]
    
    def test_tool_decorator(self, tool_registry):
        """Test tool decorator functionality"""
        # Clear any existing tools
        tool_registry._tools.clear()
        tool_registry._tool_info.clear()
        
        @tool(description="Decorated test tool", category="test")
        def decorated_tool(value: str) -> str:
            return f"Decorated: {value}"
        
        # Tool should be automatically registered
        assert "decorated_tool" in tool_registry.list_tools()
        
        result = tool_registry.execute_tool("decorated_tool", value="test")
        assert result == "Decorated: test"
    
    def test_get_tools_by_category(self, tool_registry):
        """Test getting tools organized by category"""
        def gen_tool():
            return "generated"
        
        def storage_tool():
            return "stored"
        
        tool_registry.register_tool("gen_tool", gen_tool, category="generation")
        tool_registry.register_tool("storage_tool", storage_tool, category="storage")
        
        categories = tool_registry.get_tools_by_category()
        
        assert "generation" in categories
        assert "storage" in categories
        assert len(categories["generation"]) == 1
        assert len(categories["storage"]) == 1
        assert categories["generation"][0].name == "gen_tool"
        assert categories["storage"][0].name == "storage_tool"
