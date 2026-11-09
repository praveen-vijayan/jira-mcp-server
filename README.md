# Jira MCP Server

A Model Context Protocol (MCP) server that exposes Jira Server/Data Center functionality as tools for AI assistants like Claude, Cursor, and other MCP-compatible clients.
Test Line
## Features

### Available Tools

1. **get_incidents** - Fetch incidents with optional filters (project, status, priority)
2. **get_incident_by_key** - Get detailed information about a specific issue
3. **search_issues** - Run custom JQL queries
4. **add_comment** - Add comments to issues
5. **get_transitions** - Get available status transitions for an issue
6. **update_status** - Transition an issue to a new status

## Installation

### 1. Clone or Download

```bash
cd jira-mcp-server
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your Jira credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
JIRA_BASE_URL=https://your-jira-instance.com
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```

#### Getting Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token
4. Paste it in your `.env` file

## Usage

### Running the Server

#### Stdio Mode (for Claude Desktop, local clients)

```bash
python server.py
```

#### SSE Mode (for remote/hosted clients, MCP Inspector)

```bash
python server.py --transport sse
```

The server will start on `http://0.0.0.0:8000/mcp`

### Testing with MCP Inspector

1. Start the server in SSE mode:
   ```bash
   python server.py --transport sse
   ```

2. Open MCP Inspector and connect to:
   ```
   http://localhost:8000/mcp
   ```

3. You should see all 6 tools available for testing

### Integrating with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["/path/to/jira-mcp-server/server.py"],
      "env": {
        "JIRA_BASE_URL": "https://your-jira-instance.com",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Example Queries

Once connected, you can ask Claude:

- "Show me all high priority incidents in the OPS project"
- "Get details for issue OPS-123"
- "Add a comment to OPS-123 saying 'Working on this now'"
- "What are the available transitions for OPS-123?"
- "Move OPS-123 to In Progress"
- "Search for all open bugs in project ABC"

## Configuration Options

### Environment Variables

- `JIRA_BASE_URL` - Your Jira instance URL (required)
- `JIRA_EMAIL` - Your Jira email (required)
- `JIRA_API_TOKEN` - Your Jira API token (required)
- `JIRA_PROJECT_KEY` - Default project key (optional)
- `MCP_HOST` - Server host for SSE mode (default: 0.0.0.0)
- `MCP_PORT` - Server port for SSE mode (default: 8000)

## Troubleshooting

### Connection Issues

If you see 404 errors when connecting:
- Make sure you're connecting to `/mcp` endpoint, not just `/`
- Correct: `http://localhost:8000/mcp`
- Incorrect: `http://localhost:8000/`

### Authentication Issues

- Verify your API token is correct
- Check that your email matches your Jira account
- Ensure your Jira instance URL doesn't have a trailing slash

### Permission Issues

Make sure your Jira account has permissions to:
- View issues
- Add comments
- Transition issues (if using update_status)

## Development

### Project Structure

```
jira-mcp-server/
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── .env               # Your configuration (not in git)
├── .env.example       # Example configuration
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

### Adding New Tools

To add a new tool, use the `@mcp.tool()` decorator:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int = 10) -> str:
    """
    Description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    # Your implementation here
    return "result"
```

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the MCP documentation: https://modelcontextprotocol.io
3. Check FastMCP documentation: https://github.com/jlowin/fastmcp
