# Ollama CLI Agent 🤖

A powerful, extensible command-line interface for interacting with Ollama LLMs with built-in tool support, session management, and a robust plugin system.

## ✨ Features

- **🔧 Extensible Tool System**: 11+ built-in tools with auto-discovery
- **💾 Session Management**: Resume conversations with automatic saving
- **🎨 Rich CLI Interface**: Beautiful console output with progress indicators
- **⚙️ Flexible Configuration**: Environment variables and YAML config support
- **🔌 Plugin Architecture**: Easy plugin development and loading
- **🛡️ Robust Error Handling**: Comprehensive error management and recovery
- **📊 Structured Logging**: Debug logs and performance monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Required models pulled (e.g., `ollama pull llama3.1:8b`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ollama-cli-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure (optional):**
   ```bash
   cp .agentrc.example .agentrc
   # Edit .agentrc to customize settings
   ```

4. **Start the CLI:**
   ```bash
   python main.py
   ```

## 📖 Usage

### Basic Commands

```bash
# Start a new session
python main.py

# Resume a previous session
python main.py --resume sessions/session-20240726-190634.json

# Enable verbose logging
python main.py --verbose

# Use custom config file
python main.py --config /path/to/custom/.agentrc
```

### Interactive Commands

Once in the CLI, you can use these slash commands:

- `/tools` - List all available tools by category
- `/sessions` - Show recent conversation sessions
- `/clear` - Clear current conversation history
- `/exit` - Exit the application

### Example Interactions

```
You: Generate a wedding todo list and save it to wedding-todo.md
Assistant: I'll create a comprehensive wedding todo list for you and save it to a markdown file.

🔧 Tool Call: generate_and_save_todo
Generated wedding todo list and saved to wedding-todo.md successfully.

You: Search for "venue" in the wedding file and save results
Assistant: I'll search for venue-related items in your wedding todo file.

🔧 Tool Call: search_and_save
Found 3 matches for "venue" and saved results to venue-search-results.txt
```

## ⚙️ Configuration

The application uses `.agentrc` for configuration (YAML format):

```yaml
# .agentrc - Agent configuration file
model: llama3.1:8b
verbosity: debug
log_dir: logs/
sessions_dir: sessions/

# Optional settings
ollama_url: http://localhost:11434/api/chat
timeout: 30
max_history: 10
tool_timeout: 10
max_tool_calls: 5
```

### Environment Variables

You can override any setting with environment variables:

```bash
export OLLAMA_URL="http://localhost:11434/api/chat"
export OLLAMA_MODEL="llama3.1:8b"
export VERBOSITY="debug"
export LOG_DIR="logs"
export SESSIONS_DIR="sessions"
```

## 🔧 Available Tools

### Generation Tools
- **generate_content** - Generate text content
- **generate_and_save_todo** - Create and save TODO lists

### File Operations
- **save_to_file** - Save content to files
- **read_file** - Read file contents
- **list_files** - List directory contents

### Search & Analysis
- **search_and_save** - Search content and save results
- **read_and_summarize** - Read and summarize files

### Communication
- **send_email** - Send emails (with configuration)
- **generate_and_email** - Generate content and email it

### Utility
- **run_shell** - Execute shell commands
- **get_current_time** - Get current timestamp

### Combined Operations
- **search_summarize_save** - Multi-step content processing

## 🔌 Plugin Development

Create custom tools by adding Python files to `src/tools/plugins/`:

```python
from src.tools import tool

@tool(
    name="my_custom_tool",
    description="Description of what your tool does",
    category="utility",
    schema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "First parameter"
            }
        },
        "required": ["param1"]
    }
)
def my_custom_tool(param1: str) -> str:
    """Your custom tool implementation"""
    return f"Processed: {param1}"
```

Tools are automatically discovered and loaded on startup.

## 📁 Project Structure

```
ollama-cli/
├── src/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── exceptions.py      # Custom exception hierarchy
│   │   └── agent.py           # Main chat agent
│   ├── llm/
│   │   └── client.py          # Ollama API client
│   ├── tools/
│   │   ├── __init__.py        # Tool registry
│   │   ├── loader.py          # Tool discovery
│   │   ├── shared.py          # Shared utilities
│   │   └── plugins/           # Individual tool files
│   └── utils/
│       ├── logging.py         # Structured logging
│       └── sessions.py        # Session management
├── logs/                      # Application logs
├── sessions/                  # Conversation sessions
├── tests/                     # Test suite
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── .agentrc                   # Configuration file
```

## 🧪 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_config.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Tools

1. Create a new Python file in `src/tools/plugins/`
2. Use the `@tool` decorator to register your function
3. Restart the application - tools are auto-discovered

## 📊 Monitoring & Debugging

### Logs

- **Application logs**: `logs/ollama-cli-YYYYMMDD.log`
- **Sessions**: `sessions/session-YYYYMMDD-HHMMSS.json`

### Debug Mode

```bash
# Enable debug logging
python main.py --verbose

# Or set in config
export VERBOSITY=debug
```

### Performance Monitoring

The application includes built-in timing for:
- LLM API calls
- Tool execution
- Session operations

## 🚀 Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### systemd Service

```ini
[Unit]
Description=Ollama CLI Agent
After=network.target

[Service]
Type=simple
User=ollama
WorkingDirectory=/opt/ollama-cli
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**Import Errors**
```bash
# Ensure you're in the project root
cd /path/to/ollama-cli

# Check Python path
python -c "import sys; print(sys.path)"
```

**Tool Not Found**
```bash
# List available tools
python main.py
# Then type: /tools
```

## 🔄 Changelog

See [docs/](docs/) for detailed change logs of each phase of development.

## 📧 Support

For questions and support:
- Create an issue on GitHub
- Check the [docs/](docs/) directory for detailed documentation
- Review the [troubleshooting](#-troubleshooting) section
