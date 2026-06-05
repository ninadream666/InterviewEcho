"""
模块名称：ORM 基类（base）
功能描述：定义 SQLAlchemy 声明式基类 Base，所有 ORM 模型均继承自此基类。
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
