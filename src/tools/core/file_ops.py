"""
Core tools for file operations, shell commands, and basic utilities
"""

import os
import subprocess
from typing import Optional

from .. import tool

@tool(
    description="List files in a directory",
    category="retrieval",
    schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The directory path to list files from",
                "default": "."
            }
        },
        "required": []
    }
)
def list_files(path: str = ".") -> str:
    """List files in a directory
    
    Args:
        path: The directory path to list files from
    
    Returns:
        Newline-separated list of files
    """
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

@tool(
    description="Read the contents of a file",
    category="retrieval",
    schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to read"
            }
        },
        "required": ["path"]
    }
)
def read_file(path: str) -> str:
    """Read the contents of a file
    
    Args:
        path: The file path to read
    
    Returns:
        The file contents as a string
    """
    try:
        with open(path, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"

@tool(
    description="Write content to a file",
    category="storage",
    schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path to write to"
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file"
            }
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str) -> str:
    """Write content to a file
    
    Args:
        path: The file path to write to
        content: The content to write to the file
    
    Returns:
        Success message or error description
    """
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote to {path} successfully."
    except Exception as e:
        return f"Error writing file: {e}"

@tool(
    description="Run a shell command and return its output",
    category="utility",
    schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            }
        },
        "required": ["command"]
    }
)
def run_shell(command: str) -> str:
    """Run a shell command and return its output
    
    Args:
        command: The shell command to execute
    
    Returns:
        Command output or error message
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if error:
            return f"[stderr]\n{error}\n[stdout]\n{output}"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 10 seconds"
    except Exception as e:
        return f"Error running shell command: {e}"

@tool(
    description="Search for a keyword in all files in the current directory",
    category="search",
    schema={
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "The keyword to search for"
            }
        },
        "required": ["keyword"]
    }
)
def search_files(keyword: str) -> str:
    """Search for a keyword in all files in the current directory
    
    Args:
        keyword: The keyword to search for
    
    Returns:
        Search results with file:line:content format
    """
    matches = []
    
    for root, _, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if keyword in line:
                            matches.append(f"{file_path}:{i}: {line.strip()}")
            except Exception:
                continue
    
    if matches:
        return "\n".join(matches)
    return f"No matches found for '{keyword}'."
