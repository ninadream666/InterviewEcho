"""
模块名称：认证依赖（auth deps）
功能描述：提供 FastAPI 路由用的认证依赖注入函数。
当前版本使用简化的 fake-token 机制：前端传 "fake-token-{user_id}" 作为 Bearer Token，
后端解析出 user_id 并验证用户是否存在。

注意：这是一个 MVP 实现，生产环境应替换为 JWT 或 OAuth2 方案。
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.db import models


def parse_bearer_token(authorization: Optional[str]) -> str:
    """
    从 Authorization 请求头中提取 Bearer Token。

    Args:
        authorization: HTTP Authorization 请求头值。

    Returns:
        str: 提取出的 Token 字符串。

    Raises:
        HTTPException 401: 若缺少 Authorization 请求头。
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    return authorization.split(" ", 1)[1] if " " in authorization else authorization


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> int:
    """
    从请求头中解析并验证当前登录用户的 ID。

    流程：
    1. 解析 Bearer Token
    2. 从 "fake-token-{id}" 格式中提取用户 ID
    3. 查询数据库确认用户存在

    Args:
        authorization: HTTP Authorization 请求头。
        db: 数据库会话（由 FastAPI 依赖注入）。

    Returns:
        int: 已验证的用户 ID。

    Raises:
        HTTPException 401: Token 无效或用户不存在。
    """
    token = parse_bearer_token(authorization)
    try:
        user_id = int(token.replace("fake-token-", ""))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token") from exc

    exists = db.query(models.User.id).filter(models.User.id == user_id).first()
    if not exists:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")
    return user_id
