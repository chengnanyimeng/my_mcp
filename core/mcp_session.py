import asyncio
import json
import uuid
import inspect
from typing import Any

from config.logger_config import logger
from models.event import Event
from models.mcp_request import McpRequest
from models.tool import Tool
from utils.package_path_finder import path_finder
from utils.package_scanner import ToolScanner


class McpSession:
    def __init__(self, name: str, message_path: str, tools_path: str):
        self.queue = asyncio.Queue()
        self.client_id = str(uuid.uuid4())
        self.message_path = message_path
        self.name = name
        self.tools = ToolScanner(path_finder(tools_path))

        self.info = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "experimental": {},
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": name,
                "version": "1.6.0"
            }
        }

    def _map_type(self, annotation: Any) -> str:
        """将Python的参数类型注解映射为JSON Schema类型"""
        if annotation == int or annotation == float:
            return "number"
        elif annotation == bool:
            return "boolean"
        elif annotation == dict:
            return "object"
        elif annotation == list:
            return "array"
        elif annotation == str:
            return "string"
        elif annotation == inspect._empty:  # 没写注解
            return "string"
        else:
            return "string"  # 默认 fallback 是 string

    async def _establish_stream(self, event, next_msg_path, client_id):
        """构造初始化stream msg"""
        await self.queue.put(Event(event=event, data=f"{next_msg_path}?client_id={client_id}"))

    async def open(self, event: str):
        await self._establish_stream(event, self.message_path, self.client_id)

    async def reader(self):
        """异步消费消息队列，供 SSE 发送事件"""
        while True:
            event = await self.queue.get()
            logger.info(f"Mcp Server Pushing event: {event}")
            yield {
                "event": event.event,
                "data": event.data
            }


    @staticmethod
    def response(result: Any, id: int):
        """封装响应结构"""
        message = {
            "jsonrpc": "2.0",
            "result": result,
        }
        if id is not None:
            message["id"] = id
        return json.dumps(message)

    async def request_dispatcher(self, request: McpRequest) -> Any:
        if request.method == "initialize":
            await self.queue.put(Event(event="message", data=self.response(self.info, request.id)))
        elif request.method == "tools/list":
            await self.queue.put(Event(event="message", data=self.response({"tools": self.list_tool()}, request.id)))
        elif request.method == "tools/call":
            result = await self.call_tool(request.params.get("name"), request.params.get("arguments"))
            await self.queue.put(
                Event(event="message", data=self.response({"content": result, "isError": False}, request.id)))

    def list_tool(self):
        """列出通过services反射出来的所有工具（使用Tool强类型，流式优雅版）"""
        tools = [
            Tool(
                name=method.__name__,
                description=method.__doc__ or "",
                inputSchema={
                    "type": "object",
                    "properties": {
                        name: {"type": self._map_type(param.annotation)}
                        for name, param in inspect.signature(method).parameters.items()
                    },
                    "required": [
                        name
                        for name, param in inspect.signature(method).parameters.items()
                        if param.default == inspect.Parameter.empty
                    ]
                }
            )
            for _, method in self.tools
        ]
        return [tool.model_dump() for tool in tools]

    async def call_tool(self, name: str, arguments: dict):
        """根据名字动态调用工具"""
        for instance, method in self.tools:
            if method.__name__ == name:
                return await method(**arguments)
        raise ValueError(f"Tool '{name}' not found")

"""Local Test"""
if __name__ == '__main__':
    mcp = McpSession("mcp", "mcp session", "services")
    print(mcp.tools)
    print(mcp.list_tool())

    async def call_tool():
        result = await mcp.call_tool(name="add", arguments={"a": 2, "b": 3})
        print("call_tool result:", result)
        assert result == 5
