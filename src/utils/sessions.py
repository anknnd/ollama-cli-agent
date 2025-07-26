"""
Session management utilities for saving and loading conversation sessions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.config import get_config
from .logging import get_logger


class SessionManager:
    """Manages conversation sessions with proper file handling"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.sessions_dir = Path(self.config.sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def get_session_filename(self) -> str:
        """Generate a timestamped session filename"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"session-{timestamp}.json"
    
    def save_session(self, session_file: str, conversation_history: List[Dict[str, Any]]) -> None:
        """Save conversation history to a session file
        
        Args:
            session_file: Name of the session file
            conversation_history: List of conversation messages
        """
        try:
            session_path = self.sessions_dir / session_file
            
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "conversation": conversation_history,
                "metadata": {
                    "model": self.config.model,
                    "total_messages": len(conversation_history)
                }
            }
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug(f"Session saved to {session_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session to {session_file}: {e}")
            raise
    
    def load_session(self, session_file: str) -> List[Dict[str, Any]]:
        """Load conversation history from a session file
        
        Args:
            session_file: Name of the session file
            
        Returns:
            List of conversation messages
        """
        try:
            session_path = self.sessions_dir / session_file
            
            if not session_path.exists():
                raise FileNotFoundError(f"Session file not found: {session_path}")
            
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Handle both old and new session formats
            if "conversation" in session_data:
                conversation = session_data["conversation"]
            else:
                # Legacy format - assume the whole file is the conversation
                conversation = session_data
            
            self.logger.debug(f"Session loaded from {session_path}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Failed to load session from {session_file}: {e}")
            raise
    
    def list_sessions(self) -> List[str]:
        """List all available session files
        
        Returns:
            List of session filenames
        """
        try:
            session_files = []
            for file_path in self.sessions_dir.glob("*.json"):
                session_files.append(file_path.name)
            
            return sorted(session_files, reverse=True)  # Most recent first
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []
    
    def get_session_info(self, session_file: str) -> Optional[Dict[str, Any]]:
        """Get metadata about a session file
        
        Args:
            session_file: Name of the session file
            
        Returns:
            Session metadata or None if error
        """
        try:
            session_path = self.sessions_dir / session_file
            
            if not session_path.exists():
                return None
            
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Extract metadata
            if "metadata" in session_data:
                metadata = session_data["metadata"]
            else:
                # Generate metadata for legacy format
                conversation = session_data.get("conversation", session_data)
                metadata = {
                    "total_messages": len(conversation) if isinstance(conversation, list) else 0
                }
            
            # Add file info
            stat = session_path.stat()
            metadata.update({
                "file_size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "filename": session_file
            })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get session info for {session_file}: {e}")
            return None


# Global session manager instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

def save_session(session_file: str, conversation_history: List[Dict[str, Any]]) -> None:
    """Convenience function to save a session"""
    manager = get_session_manager()
    manager.save_session(session_file, conversation_history)

def load_session(session_file: str) -> List[Dict[str, Any]]:
    """Convenience function to load a session"""
    manager = get_session_manager()
    return manager.load_session(session_file)

def get_session_filename() -> str:
    """Convenience function to get a new session filename"""
    manager = get_session_manager()
    return manager.get_session_filename()

def list_sessions() -> List[str]:
    """Convenience function to list sessions"""
    manager = get_session_manager()
    return manager.list_sessions()
