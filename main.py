"""
Main entry point for Ollama CLI with refactored architecture
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import get_config
from src.core.agent import ChatAgent
from src.utils.logging import get_logger
from src.utils.sessions import get_session_manager, save_session, load_session, get_session_filename
from src.llm.client import get_client
from src.tools.loader import ToolLoader

from rich.prompt import Prompt
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from datetime import datetime

def main():
    """Main CLI entry point"""
    import argparse
    
    # Setup console for rich output
    console = Console()
    
    # Setup
    config = get_config()
    logger = get_logger()
    session_manager = get_session_manager()
    
    # Load tools with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Loading tools...", total=None)
        tool_loader = ToolLoader()
        tool_loader.load_all_tools()
        progress.update(task, description="✅ Tools loaded successfully")
    
    # Check Ollama connection with better error handling
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Connecting to Ollama...", total=None)
        llm_client = get_client()
        if not llm_client.health_check():
            progress.update(task, description="❌ Connection failed")
            logger.error(
                Panel(
                    "[red]Cannot connect to Ollama[/red]\n\n"
                    "Possible solutions:\n"
                    "• Check if Ollama is running: [cyan]ollama serve[/cyan]\n"
                    "• Verify the endpoint in .agentrc\n"
                    "• Ensure the model is available: [cyan]ollama list[/cyan]",
                    title="Connection Error",
                    style="red"
                )
            )
            sys.exit(1)
        progress.update(task, description="✅ Connected to Ollama")
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Ollama CLI Agent - Intelligent assistant with tool support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start interactive session
  python main.py --verbose               # Enable debug logging
  python main.py --resume session.json   # Resume previous conversation
  python main.py --config custom.agentrc # Use custom configuration

Commands in session:
  /tools      Show available tools
  /sessions   List recent sessions  
  /clear      Clear conversation history
  /exit       Exit the application
"""
    )
    parser.add_argument("--resume", type=str, metavar="FILE", 
                       help="Resume from a previous session file")
    parser.add_argument("--config", type=str, metavar="FILE",
                       help="Path to configuration file (default: .agentrc)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose/debug logging")
    parser.add_argument("--version", action="version", version="Ollama CLI v1.0.0")
    args = parser.parse_args()
    
    # Update config based on args
    if args.verbose:
        config.verbosity = "debug"
        from src.utils.logging import setup_logging
        setup_logging("debug")
    
    if args.config:
        from src.core.config import reload_config
        config = reload_config(args.config)
    
    # Initialize agent
    agent = ChatAgent()
    
    # Handle session resumption first (to get session_file)
    if args.resume:
        try:
            history = load_session(args.resume)
            agent.load_history(history)
            session_file = args.resume
            logger.print_message(
                Panel(f"Resuming session from [bold]{args.resume}[/bold]", 
                     style="bold green", box=box.ROUNDED)
            )
        except Exception as e:
            logger.error(f"Failed to resume session: {e}")
            sys.exit(1)
    else:
        session_file = get_session_filename()
        logger.print_message(
            Panel(f"New session. Saving to [bold]{session_file}[/bold]", 
                 style="bold green", box=box.ROUNDED)
        )
    
    # Display startup information
    logger.print_message(
        Panel.fit(
            f"[bold cyan]Ollama CLI Agent v1.0.0[/bold cyan]\n"
            f"Model: [green]{config.model}[/green]\n"
            f"Endpoint: [blue]{config.ollama_url}[/blue]\n"
            f"Session: [yellow]{session_file}[/yellow]",
            style="bold",
            border_style="cyan"
        )
    )
    
    # Welcome message with helpful tips
    help_text = (
        "💬 [bold]Chat naturally[/bold] - Ask questions, request tasks, or give instructions\n"
        "🔧 [bold]Use tools[/bold] - I can save files, search content, send emails, and more\n"
        "📋 [bold]Commands[/bold] - Type /tools, /sessions, /health, /help, /clear, or /exit\n"
        "💡 [bold]Tips[/bold] - Be specific about file names and locations for best results"
    )
    
    logger.print_message(
        Panel(
            help_text,
            title="[bold green]Welcome to Ollama CLI Agent[/bold green]",
            style="green",
            box=box.ROUNDED
        )
    )
    
    # Main interaction loop
    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]").strip()
                
                if user_input.lower() in {"exit", "quit", "/exit"}:
                    logger.print_message("[bold red]Exiting REPL.[/bold red]")
                    break
                
                # Handle slash commands
                if user_input.startswith("/"):
                    if user_input == "/exit":
                        logger.print_message("[bold red]Exiting REPL.[/bold red]")
                        break
                    elif user_input == "/tools":
                        from src.tools import get_registry
                        registry = get_registry()
                        categories = registry.get_tools_by_category()
                        logger.print_message("[bold cyan]Available Tools:[/bold cyan]")
                        for category, tool_infos in categories.items():
                            logger.print_message(f"[bold]{category}:[/bold]")
                            for tool_info in tool_infos:
                                logger.print_message(f"  - {tool_info.name}: {tool_info.description}")
                        continue
                    elif user_input == "/sessions":
                        sessions = session_manager.list_sessions()
                        logger.print_message("[bold cyan]Available Sessions:[/bold cyan]")
                        for session in sessions[:10]:  # Show last 10
                            info = session_manager.get_session_info(session)
                            if info:
                                logger.print_message(f"  - {session} ({info.get('total_messages', 0)} messages)")
                        continue
                    elif user_input == "/health":
                        from src.utils.validation import run_system_diagnostics
                        run_system_diagnostics()
                        continue
                    elif user_input == "/clear":
                        agent.clear_history()
                        logger.print_message("[bold yellow]Conversation history cleared.[/bold yellow]")
                        continue
                    elif user_input == "/help":
                        help_text = (
                            "[bold cyan]Available Commands:[/bold cyan]\n"
                            "  /tools    - Show all available tools by category\n"
                            "  /sessions - List recent conversation sessions\n"
                            "  /health   - Run system health diagnostics\n"
                            "  /clear    - Clear conversation history\n"
                            "  /help     - Show this help message\n"
                            "  /exit     - Exit the application\n\n"
                            "[bold cyan]Tips:[/bold cyan]\n"
                            "  • Be specific about file names and paths\n"
                            "  • Use natural language to describe tasks\n"
                            "  • Tools can be chained automatically\n"
                            "  • Sessions are saved automatically"
                        )
                        logger.print_message(Panel(help_text, title="Help", style="cyan"))
                        continue
                    else:
                        logger.print_message(f"[bold red]Unknown command: {user_input}[/bold red]")
                        continue
                
                if not user_input:
                    continue
                
                # Process message with agent
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Processing your request...", total=None)
                    response = agent.process_message(user_input)
                    progress.update(task, description="✅ Request completed")
                
                # Save updated history
                save_session(session_file, agent.get_history())
                
            except KeyboardInterrupt:
                logger.print_message(
                    Panel(
                        "[yellow]Session interrupted by user[/yellow]\n"
                        "Your conversation has been saved automatically.",
                        title="Goodbye!",
                        style="yellow"
                    )
                )
                break
            except Exception as e:
                logger.error(
                    Panel(
                        f"[red]Unexpected error:[/red] {e}\n\n"
                        "The session will continue. Check logs for details.\n"
                        f"[dim]Log file: {config.log_dir}/ollama-cli-{datetime.now().strftime('%Y%m%d')}.log[/dim]",
                        title="Error",
                        style="red"
                    )
                )
                logger.error(f"Error in main loop: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(
            Panel(
                f"[red]Fatal error during startup:[/red] {e}\n\n"
                "Please check your configuration and try again.\n"
                f"[dim]Config file: .agentrc[/dim]\n"
                f"[dim]Log file: {config.log_dir if 'config' in locals() else 'logs'}/ollama-cli-{datetime.now().strftime('%Y%m%d')}.log[/dim]",
                title="Startup Error",
                style="red"
            )
        )
        if logger:
            logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
