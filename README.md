# 🚀 My MCP Server

A lightweight, self-hosted MCP (Model Context Protocol) server based on the official MCP specification.

## 🚀 What is this?

This project provides a **quick transformation structure**  
to **adapt your existing backend services into an MCP-compliant server** with minimal changes.

You can expose your existing service methods as MCP tools effortlessly!

✅ **Only one requirement**:  
Make sure your `services/` package contains **all the business interfaces** you want to expose as MCP tools.

---

## 🛠️ Features

- ⚡ **Fast Transformation**: Quickly adapt your current backend into an MCP server.
- 🔍 **Auto Discovery**: Automatically scan and register service methods as MCP tools.
- 📦 **Fully MCP-Compatible**: Seamless connection to MCP Inspector or any MCP-compliant client.
- 🛠️ **Minimal Invasive**: No need to heavily modify your existing service logic.
- 🚀 **Plug-and-Play**: Just organize your methods properly under the `services/` directory.

---

## 📂 Project Structure

```plaintext
my_mcp_server/
├── app.py                     # FastAPI app, defines /sse and /rpc endpoints
├── config/                     # Configuration files
├── core/
│   ├── mcp_session.py          # MCP session logic
│   ├── mcp_session_manager.py  # Session management
│   ├── models/                 # Event, McpRequest, Tool models
│   └── utils/                  # Scanners and path finders
├── services/                   # Business services to expose as MCP tools
│   ├── math_tool.py            # Example tool: math operations
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

## 📦 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Connect MCP Inspector

- Open [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- Set your **MCP Server URL** to: `http://localhost:8000`
- Start interacting!

---

## 📚 How It Works

1. When a client connects to `/sse`, the server:
   - Creates a new `McpSession`.
   - Scans all tools in `services/` and registers them.
   - Immediately pushes an `initialize` event.
2. When a client sends a request to `/v1/mcp/events/send`:
   - The server routes it to the correct session.
   - Dispatches `initialize`, `tools/list`, or `tools/call` accordingly.
3. Tools are dynamically mapped to your service methods.

---

## ⚠️ Notes

- All business logic you want to expose must be placed inside the `services/` directory.
- Each service method should be an `async def` coroutine.
- Tool scanning supports simple class-based services.
- Make sure method names are **unique** across all services to avoid conflicts.

---

## 📄 Example Service (`services/math_tool.py`)

```python
class MathService:
    async def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    async def subtract(self, a: int, b: int) -> int:
        """Subtract two numbers."""
        return a - b
```

Once placed under `services/`, they will be automatically scanned and registered as MCP tools!

---

## 📋 Todo (optional extensions)

- [ ] Support nested sub-packages inside `services/`
- [ ] Add Session idle timeout and auto cleanup
- [ ] Add `/health` and `/metrics` endpoints
- [ ] Add Dockerfile and CI/CD scripts

---

## 📜 License

This project is open-sourced under the [MIT License](LICENSE).
