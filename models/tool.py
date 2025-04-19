from typing import Dict, Any
from pydantic import BaseModel, Field


class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(default_factory=lambda: {
        "type": "object",
        "properties": {}
    })
