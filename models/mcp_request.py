from typing import Optional

from pydantic import BaseModel


class McpRequest(BaseModel):
    id: Optional[int] = None
    jsonrpc: str
    method: str
    params: Optional[dict] = None
