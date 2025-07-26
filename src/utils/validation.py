"""
System validation and health check utilities
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.config import get_config
from src.utils.logging import get_logger

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: bool
    message: str
    details: Optional[Dict] = None

class SystemValidator:
    """Validates system requirements and health"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
    
    def check_python_version(self) -> HealthCheckResult:
        """Check Python version requirements"""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            return HealthCheckResult(
                component="Python Version",
                status=True,
                message=f"Python {'.'.join(map(str, current_version))} (>= {'.'.join(map(str, min_version))})",
                details={"version": sys.version}
            )
        else:
            return HealthCheckResult(
                component="Python Version",
                status=False,
                message=f"Python {'.'.join(map(str, current_version))} < required {'.'.join(map(str, min_version))}",
                details={"version": sys.version}
            )
    
    def check_dependencies(self) -> HealthCheckResult:
        """Check required Python packages"""
        required_packages = {
            "requests": "2.31.0",
            "rich": "13.0.0", 
            "pyyaml": "6.0"
        }
        
        missing = []
        installed = {}
        version_issues = []
        
        for package, min_version in required_packages.items():
            try:
                # Import the package
                if package == "pyyaml":
                    import yaml as mod
                    package_name = "pyyaml"
                else:
                    mod = __import__(package)
                    package_name = package
                
                # Try to get version info
                try:
                    version = getattr(mod, '__version__', 'unknown')
                    installed[package_name] = version
                    
                    # Check version compatibility (basic check)
                    if version != 'unknown' and min_version:
                        try:
                            # Simple version comparison - convert to tuples
                            current_parts = [int(x) for x in version.split('.')[:3]]
                            min_parts = [int(x) for x in min_version.split('.')[:3]]
                            
                            # Pad shorter version with zeros
                            while len(current_parts) < 3:
                                current_parts.append(0)
                            while len(min_parts) < 3:
                                min_parts.append(0)
                            
                            if current_parts < min_parts:
                                version_issues.append(f"{package_name} {version} < {min_version}")
                        except (ValueError, AttributeError):
                            # If version parsing fails, assume it's okay
                            pass
                            
                except Exception:
                    installed[package_name] = 'installed'
                    
            except ImportError:
                missing.append(f"{package} >= {min_version}")
        
        # Determine overall status
        all_issues = missing + version_issues
        
        if not all_issues:
            return HealthCheckResult(
                component="Dependencies",
                status=True,
                message="All required packages installed",
                details={"installed": installed}
            )
        else:
            return HealthCheckResult(
                component="Dependencies", 
                status=False,
                message=f"Package issues: {', '.join(all_issues)}",
                details={"missing": missing, "version_issues": version_issues, "installed": installed}
            )
    
    def check_ollama_connection(self) -> HealthCheckResult:
        """Check Ollama service connection"""
        try:
            # Extract base URL from chat endpoint
            base_url = self.config.ollama_url.replace('/api/chat', '')
            tags_url = f"{base_url}/api/tags"
            
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [model.get('name', 'unknown') for model in models]
            
            # Check if configured model is available
            configured_model = self.config.model
            model_available = any(configured_model in name for name in model_names)
            
            if model_available:
                return HealthCheckResult(
                    component="Ollama Connection",
                    status=True,
                    message=f"Connected. Model '{configured_model}' available.",
                    details={
                        "endpoint": base_url,
                        "models": model_names,
                        "configured_model": configured_model
                    }
                )
            else:
                return HealthCheckResult(
                    component="Ollama Connection",
                    status=False,
                    message=f"Connected but model '{configured_model}' not found",
                    details={
                        "endpoint": base_url,
                        "models": model_names,
                        "configured_model": configured_model
                    }
                )
        
        except requests.exceptions.RequestException as e:
            return HealthCheckResult(
                component="Ollama Connection",
                status=False,
                message=f"Connection failed: {e}",
                details={"endpoint": self.config.ollama_url, "error": str(e)}
            )
    
    def check_directories(self) -> HealthCheckResult:
        """Check required directories exist and are writable"""
        dirs_to_check = [
            self.config.log_dir,
            self.config.sessions_dir,
            self.config.tool_dir if hasattr(self.config, 'tool_dir') else None
        ]
        
        issues = []
        checked_dirs = {}
        
        for dir_path in dirs_to_check:
            if dir_path is None:
                continue
                
            path = Path(dir_path)
            
            # Check if exists
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    checked_dirs[str(path)] = "created"
                except OSError as e:
                    issues.append(f"Cannot create {dir_path}: {e}")
                    continue
            
            # Check if writable
            if not os.access(path, os.W_OK):
                issues.append(f"Directory {dir_path} is not writable")
            else:
                checked_dirs[str(path)] = "writable"
        
        if not issues:
            return HealthCheckResult(
                component="Directories",
                status=True,
                message="All directories accessible",
                details={"directories": checked_dirs}
            )
        else:
            return HealthCheckResult(
                component="Directories",
                status=False,
                message=f"Directory issues: {'; '.join(issues)}",
                details={"directories": checked_dirs, "issues": issues}
            )
    
    def check_configuration(self) -> HealthCheckResult:
        """Validate configuration settings"""
        issues = []
        config_info = {}
        
        # Check critical settings
        if not self.config.ollama_url:
            issues.append("ollama_url not configured")
        else:
            config_info["ollama_url"] = self.config.ollama_url
        
        if not self.config.model:
            issues.append("model not configured")
        else:
            config_info["model"] = self.config.model
        
        # Check numeric settings
        if self.config.timeout <= 0:
            issues.append("timeout must be positive")
        else:
            config_info["timeout"] = self.config.timeout
        
        if self.config.max_history <= 0:
            issues.append("max_history must be positive")
        else:
            config_info["max_history"] = self.config.max_history
        
        # Check config file exists
        config_file = Path.cwd() / ".agentrc"
        config_info["config_file_exists"] = config_file.exists()
        
        if not issues:
            return HealthCheckResult(
                component="Configuration",
                status=True,
                message="Configuration valid",
                details=config_info
            )
        else:
            return HealthCheckResult(
                component="Configuration",
                status=False,
                message=f"Configuration issues: {'; '.join(issues)}",
                details={"issues": issues, "config": config_info}
            )
    
    def run_full_health_check(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        checks = [
            self.check_python_version,
            self.check_dependencies,
            self.check_configuration,
            self.check_directories,
            self.check_ollama_connection,
        ]
        
        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(HealthCheckResult(
                    component=check.__name__.replace('check_', '').title(),
                    status=False,
                    message=f"Health check failed: {e}",
                    details={"error": str(e)}
                ))
        
        return results
    
    def print_health_report(self, results: Optional[List[HealthCheckResult]] = None) -> bool:
        """Print formatted health check report"""
        if results is None:
            results = self.run_full_health_check()
        
        all_passed = all(result.status for result in results)
        
        # Print header
        status_emoji = "✅" if all_passed else "❌"
        self.logger.print_message(f"\n{status_emoji} System Health Check Report")
        self.logger.print_message("=" * 50)
        
        # Print individual results
        for result in results:
            status_emoji = "✅" if result.status else "❌"
            self.logger.print_message(f"{status_emoji} {result.component}: {result.message}")
            
            if result.details and self.config.verbosity == "debug":
                self.logger.print_message(f"   Details: {result.details}")
        
        # Print summary
        passed_count = sum(1 for r in results if r.status)
        total_count = len(results)
        
        self.logger.print_message("=" * 50)
        self.logger.print_message(f"Summary: {passed_count}/{total_count} checks passed")
        
        if not all_passed:
            self.logger.print_message("\n🔧 Suggested fixes:")
            for result in results:
                if not result.status:
                    self.logger.print_message(f"   • {result.component}: {self._get_fix_suggestion(result)}")
        
        return all_passed
    
    def _get_fix_suggestion(self, result: HealthCheckResult) -> str:
        """Get suggested fix for failed health check"""
        component = result.component.lower()
        
        suggestions = {
            "python version": "Upgrade Python to 3.8 or higher",
            "dependencies": "Run: pip install -r requirements.txt",
            "ollama connection": "Start Ollama with: ollama serve",
            "directories": "Check directory permissions and disk space",
            "configuration": "Review and fix .agentrc configuration file"
        }
        
        return suggestions.get(component, "Check the documentation for troubleshooting")

def run_system_diagnostics() -> bool:
    """Quick function to run system diagnostics"""
    validator = SystemValidator()
    return validator.print_health_report()
