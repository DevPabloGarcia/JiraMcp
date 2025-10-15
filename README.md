# Jira MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with Jira, enabling AI assistants like Claude to interact with your Jira tickets directly.

## Features

- **Get Issue Details**: Retrieve complete information about specific Jira tickets
- **Search Issues**: Search tickets by project, status, assignee, issue type, priority, and more
- **Get My Issues**: Quickly fetch all tickets assigned to you
- **Smart Filtering**: Build complex JQL queries through simple parameters
- **Clean Output**: Automatically extracts and formats data from Atlassian Document Format (ADF)

## Prerequisites

- Python 3.7 or higher
- A Jira account with API access
- Jira Personal Access Token (PAT)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd JIRA_MCP_PY
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables


```bash
JIRA_URL=https://your-instance.atlassian.net
JIRA_PAT=your_personal_access_token
```

### Getting Your Jira Personal Access Token

1. Go to your Jira settings
2. Click "Developer Settings"
3. Click "Create API token"
4. Give it a memorable name

### MCP Configuration

Add this server to your MCP settings file (usually `~/.config/claude/mcp.json`):

```json
{
  "mcpServers": {
    "jira": {
      "command": "/path/to/JIRA_MCP_PY/venv/bin/python",
      "args": ["/path/to/JIRA_MCP_PY/jira_server.py"],
      "env": {
        "JIRA_URL": "https://your-instance.atlassian.net",
        "JIRA_PAT": "your_personal_access_token"
      }
    }
  }
}
```

## Usage

Once configured, the MCP server provides three main tools:

### 1. Get Issue
Retrieve detailed information about a specific Jira ticket:
```
Get details for issue KEY-123
```

### 2. Search Issues
Search for tickets using various criteria:
```
Search for bugs in project PROJ that are in progress
Find all high priority tasks assigned to me
```

### 3. Get My Issues
Quick access to your assigned tickets:
```
Show me my current tickets
What issues am I working on?
```

## Available Search Filters

- **project**: Project key (e.g., "PROJ", "DEV")
- **status**: Issue status (e.g., "To Do", "In Progress", "Done")
- **assignee**: Email, name, or "currentUser()"
- **issue_type**: Type of issue (e.g., "Bug", "Task", "Story")
- **priority**: Priority level (e.g., "P1", "P2", "P3")
- **fix_version**: Target version (e.g., "25.11", "25.13")
- **text**: Search in summary and description
- **max_results**: Limit number of results (default: 20, max: 100)

## Development

### Project Structure
```
JIRA_MCP_PY/
├── jira_server.py      # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

### Running Tests
```bash
# Test the server locally
python jira_server.py
```

## Troubleshooting

### Authentication Errors
- Verify your `JIRA_URL` doesn't have a trailing slash
- Ensure your PAT is valid and hasn't expired
- Check you have proper permissions in Jira

### Connection Issues
- Confirm your Jira instance URL is correct
- Check your network connection
- Verify firewall settings aren't blocking the connection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal.

## Support

For issues and questions:
- Open an issue on GitHub
- Check Jira API documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v2/

## Acknowledgments

Built using the [Model Context Protocol](https://github.com/anthropics/mcp) by Anthropic.
