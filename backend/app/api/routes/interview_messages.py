"""
模块名称：面试消息路由（interview_messages）
功能描述：处理面试中的消息收发端点。

端点：
- GET  /interview/{id}/messages：获取面试所有消息
- POST /interview/{id}/message：发送文字消息
- POST /interview/{id}/voice：上传语音消息
- POST /interview/polish：润色转写文本
"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user_id
from app.api.deps.database import get_db
from app.db import schemas
from app.services.interview_runtime import get_interview_messages, handle_voice_message, process_message_logic
from app.core.llm_service import polish_text

router = APIRouter()


@router.get("/{interview_id}/messages", response_model=list[schemas.MessageResponse])
def fetch_messages(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """获取指定面试的全部对话消息（按时间顺序）。"""
    return get_interview_messages(db, user_id, interview_id)


@router.post("/polish")
async def polish_transcription(data: dict, user_id: int = Depends(get_current_user_id)):
    """对 Whisper 转写文本进行润色（加标点、修正错词）。"""
    del user_id
    text = data.get("text", "")
    if not text:
        return {"text": ""}
    return {"text": await polish_text(text)}


@router.post("/{interview_id}/message", response_model=schemas.MessageResponse)
async def send_message(interview_id: int, payload: schemas.MessageSend, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """发送文字消息给面试官，由面试引擎决定回应。"""
    response, _ = await process_message_logic(interview_id, payload.content, db, user_id)
    return response


@router.post("/{interview_id}/voice", response_model=schemas.VoiceResponse)
async def upload_voice(
    interview_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """上传语音消息，先转录再润色，然后进入对话引擎。"""
    return await handle_voice_message(interview_id, file, db, user_id)
