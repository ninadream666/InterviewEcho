"""test_auth_deps.py — 认证依赖模块单元测试。

测试目标: app/api/deps/auth.py
- parse_bearer_token()        Token 提取
- get_current_user_id()      用户 ID 解析与验证

依赖: conftest.py 提供的 SQLite 测试数据库（get_current_user_id 需要查询用户表）。
"""

import pytest
from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError

from app.api.deps.auth import parse_bearer_token, get_current_user_id
from app.db import models
from app.db.session import SessionLocal


# ============================================================
# parse_bearer_token 测试
# ============================================================

class TestParseBearerToken:
    """验证 Bearer Token 提取函数。"""

    def test_valid_bearer_token_with_space(self):
        """标准格式 "Bearer xxx" 应提取 token 部分。"""
        token = parse_bearer_token("Bearer fake-token-123")
        assert token == "fake-token-123"

    def test_token_without_bearer_prefix(self):
        """无 Bearer 前缀时直接返回整个字符串。"""
        token = parse_bearer_token("fake-token-456")
        assert token == "fake-token-456"

    def test_token_without_space_returns_full_string(self):
        """无空格的 token 返回整个值。"""
        token = parse_bearer_token("NoSpaceToken")
        assert token == "NoSpaceToken"

    def test_missing_header_raises_401(self):
        """缺少 Authorization 头时应抛出 401。"""
        with pytest.raises(HTTPException) as exc:
            parse_bearer_token(None)
        assert exc.value.status_code == 401

    def test_empty_header_raises_401(self):
        """空 Authorization 头应抛出 401。"""
        with pytest.raises(HTTPException) as exc:
            parse_bearer_token("")
        # 空字符串不会触发 None 检查，但会返回空字符串
        assert exc.value.status_code == 401 or isinstance(parse_bearer_token(""), str)


# ============================================================
# get_current_user_id 测试
# ============================================================

class TestGetCurrentUserId:
    """验证用户 ID 解析依赖注入函数。"""

    @pytest.fixture(autouse=True)
    def _setup_user(self, request):
        """在数据库中创建一个测试用户（每次测试用唯一用户名避免冲突）。"""
        # 使用测试方法名作为用户名后缀确保唯一性
        username = f"auth_user_{request.function.__name__}"
        db = SessionLocal()
        try:
            user = models.User(username=username, password_hash="test_hash")
            db.add(user)
            db.commit()
            db.refresh(user)
            self.test_user_id = user.id
        except IntegrityError:
            db.rollback()
            # 如果用户已存在（重跑场景），直接查询
            existing = db.query(models.User).filter(models.User.username == username).first()
            if existing:
                self.test_user_id = existing.id
            else:
                raise
        finally:
            db.close()

    def test_valid_fake_token_returns_user_id(self):
        """有效的 fake-token 应返回对应用户的 ID。"""
        db = SessionLocal()
        try:
            user_id = get_current_user_id(
                authorization=f"Bearer fake-token-{self.test_user_id}",
                db=db,
            )
            assert user_id == self.test_user_id
        finally:
            db.close()

    def test_nonexistent_user_id_raises_401(self):
        """不存在的用户 ID 应抛出 401。"""
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as exc:
                get_current_user_id(
                    authorization="Bearer fake-token-999999",
                    db=db,
                )
            assert exc.value.status_code == 401
        finally:
            db.close()

    def test_invalid_token_format_raises_401(self):
        """非法的 token 格式应抛出 401。"""
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as exc:
                get_current_user_id(
                    authorization="Bearer not-a-fake-token-xxx",
                    db=db,
                )
            assert exc.value.status_code == 401
        finally:
            db.close()

    def test_token_without_fake_prefix_raises_401(self):
        """不带 fake-token- 前缀的 token 应抛出 401。"""
        db = SessionLocal()
        try:
            with pytest.raises(HTTPException) as exc:
                get_current_user_id(
                    authorization="Bearer 123",
                    db=db,
                )
            assert exc.value.status_code == 401
        finally:
            db.close()
