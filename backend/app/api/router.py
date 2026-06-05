"""
模块名称：API 主路由器（router）
功能描述：汇总所有子路由并挂载到统一前缀下。

路由结构：
- /auth/*      ：用户认证（注册/登录）
- /interview/* ：面试核心功能（会话/消息/报告/辅助）
- /code/*      ：代码练习与判题
"""

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.code import router as code_router
from app.api.routes.interview_aux import router as interview_aux_router
from app.api.routes.interview_messages import router as interview_messages_router
from app.api.routes.interview_reports import router as interview_reports_router
from app.api.routes.interview_session import router as interview_session_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(interview_aux_router, prefix="/interview", tags=["interview"])
api_router.include_router(interview_session_router, prefix="/interview", tags=["interview"])
api_router.include_router(interview_messages_router, prefix="/interview", tags=["interview"])
api_router.include_router(interview_reports_router, prefix="/interview", tags=["interview"])
api_router.include_router(code_router, prefix="/code", tags=["code"])
