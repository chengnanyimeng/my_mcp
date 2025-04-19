from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends

from sse_starlette import EventSourceResponse
from starlette.responses import JSONResponse

from config.logger_config import logger
from core.session_manager import McpSessionManager
from models.mcp_request import McpRequest
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ⭐ 应用启动时
    app.state.session_manager = McpSessionManager()
    print("✅ MCP Session Manager created.")

    yield

    # ⭐ 应用关闭时
    print("❌ Shutting down MCP Session Manager...")
    # todo：可以加资源清理，比如关闭连接池、清理session
app = FastAPI(lifespan=lifespan)

def get_session_manager() -> McpSessionManager:
    return app.state.session_manager

@app.get("/sse")
async def open_stream(session_manager: McpSessionManager = Depends(get_session_manager)):
    session = session_manager.create_session(name="my_mcp", message_path="/rpc", tools_path="services")
    await session.open("endpoint")
    return EventSourceResponse(session.reader())

@app.post("/rpc")
async def push_stream(request: Request, payload: McpRequest, session_manager: McpSessionManager = Depends(get_session_manager)):
    client_id = request.query_params.get("client_id")
    logger.info(f"Client ID: {client_id}")
    if not client_id:
        raise HTTPException(status_code=400, detail="Missing 'client_id' in params")

    session = session_manager.get_session(client_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Client with client_id '{client_id}' not found")

    try:
        await session.request_dispatcher(payload)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",  # 模块名:app对象名
        host="0.0.0.0",  # 开到所有IP，局域网/外网都能连
        port=8000,  # MCP Server跑的端口
        reload=True  # 自动重启（开发模式建议开，生产建议关）
    )
