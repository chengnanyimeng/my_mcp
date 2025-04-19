class MathService:
    async def add(self, a: int, b: int) -> int:
        """加法，返回两个数的和"""
        return a + b

    async def subtract(self, a: int, b: int) -> int:
        """减法，返回第一个数减去第二个数"""
        return a - b