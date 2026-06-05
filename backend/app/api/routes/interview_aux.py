"""
模块名称：面试辅助功能路由（interview_aux）
功能描述：提供面试的辅助功能端点。

端点：
- GET  /interview/roles：获取可选岗位列表
- GET  /interview/roles/{key}/sections：获取岗位的知识点章节
- POST /interview/resume/parse：解析简历（PDF/文本）
- POST /interview/repo/analyze：分析 GitHub 仓库
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps.auth import get_current_user_id
from app.db.schemas import RepoAnalyzeRequest
from app.services.interview_runtime import analyze_repo_preview, get_role_sections, get_roles, parse_resume_payload

router = APIRouter()


@router.get("/roles")
def list_roles():
    """获取所有可选的面试岗位列表（Java后端/Web前端/Python算法）。"""
    return get_roles()


@router.get("/roles/{role_key}/sections")
def list_role_sections(role_key: str):
    """获取指定岗位的知识点章节列表。"""
    return get_role_sections(role_key)


@router.post("/resume/parse")
async def parse_resume_endpoint(
    file: UploadFile = File(None),
    text: str = Form(None),
    user_id: int = Depends(get_current_user_id),
):
    """上传简历（PDF 文件或纯文本），解析为候选人画像。"""
    del user_id
    return await parse_resume_payload(file, text)


@router.post("/repo/analyze")
async def analyze_repo_endpoint(data: RepoAnalyzeRequest, user_id: int = Depends(get_current_user_id)):
    """分析指定的 GitHub 公开仓库，返回项目摘要信息。"""
    del user_id
    return await analyze_repo_preview(data.url)
