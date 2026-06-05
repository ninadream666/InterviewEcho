"""
模块名称：数据库会话管理（session）
功能描述：创建 SQLAlchemy 引擎和会话工厂，提供 FastAPI 依赖注入用的数据库会话生成器。
支持 MySQL（生产）和 SQLite（测试/本地）两种数据库。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# ---- 创建数据库引擎 ----
database_url = settings.sqlalchemy_database_url
engine_kwargs = {"echo": False}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    获取数据库会话（生成器），用于 FastAPI Depends 依赖注入。

    用法：
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    会话在请求结束时自动关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
