#!/usr/bin/env python3
import asyncio
import os
import json
import requests
from typing import Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Jira Configuration
JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_PAT = os.getenv("JIRA_PAT", "")

# Server creation
server = Server("jira-mcp")

def get_headers():
    """Get headers for authentication with PAT"""
    return {
        "Authorization": f"Bearer {JIRA_PAT}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def make_jira_request(endpoint: str, params: Optional[dict] = None):
    """Make a GET request to Jira API"""
    url = f"{JIRA_URL}/rest/api/2/{endpoint}"
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()

def extract_text_from_adf(adf_content):
    """Extract plain text from ADF (Atlassian Document Format)"""
    if not adf_content:
        return ""
    
    if isinstance(adf_content, str):
        return adf_content
    
    text_parts = []
    
    def extract_recursive(node):
        if isinstance(node, dict):
            if "text" in node:
                text_parts.append(node["text"])
            if "content" in node:
                for child in node["content"]:
                    extract_recursive(child)
        elif isinstance(node, list):
            for item in node:
                extract_recursive(item)
    
    extract_recursive(adf_content)
    return " ".join(text_parts)

def clean_issue_data(issue):
    """Extract and clean relevant data from a Jira issue"""
    fields = issue.get("fields", {})
    
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "type": fields.get("issuetype", {}).get("name"),
        "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
        "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
        "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "description": extract_text_from_adf(fields.get("description")),
        "url": f"{JIRA_URL}/browse/{issue.get('key')}"
    }

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for Jira"""
    return [
        types.Tool(
            name="get_issue",
            description="Get complete details of a specific Jira ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g.: PROJ-123, DEV-45)",
                    }
                },
                "required": ["issue_key"],
            },
        ),
        types.Tool(
            name="search_issues",
            description="Search for Jira tickets by different criteria like status, project, assignee, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project key (e.g.: PROJ, DEV)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Issue status (e.g.: 'To Do', 'In Progress', 'Done')",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Assignee email or name. Use 'currentUser()' for your tickets",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (e.g.: Bug, Task, Story)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Issue priority (e.g.: P1, P2, P3)",
                    },
                    "fix_version": {
                        "type": "string",
                        "description": "Issue fix version (e.g.: 25.11, 25.13, 25.14)",
                    },
                    "text": {
                        "type": "string",
                        "description": "Search by text in summary or description",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20, max: 100)",
                        "default": 20,
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_my_issues",
            description="Get all tickets assigned to you (current user)",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by specific status (optional)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20,
                    }
                },
                "required": [],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle calls to Jira tools"""
    
    # Verify configuration
    if not JIRA_URL or not JIRA_PAT:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "Missing JIRA_URL or JIRA_PAT in environment variables"
            })
        )]
    try:
        # TOOL 1: Get a specific ticket
        if name == "get_issue":
            issue_key = arguments.get("issue_key")
            
            if not issue_key:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "issue_key is required"})
                )]
            
            # Get issue from Jira
            issue = make_jira_request(f"issue/{issue_key}")
            
            # Return cleaned data as JSON
            return [types.TextContent(
                type="text",
                text=json.dumps(clean_issue_data(issue), indent=2)
            )]
        
        # TOOL 2: Search tickets by criteria
        elif name == "search_issues":
            # Build JQL query based on criteria
            jql_parts = []
            
            project = arguments.get("project")
            status = arguments.get("status")
            assignee = arguments.get("assignee")
            issue_type = arguments.get("issue_type")
            text = arguments.get("text")
            max_results = arguments.get("max_results", 20)
            
            if project:
                jql_parts.append(f'project = "{project}"')
            if status:
                jql_parts.append(f'status = "{status}"')
            if assignee:
                if assignee.lower() == "currentuser()":
                    jql_parts.append('assignee = currentUser()')
                else:
                    jql_parts.append(f'assignee = "{assignee}"')
            if issue_type:
                jql_parts.append(f'issuetype = "{issue_type}"')
            if text:
                jql_parts.append(f'(summary ~ "{text}" OR description ~ "{text}")')
            
            jql = " AND ".join(jql_parts) if jql_parts else "order by created DESC"
            
            # Perform search
            search_result = make_jira_request(
                "search",
                params={
                    "jql": jql,
                    "maxResults": min(max_results, 100),
                    "fields": "summary,status,assignee,issuetype,priority,created,updated"
                }
            )
            
            issues = search_result.get("issues", [])
            total = search_result.get("total", 0)
            
            # Return data structure
            result = {
                "total": total,
                "count": len(issues),
                "jql": jql,
                "issues": [clean_issue_data(issue) for issue in issues]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        # TOOL 3: Get my tickets
        elif name == "get_my_issues":
            status = arguments.get("status")
            max_results = arguments.get("max_results", 20)
            
            # Build JQL for current user tickets
            jql = "assignee = currentUser()"
            if status:
                jql += f' AND status = "{status}"'
            jql += " ORDER BY updated DESC"
            
            # Perform search
            search_result = make_jira_request(
                "search",
                params={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,issuetype,priority,updated"
                }
            )
            
            issues = search_result.get("issues", [])
            total = search_result.get("total", 0)
            
            # Return data structure
            result = {
                "total": total,
                "count": len(issues),
                "status_filter": status,
                "issues": [clean_issue_data(issue) for issue in issues]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        # Unknown tool
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    except requests.exceptions.HTTPError as e:
        error_data = {"error": f"Jira HTTP Error: {e.response.status_code}"}
        try:
            error_detail = e.response.json()
            error_data["detail"] = error_detail.get('errorMessages', error_detail)
        except:
            error_data["detail"] = e.response.text
        
        return [types.TextContent(type="text", text=json.dumps(error_data))]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Unexpected error: {str(e)}"})
        )]
    
async def main():
    """Main entry point"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())