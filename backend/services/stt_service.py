import whisper
import os
import torch
from typing import Optional

class WhisperSTT:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WhisperSTT, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_name: str = "small"):
        """
        Load the whisper model into memory (singleton).
        """
        if self._model is None:
            print(f"Loading Whisper model: {model_name}...")
            # Detect device: use cuda if available, else cpu
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Whisper will run on: {device}")
            self._model = whisper.load_model(model_name, device=device)
        return self._model

    def transcribe(self, audio_path: str) -> Optional[str]:
        """
        Transcribe an audio file using the local model.
        """
        if self._model is None:
            self.load_model()
        
        if not os.path.exists(audio_path):
            print(f"Whisper error: Audio file not found at {audio_path}")
            return None

        try:
            print(f"Starting transcription for: {audio_path}")
            # fp16=False is necessary when running on CPU
            result = self._model.transcribe(audio_path, fp16=(torch.cuda.is_available()))
            text = result.get("text", "").strip()
            print(f"Transcription successful: {text[:50]}...")
            return text
        except Exception as e:
            print(f"Whisper transcription error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global instance
stt_service = WhisperSTT()
