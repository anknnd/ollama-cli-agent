"""
Enhanced tool loader with automatic discovery
"""

import importlib
from pathlib import Path
from typing import Dict, List
import sys

from src.core.config import get_config
from src.utils.logging import get_logger
from . import get_registry

class ToolLoader:
    """Advanced tool loader with automatic discovery"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.registry = get_registry()
    
    def load_all_tools(self) -> None:
        """Load all tools from core and plugins"""
        self.load_core_tools()
        self.load_plugins()
        self.load_legacy_plugins()
    
    def load_core_tools(self) -> None:
        """Load core tools from src/tools/core"""
        try:
            core_path = Path(__file__).parent / "core"
            if core_path.exists():
                self._load_modules_from_path(core_path, "src.tools.core")
        except Exception as e:
            self.logger.error(f"Failed to load core tools: {e}")
    
    def load_plugins(self) -> None:
        """Load plugins from src/tools/plugins"""
        try:
            plugins_path = Path(__file__).parent / "plugins" 
            if plugins_path.exists():
                self._load_modules_from_path(plugins_path, "src.tools.plugins")
        except Exception as e:
            self.logger.error(f"Failed to load new plugins: {e}")
    
    def load_legacy_plugins(self) -> None:
        """Load legacy plugins from root plugins directory"""
        try:
            legacy_path = Path.cwd() / self.config.tool_dir
            if legacy_path.exists():
                self._load_legacy_modules_from_path(legacy_path)
        except Exception as e:
            self.logger.error(f"Failed to load legacy plugins: {e}")
    
    def _load_modules_from_path(self, path: Path, package: str) -> None:
        """Load Python modules from a path"""
        for module_file in path.glob("*.py"):
            if module_file.name.startswith("__"):
                continue
            
            module_name = module_file.stem
            try:
                # Import module to trigger tool registration
                full_module_name = f"{package}.{module_name}"
                importlib.import_module(full_module_name)
                self.logger.debug(f"Loaded module: {full_module_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load module {module_file}: {e}")
    
    def _load_legacy_modules_from_path(self, path: Path) -> None:
        """Load legacy modules using spec loading"""
        for module_file in path.glob("*.py"):
            if module_file.name.startswith("__"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    module_file.stem, 
                    module_file
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add to sys.modules for imports to work
                    sys.modules[spec.name] = module
                    
                    spec.loader.exec_module(module)
                    self.logger.debug(f"Loaded legacy plugin: {module_file}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load legacy plugin {module_file}: {e}")
    
    def get_tool_summary(self) -> Dict[str, any]:
        """Get summary of loaded tools"""
        tools = self.registry.list_tools()
        categories = self.registry.get_tools_by_category()
        
        summary = {
            "total_tools": len(tools),
            "tools_by_category": {
                cat: len(tools) for cat, tools in categories.items()
            },
            "tool_names": sorted(tools)
        }
        
        return summary

def load_all_tools() -> Dict[str, any]:
    """Load all tools and return summary"""
    loader = ToolLoader()
    loader.load_all_tools()
    return loader.get_tool_summary()
