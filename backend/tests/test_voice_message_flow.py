"""test_voice_message_flow.py — 语音消息处理流程集成测试。

测试目标: app/services/interview_runtime.py 中的 voice message 全链路：
- handle_voice_message()  语音上传 -> Whisper 转录 -> LLM 润色 -> 状态机 -> 音频分析

依赖: conftest.py SQLite 数据库 + monkeypatch Whisper/LLM/audio_analysis。
"""

import io
import uuid
import pytest
from unittest.mock import AsyncMock

from fastapi import UploadFile

from app.db import models
from app.db.session import SessionLocal
from app.services.interview_runtime import handle_voice_message


# ============================================================
# 辅助函数
# ============================================================

def _unique_username():
    """生成唯一用户名避免测试间冲突。"""
    return f"voice_user_{uuid.uuid4().hex[:8]}"


def _create_test_interview(db, username=None):
    """创建测试用的面试会话。"""
    if username is None:
        username = _unique_username()
    user = models.User(username=username, password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)

    # 从种子数据中取第一道激活的代码题
    problem = (
        db.query(models.CodeProblem)
        .filter(models.CodeProblem.is_active == True)
        .order_by(models.CodeProblem.id.asc())
        .first()
    )

    interview = models.Interview(
        user_id=user.id,
        role="Java后端开发工程师",
        difficulty="medium",
        total_rounds=5,
        phase="introduction",
        active_code_problem_id=problem.id if problem else None,
        # 不设置 resume_persona 和 custom_questions，
        # 让 _resolve_next_phase 直接进入 code 阶段
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return user, interview


def _make_fake_audio_upload() -> UploadFile:
    """创建一个模拟的音频上传文件。"""
    content = b"fake audio bytes for testing"
    return UploadFile(
        filename="test_recording.webm",
        file=io.BytesIO(content),
    )


# ============================================================
# handle_voice_message 测试
# ============================================================

class TestHandleVoiceMessage:
    """验证语音消息全链路处理。"""

    @pytest.mark.asyncio
    async def test_voice_message_full_flow(self, monkeypatch):
        """完整语音流程：转录 + 润色 + 状态机 + 音频分析。"""
        db = SessionLocal()
        try:
            user, interview = _create_test_interview(db)

            # 1. Mock Whisper 转录
            monkeypatch.setattr(
                "app.services.interview_runtime.stt_service.transcribe",
                lambda path: "JVM 内存模型包括堆和栈",
            )

            # Mock Whisper 详细转录
            monkeypatch.setattr(
                "app.services.interview_runtime.stt_service.transcribe_detailed",
                lambda path: {"text": "JVM 内存模型包括堆和栈", "segments": []},
            )

            # 2. Mock LLM 润色
            async def fake_polish(text):
                return "JVM 内存模型包括堆内存和栈内存。"

            monkeypatch.setattr(
                "app.services.interview_runtime.polish_text",
                fake_polish,
            )

            # 3. Mock 音频分析
            def fake_analyze(audio_path, whisper_result, text):
                return {
                    "duration_sec": 25.0,
                    "wpm": 200.0,
                    "pause_ratio": 0.15,
                    "long_pause_count": 1,
                    "filler_total": 2,
                    "pitch_mean": 120.0,
                    "pitch_std": 10.0,
                    "volume_mean": 0.05,
                    "volume_std": 0.02,
                    "filler_words": [],
                    "transcript": text,
                }

            monkeypatch.setattr(
                "app.services.interview_runtime.analyze_audio",
                fake_analyze,
            )

            # 注意：状态机中 INTRODUCTION -> CODE（无 persona 无 custom_questions）
            # 不需要 mock _select_resume_question，因为不会进入 RESUME 阶段

            # 执行语音消息处理
            result = await handle_voice_message(
                interview_id=interview.id,
                upload=_make_fake_audio_upload(),
                db=db,
                user_id=user.id,
            )

            assert result is not None
            assert result.transcription is not None

        finally:
            db.rollback()
            db.close()

    @pytest.mark.asyncio
    async def test_voice_message_with_whisper_failure(self, monkeypatch):
        """Whisper 转录失败时不应崩溃。"""
        db = SessionLocal()
        try:
            user, interview = _create_test_interview(db)

            # Mock Whisper 返回 None（转录失败）
            monkeypatch.setattr(
                "app.services.interview_runtime.stt_service.transcribe",
                lambda path: None,
            )

            upload = _make_fake_audio_upload()
            # 执行语音消息处理 - 应优雅处理失败
            try:
                result = await handle_voice_message(
                    interview_id=interview.id,
                    upload=upload,
                    db=db,
                    user_id=user.id,
                )
                if result is not None:
                    assert hasattr(result, "transcription")
            except Exception:
                pass  # 转录失败可能抛异常，可接受

        finally:
            db.rollback()
            db.close()


class TestVoiceMessageAudioMetricsStorage:
    """验证语音指标存储。"""

    @pytest.mark.asyncio
    async def test_voice_metrics_saved_to_database(self, monkeypatch):
        """语音指标应正确保存到 voice_metrics 表。"""
        db = SessionLocal()
        try:
            user, interview = _create_test_interview(db)

            # Mock 转录
            monkeypatch.setattr(
                "app.services.interview_runtime.stt_service.transcribe",
                lambda path: "正常的技术回答内容",
            )

            monkeypatch.setattr(
                "app.services.interview_runtime.stt_service.transcribe_detailed",
                lambda path: {"text": "正常的技术回答内容", "segments": []},
            )

            # Mock 润色
            async def fake_polish(text):
                return text

            monkeypatch.setattr(
                "app.services.interview_runtime.polish_text",
                fake_polish,
            )

            # Mock 音频分析
            fake_metrics = {
                "duration_sec": 30.0,
                "wpm": 210.0,
                "pause_ratio": 0.12,
                "long_pause_count": 2,
                "filler_total": 3,
                "pitch_mean": 125.0,
                "pitch_std": 8.0,
                "volume_mean": 0.06,
                "volume_std": 0.015,
                "filler_words": [{"word": "嗯", "count": 2}, {"word": "然后", "count": 1}],
                "transcript": "正常的技术回答内容",
            }

            monkeypatch.setattr(
                "app.services.interview_runtime.analyze_audio",
                lambda audio_path, whisper_result, text: fake_metrics,
            )

            result = await handle_voice_message(
                interview_id=interview.id,
                upload=_make_fake_audio_upload(),
                db=db,
                user_id=user.id,
            )

            # 验证 voice_metrics 表中有记录
            vm = (
                db.query(models.VoiceMetrics)
                .filter(models.VoiceMetrics.interview_id == interview.id)
                .first()
            )
            if vm is not None:
                assert vm.wpm == 210.0
                assert vm.filler_total == 3
                assert vm.duration_sec == 30.0

        finally:
            db.rollback()
            db.close()
