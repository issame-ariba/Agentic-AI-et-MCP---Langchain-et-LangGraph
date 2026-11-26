# n8n MCP agent

## Start the local services

Start Docker Desktop, then run these commands from the project root in
PowerShell. Use the Docker Desktop executable explicitly if `docker` opens the
Windows app chooser:

```powershell
$Docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
& $Docker ps
& $Docker compose up --build -d
```

Open n8n at `http://127.0.0.1:5678` and complete its local owner setup. The
Compose configuration keeps all published services bound to loopback; n8n persists its
own configuration in the `n8n_data` Docker volume. The MCP server is reachable
from n8n at `http://mcp-demo:24000/mcp` and from MCP Inspector on the host at
`http://127.0.0.1:24000/mcp`.

Import [n8n_workflow.json](n8n_workflow.json) into n8n using **Import from
File**. Create a Groq credential in n8n and select it in **Groq Chat Model**.
The workflow contains no credential material and stays inactive until you test
it.

Stop the services without deleting n8n data:

```powershell
& $Docker compose down
```

Do not use `docker compose down -v` unless you intend to delete the n8n volume.

## Build the agent workflow

1. Create a **When chat message received** trigger and connect it to an
   **AI Agent** node.
2. Create a Groq credential in n8n, select it in **Groq Chat Model**, and
   connect that node to the AI Agent's `ai_languageModel` input. Do not put API
   keys in the workflow export or this repository.
3. Add an **MCP Client Tool** sub-node, choose node version **1.2 or newer**,
   select **Streamable HTTP**, and set the endpoint to
   `http://mcp-demo:24000/mcp`.
4. Connect the MCP tool to the AI Agent's `ai_tool` input. Confirm that the
   agent can list `get_employee_infos` and `search`, then test with the
   fictitious employee `Sami Demo`.
5. To use web search, set `TAVILY_API_KEY` in the ignored root `.env` file and
   rebuild the MCP service with `& $Docker compose up --build -d mcp-demo`.
   Without this key, calling `search` returns an explicit configuration error.

## MCP Inspector

The Compose stack also starts the official MCP Inspector Docker image, avoiding
an npm install. Open `http://127.0.0.1:6274`, select **Streamable HTTP**, and
connect to `http://mcp-demo:24000/mcp`. The Inspector backend and MCP server
share a private Docker network; only the Inspector UI is published on loopback.
No Inspector volume is configured, so any future authentication secrets remain
in memory for that container session.
