from typing import List, Dict


class MathService:
    def _response_wrap(self, content: str) -> List[Dict]:
        """TEXT response wrapper"""
        #todo: need to support other type returns including audio & image & resource
        return [{"type": "text", "text": content}]

    async def add(self, a: int, b: int) -> List[Dict]:
        """加法，返回两个数的和"""
        return self._response_wrap(str(a + b))

    async def subtract(self, a: int, b: int) -> List[Dict]:
        """减法，返回第一个数减去第二个数"""
        return self._response_wrap(str(a - b))