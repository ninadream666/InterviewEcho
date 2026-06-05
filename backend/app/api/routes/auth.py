"""
模块名称：用户认证路由（auth）
功能描述：处理用户注册和登录请求。

认证方案（MVP 阶段）：
- 密码使用 bcrypt 哈希存储
- 登录成功后返回 "fake-token-{user_id}" 格式的 Token
- 生产环境应替换为 JWT 方案

端点：
- POST /auth/register：用户注册
- POST /auth/login：用户登录
"""

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.api.deps.database import get_db
from app.db import models, schemas

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """验证明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """对明文密码进行 bcrypt 哈希。"""
    return pwd_context.hash(password)


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    用户注册端点。

    流程：
    1. 检查用户名是否已存在
    2. 哈希密码后创建新用户
    3. 返回用户信息（不含密码）
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = models.User(username=user.username, password_hash=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    用户登录端点。

    返回 fake-token-{user_id} 格式的 Token（MVP 方案），
    前端需要将其存入 localStorage 并在后续请求的 Authorization 头中携带。
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = f"fake-token-{db_user.id}"
    return {"access_token": access_token, "token_type": "bearer"}
