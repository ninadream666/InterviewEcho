from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class InterviewStart(BaseModel):
    role: str
    difficulty: Optional[str] = "medium"
    knowledge_points: Optional[List[str]] = []
    total_rounds: Optional[int] = 5

class InterviewResponse(BaseModel):
    id: int
    user_id: int
    role: str
    status: str
    start_time: datetime
    class Config:
        from_attributes = True

class MessageSend(BaseModel):
    content: str
    # audio path omitted for MVP simplicity handled via multipart if needed

class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    created_at: datetime
    is_final: bool = False
    class Config:
        from_attributes = True

class EvaluationSummary(BaseModel):
    id: int
    role: str
    difficulty: str
    total_score: float
    created_at: datetime
    class Config:
        from_attributes = True

class EvaluationDetail(BaseModel):
    interview_id: int
    role: str
    content_score: float
    expression_score: float
    business_scenario_score: float
    problem_solving_score: float
    total_score: float
    highlights: List[str]
    weaknesses: List[str]
    recommendations: str
    scores: Optional[dict] = None
    created_at: datetime

class VoiceResponse(BaseModel):
    transcription: str
    ai_message: MessageResponse
