"""
模块名称：数据库依赖（database deps）
功能描述：重导出 get_db 数据库会话生成器，供路由层通过 Depends(get_db) 注入使用。
"""

from app.db.session import get_db

__all__ = ["get_db"]
