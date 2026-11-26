# MCP: Streamable HTTP

The server exposes `get_employee_infos` and `search` using Streamable HTTP:

```powershell
python C_MCP\server.py
```

Test it with MCP Inspector:

```powershell
npx -y @modelcontextprotocol/inspector
```

Configure the Inspector connection as Streamable HTTP and use
`http://127.0.0.1:24000/mcp`. The employee entries are fictional test data.
`search` requires `TAVILY_API_KEY`.

With the MCP server still running, start the LangChain client in a second
terminal:

```powershell
python -m C_MCP.agent
```

The n8n setup is described in [n8n_setup.md](n8n_setup.md).

The instructor's [mcp-demo reference](https://github.com/mohamedYoussfi/mcp-demo)
contains a related two-tool Streamable HTTP example.
