# Horizon MCP Integration

## Recommended Command

Start the built-in MCP server from the Horizon repository root:

```bash
uv run horizon-mcp
```

If you need a Python module fallback:

```bash
uv run python -m src.mcp.server
```

## Two Setup Modes

### Option A: Client Config With Explicit `cwd`

Some MCP clients need a fixed working directory in their config. In that case, the absolute path is only used in the client-side `cwd` field, not in Horizon's code.

Example:

```json
{
  "mcpServers": {
    "horizon": {
      "command": "uv",
      "args": ["run", "horizon-mcp"],
      "cwd": "/absolute/path/to/Horizon"
    }
  }
}
```

Restart the client after saving the config.

### Option B: Local Start Without Any Path In Config

If your workflow allows you to start the MCP server manually, no absolute path is needed at all:

```bash
cd /absolute/path/to/Horizon
uv run horizon-mcp
```

This is the cleanest way to avoid path values in client configuration.

## Secret Files

Instead of exporting environment variables manually, you can place a JSON file in one of these locations:

- `.cursor/mcp.secrets.json`
- `.cursor/mcp.secrets.local.json`
- `config/mcp.secrets.json`
- `config/mcp.secrets.local.json`
- `<horizon_path>/data/mcp.secrets.json`
- `<horizon_path>/data/mcp-secrets.json`

Supported formats:

```json
{
  "OPENAI_API_KEY": "sk-xxxx",
  "ANTHROPIC_API_KEY": "sk-ant-xxxx",
  "GOOGLE_API_KEY": "xxxx",
  "GITHUB_TOKEN": "ghp_xxxx"
}
```

```json
{
  "env": {
    "OPENAI_API_KEY": "sk-xxxx",
    "ANTHROPIC_API_KEY": "sk-ant-xxxx",
    "GOOGLE_API_KEY": "xxxx",
    "GITHUB_TOKEN": "ghp_xxxx"
  }
}
```

To use a secrets file elsewhere, set `HORIZON_MCP_SECRETS_PATH` in the MCP
server process environment. For a client config that supports per-server
environment variables, add it to the Horizon server entry:

```json
{
  "mcpServers": {
    "horizon": {
      "command": "uv",
      "args": ["run", "horizon-mcp"],
      "cwd": "/absolute/path/to/Horizon",
      "env": {
        "HORIZON_MCP_SECRETS_PATH": "/absolute/path/to/mcp.secrets.json"
      }
    }
  }
}
```

## Smoke Check

Run the local smoke check from the repository root:

```bash
uv run python scripts/check_mcp.py
```

It verifies module import, path resolution, config loading, and metrics access.
