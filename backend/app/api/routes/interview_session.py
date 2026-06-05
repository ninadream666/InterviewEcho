"""
模块名称：面试会话路由（interview_session）
功能描述：管理面试会话的生命周期端点。

端点：
- GET  /interview/incomplete：查询是否有未完成的面试
- GET  /interview/{id}/state：获取面试当前状态
- POST /interview/start：开始新面试
- POST /interview/{id}/discard：放弃当前面试
- POST /interview/{id}/code/submit：面试中提交代码
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_id
from app.api.deps.database import get_db
from app.db import schemas
from app.services.interview_runtime import (
    discard_interview,
    get_incomplete_interview,
    get_interview_state,
    start_interview,
    submit_interview_code,
)

router = APIRouter()


@router.get("/incomplete", response_model=schemas.IncompleteInterviewResponse)
def fetch_incomplete_interview(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """查询当前用户是否有未完成的面试（用于登录后自动恢复）。"""
    return get_incomplete_interview(db, user_id)


@router.get("/{interview_id}/state", response_model=schemas.InterviewStateResponse)
def fetch_interview_state(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """获取面试当前状态（前端轮询用，含阶段、轮次、代码题信息）。"""
    return get_interview_state(db, user_id, interview_id)


@router.post("/{interview_id}/discard")
def discard_incomplete_interview(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """放弃当前面试（物理删除面试记录）。"""
    return discard_interview(db, user_id, interview_id)


@router.post("/{interview_id}/code/submit", response_model=schemas.InterviewCodeSubmitResponse)
async def submit_code_for_interview(
    interview_id: int,
    payload: schemas.CodeRunRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """面试中提交代码答案，触发判题 + LLM 代码审查。"""
    return await submit_interview_code(db, user_id, interview_id, payload)


@router.post("/start", response_model=schemas.InterviewResponse)
async def begin_interview(payload: schemas.InterviewStart, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """开始一场新的模拟面试。"""
    return await start_interview(db, user_id, payload)
