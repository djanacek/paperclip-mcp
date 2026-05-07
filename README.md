# paperclip-mcp

MCP server for the [Paperclip](https://github.com/paperclipai/paperclip) AI agent orchestration platform.

Exposes Paperclip's REST API as [Model Context Protocol](https://modelcontextprotocol.io) tools, so any MCP-compatible AI assistant (Claude, etc.) can manage issues, agents, goals, approvals, and costs through natural language.

---

## Features

| Category | Tools |
|---|---|
| **Issues** | `list_issues` . `get_issue` . `create_issue` . `update_issue` . `checkout_issue` . `release_issue` . `comment_on_issue` . `list_comments` . `delete_issue` |
| **Agents** | `list_agents` . `get_agent` . `invoke_agent_heartbeat` |
| **Goals** | `list_goals` . `create_goal` . `update_goal` |
| **Approvals** | `list_approvals` . `approve` . `reject` . `request_approval_revision` |
| **Monitoring** | `get_cost_summary` . `get_dashboard` . `list_activity` |

---

## Requirements

- Python 3.10+
- A running [Paperclip](https://github.com/paperclipai/paperclip) instance
- Authentication, one of:
  - An Agent API key (Paperclip UI -> Settings -> API Keys), **or**
  - A browser session token (`__Secure-better-auth.session_token` cookie)

---

## Installation

```bash
pip install paperclip-mcp
```

Or install directly from a branch:

```bash
pip install "git+https://github.com/djanacek/paperclip-mcp.git@feat/list-comments"
```

---

## Configuration

Set these environment variables (or use a `.env` file):

```env
PAPERCLIP_API_KEY=your-api-key-here
PAPERCLIP_COMPANY_ID=your-company-uuid-here
PAPERCLIP_BASE_URL=http://localhost:3100/api
```

---

## Usage

### Claude Desktop (stdio)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "paperclip-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "PAPERCLIP_API_KEY": "your-api-key",
        "PAPERCLIP_COMPANY_ID": "your-company-uuid"
      }
    }
  }
}
```

### Claude Code / HTTP transport

```bash
paperclip-mcp --transport streamable-http --port 9011
```

---

## Changelog

### 0.3.0

- New tool `list_comments(issue_id, limit, after)`: read comment threads on any issue.
  Returns comments in chronological order with id, body, author, createdAt, parentId.
  Supports pagination via `after` cursor.

### 0.2.1

- Initial release with list_issues, get_issue, create_issue, update_issue,
  checkout_issue, release_issue, comment_on_issue, delete_issue,
  list_agents, get_agent, invoke_agent_heartbeat,
  list_goals, create_goal, update_goal,
  list_approvals, approve, reject, request_approval_revision,
  get_cost_summary, get_dashboard, list_activity.
