from core.mcp_session import McpSession


class McpSessionManager:
    def __init__(self):
        self.sessions = {}  # client_id -> McpSession

    def create_session(self, name: str, message_path: str, tools_path: str) -> 'McpSession':
        """创建并注册一个新的McpSession"""
        session = McpSession(name=name, message_path=message_path, tools_path=tools_path)
        self.sessions[session.client_id] = session
        return session

    def get_session(self, client_id: str) -> 'McpSession':
        """根据client_id查找McpSession"""
        return self.sessions.get(client_id)

    def delete_session(self, client_id: str):
        """删除一个McpSession"""
        if client_id in self.sessions:
            del self.sessions[client_id]

    def all_sessions(self) -> list:
        """返回所有活跃的McpSession"""
        return list(self.sessions.values())

session_manager = McpSessionManager()