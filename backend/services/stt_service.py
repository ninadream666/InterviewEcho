"""
模块名称：语音转文本服务（stt_service）
功能描述：基于 OpenAI Whisper 模型实现语音到文本的转写。

核心功能：
1. 使用单例模式管理 Whisper 模型（避免重复加载）
2. 提供基础转写（纯文本）和详细转写（带时间戳）两种模式
3. 自动检测设备（CUDA GPU / CPU）

配置：
- 模型大小通过 WHISPER_MODEL 环境变量控制（默认 "small"）
- fp16 仅在 CUDA 可用时启用（CPU 上必须设为 False）
"""

import whisper
import os
import torch
from typing import Optional


class WhisperSTT:
    """
    Whisper 语音转文本服务（单例模式）。

    使用方式：
        stt_service = WhisperSTT()  # 全局唯一实例
        text = stt_service.transcribe("audio.webm")
        detailed = stt_service.transcribe_detailed("audio.webm")  # 含时间戳
    """

    _instance = None   # 单例实例
    _model = None      # Whisper 模型对象（懒加载）

    def __new__(cls):
        """单例模式：确保全局只有一个 WhisperSTT 实例和一份模型。"""
        if cls._instance is None:
            cls._instance = super(WhisperSTT, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: str = "small"):
        """
        加载 Whisper 模型到内存（懒加载，仅首次调用时加载）。

        Args:
            model_name: Whisper 模型大小（"tiny" / "small" / "medium" / "large"）。

        Returns:
            whisper.Model: 加载后的模型对象。
        """
        if self._model is None:
            print(f"Loading Whisper model: {model_name}...")
            # 自动检测设备优先级：CUDA GPU > CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Whisper will run on: {device}")
            self._model = whisper.load_model(model_name, device=device)
        return self._model

    def transcribe(self, audio_path: str) -> Optional[str]:
        """
        将音频文件转写为纯文本字符串。

        Args:
            audio_path: 音频文件的绝对路径。

        Returns:
            str: 转写文本，或 None（文件不存在 / 转写失败）。
        """
        if self._model is None:
            self.load_model()

        if not os.path.exists(audio_path):
            print(f"Whisper error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Starting transcription for: {audio_path}")
            # CPU 上必须 fp16=False，否则会报错
            result = self._model.transcribe(audio_path, fp16=(torch.cuda.is_available()))
            text = result.get("text", "").strip()
            print(f"Transcription successful: {text[:50]}...")
            return text
        except Exception as e:
            print(f"Whisper transcription error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def transcribe_detailed(self, audio_path: str) -> Optional[dict]:
        """
        返回带时间戳的完整 Whisper 转写结果，供 audio_analysis 模块使用。

        与 transcribe() 的区别：
            - transcribe() 只返回纯文本字符串
            - transcribe_detailed() 返回 dict，包含 segments 时间戳，用于计算语速、停顿等

        Returns:
            {
                "text": str,                              # 完整文本
                "segments": [                              # 分段（带时间戳）
                    {"start": float, "end": float, "text": str, ...}
                ],
                "language": str                            # 检测到的语言
            }
            或 None（文件不存在 / 转写失败）
        """
        if self._model is None:
            self.load_model()

        if not os.path.exists(audio_path):
            print(f"Whisper error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Starting detailed transcription for: {audio_path}")
            result = self._model.transcribe(
                audio_path,
                fp16=torch.cuda.is_available(),
                word_timestamps=True,    # 关键参数：启用字级时间戳
                verbose=False,
            )
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            language = result.get("language", "zh")
            print(f"Detailed transcription successful: {len(segments)} segments, text[:50]={text[:50]}...")
            return {
                "text": text,
                "segments": segments,
                "language": language,
            }
        except Exception as e:
            print(f"Whisper detailed transcription error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None


# 全局单例，其他模块直接 import 使用
stt_service = WhisperSTT()
