# Quick Start Guide

## 1. Setup (First Time Only)

Run the setup script:
```bash
cd jira-mcp-server
./setup.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## 2. Configure

Edit `.env` file with your Jira credentials:
```env
JIRA_BASE_URL=https://your-jira-instance.com
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```

**Get your API token:** https://id.atlassian.com/manage-profile/security/api-tokens

## 3. Run

### For MCP Inspector (Testing)
```bash
source .venv/bin/activate
python server.py --transport sse
```
Then connect MCP Inspector to: `http://localhost:8000/mcp`

### For Claude Desktop
```bash
source .venv/bin/activate
python server.py
```

Add to Claude config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["/full/path/to/jira-mcp-server/server.py"]
    }
  }
}
```

## 4. Test

Try these commands in Claude or MCP Inspector:
- "Show me all incidents in the OPS project"
- "Get details for issue OPS-123"
- "Add a comment to OPS-123"

## Troubleshooting

**404 errors?** Make sure you're connecting to `/mcp` endpoint:
- ✅ Correct: `http://localhost:8000/mcp`
- ❌ Wrong: `http://localhost:8000/`

**Authentication failed?** 
- Check your API token is correct
- Verify your email matches your Jira account
- Remove any trailing slashes from JIRA_BASE_URL

**Can't find python?** Use `python3` instead of `python`