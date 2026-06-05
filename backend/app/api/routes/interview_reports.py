"""
模块名称：面试报告路由（interview_reports）
功能描述：处理面试评估报告的查看和生成端点。

端点：
- GET  /interview/{id}/evaluation：获取面试评估详情
- GET  /interview/history：获取历史面试列表
- POST /interview/{id}/end：结束面试并生成报告
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_id
from app.api.deps.database import get_db
from app.db import schemas
from app.services.interview_runtime import end_interview, get_evaluation_detail, get_history

router = APIRouter()


@router.get("/{interview_id}/evaluation", response_model=schemas.EvaluationDetail)
def fetch_evaluation(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """获取指定面试的完整评估报告（评分、亮点、弱点、建议等）。"""
    return get_evaluation_detail(db, user_id, interview_id)


@router.get("/history", response_model=list[schemas.EvaluationSummary])
def fetch_history(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """获取用户的历史面试评估摘要列表。"""
    return get_history(db, user_id)


@router.post("/{interview_id}/end")
async def finish_interview(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """结束面试，触发 LLM 综合评估 + 表达评分 + 学习计划生成。"""
    return await end_interview(db, user_id, interview_id)
