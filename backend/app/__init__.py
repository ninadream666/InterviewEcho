"""
模块名称：FastAPI 应用工厂（app）
功能描述：InterviewEcho API 应用入口，负责创建和配置 FastAPI 实例。
配置内容包括：CORS 跨域中间件、根路由、API 路由器挂载。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例。

    Returns:
        FastAPI: 配置完成的 FastAPI 应用。
    """
    app = FastAPI(title="InterviewEcho API", description="AI Mock Interview MVP")

    # 配置 CORS 跨域策略
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def read_root():
        """API 根路径健康检查。"""
        return {"message": "Welcome to InterviewEcho API"}

    # 挂载所有业务路由到 /api 前缀
    app.include_router(api_router, prefix="/api")
    return app
