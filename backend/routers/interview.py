from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import uuid
import shutil
import tempfile
from services.stt_service import stt_service
from sqlalchemy.orm import Session
from typing import List
import json
import os
import random
from db import models, schemas
from db.database import get_db
from datetime import datetime
from core.llm_service import generate_llm_response, evaluate_full_interview

router = APIRouter()

ROLES = [
    {
        "id": 1, 
        "name": "Java后端开发工程师", 
        "key": "java-backend", 
        "icon": "☕", 
        "desc": "重点考察自动装配、JVM、并发编程等", 
        "gradient": "from-orange-400 to-red-500"
    },
    {
        "id": 2, 
        "name": "Web前端开发工程师", 
        "key": "web-frontend", 
        "icon": "🌐", 
        "desc": "重点考察Vue/React原理、性能优化、事件循环等", 
        "gradient": "from-blue-400 to-indigo-600"
    },
    {
        "id": 3, 
        "name": "Python算法工程师", 
        "key": "python-algorithm", 
        "icon": "🐍", 
        "desc": "重点考察机器学习模型、数据结构、模型调优等", 
        "gradient": "from-green-400 to-emerald-600"
    }
]

def get_random_starting_question(role_name: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # Find the role key from ROLES list
    role_info = next((r for r in ROLES if r["name"] == role_name), None)
    role_key = role_info["key"] if role_info else "java-backend"
    
    # Map role key to actual folder path
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_questions_path = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions")
    
    if not os.path.exists(kb_questions_path):
        return "请做一个简单的自我介绍，并聊聊你最近参与的一个技术项目。"

    # Map easy/medium/hard from UI to internal JSON difficulty
    diff_map = {"简单": "easy", "中等": "medium", "困难": "hard"}
    target_diff = diff_map.get(difficulty, "medium")

    try:
        potential_questions = []
        for f_name in os.listdir(kb_questions_path):
            if f_name.endswith(".json"):
                f_path = os.path.join(kb_questions_path, f_name)
                with open(f_path, "r", encoding="utf-8") as f:
                    questions = json.load(f)
                    for q in questions:
                        # Filter by difficulty and optionally by knowledge point section
                        q_diff = q.get("difficulty", "medium")
                        q_section = q.get("section", "")
                        
                        match_diff = (q_diff == target_diff)
                        match_section = True
                        if knowledge_points:
                            match_section = any(kp == q_section for kp in knowledge_points)
                        
                        if match_diff and match_section:
                            potential_questions.append(q.get("question"))
        
        if potential_questions:
            return random.choice(potential_questions)
            
    except Exception as e:
        pass
    
    return "请做一个简单的自我介绍，并谈谈你对该岗位的理解。"

@router.get("/roles")
def get_roles():
    return ROLES

from fastapi import Header

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    try:
        # Expected format: "Bearer fake-token-1"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        user_id_str = token.replace("fake-token-", "")
        return int(user_id_str)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Authorization Token")

@router.post("/start", response_model=schemas.InterviewResponse)
def start_interview(data: schemas.InterviewStart, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    knowledge_points_json = json.dumps(data.knowledge_points) if data.knowledge_points else "[]"
    new_interview = models.Interview(
        user_id=user_id, 
        role=data.role, 
        difficulty=data.difficulty,
        knowledge_points=knowledge_points_json,
        status="in_progress"
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # Initial greeting based on role, difficulty, and selected directions
    intro_q = get_random_starting_question(data.role, data.difficulty, data.knowledge_points)
    greeting = f"你好，我是你的{data.role}面试官。很高兴见到你。接下来我们将进行一次{data.difficulty or '标准'}难度的面试{f'，重点关注{', '.join(data.knowledge_points)}等领域' if data.knowledge_points else ''}。{intro_q}"
    ai_msg = models.Message(interview_id=new_interview.id, sender="ai", content=greeting)
    db.add(ai_msg)
    db.commit()

    return new_interview

@router.get("/roles/{role_key}/sections")
def get_role_sections(role_key: str):
    # Dynamic extraction of sections from knowledge base JSON files
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_questions_path = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions")
    
    sections = set()
    if os.path.exists(kb_questions_path):
        for f_name in os.listdir(kb_questions_path):
            if f_name.endswith(".json"):
                try:
                    with open(os.path.join(kb_questions_path, f_name), "r", encoding="utf-8") as f:
                        questions = json.load(f)
                        for q in questions:
                            if "section" in q:
                                sections.add(q["section"])
                except:
                    pass
    
    # Return as a sorted list
    return sorted(list(sections))

@router.get("/{interview_id}/messages", response_model=List[schemas.MessageResponse])
def get_interview_messages(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")
    
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    return messages

@router.get("/{interview_id}/evaluation", response_model=schemas.EvaluationDetail)
def get_evaluation(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    eval_record = db.query(models.Evaluation).join(models.Interview).filter(
        models.Evaluation.interview_id == interview_id,
        models.Interview.user_id == user_id
    ).first()
    if not eval_record:
        raise HTTPException(status_code=404, detail="Evaluation not found or unauthorized")
    
    report_data = {}
    if eval_record.report_json:
        try:
            report_data = json.loads(eval_record.report_json)
        except:
            report_data = {}

    return schemas.EvaluationDetail(
        interview_id=eval_record.interview_id,
        role=eval_record.interview.role,
        content_score=eval_record.content_score,
        expression_score=eval_record.expression_score,
        business_scenario_score=eval_record.business_scenario_score,
        problem_solving_score=eval_record.problem_solving_score,
        total_score=eval_record.total_score,
        highlights=report_data.get("highlights", report_data.get("strengths", [])),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=eval_record.recommendations or report_data.get("improvement_suggestions", "继续加油！"),
        scores=report_data.get("scores"),
        created_at=eval_record.created_at
    )

@router.post("/polish")
async def polish_transcription(data: dict, user_id: int = Depends(get_current_user_id)):
    """
    Endpoint to add punctuation to raw transcription.
    """
    text = data.get("text", "")
    if not text:
        return {"text": ""}
    
    polished_text = await llm_service.polish_text(text)
    return {"text": polished_text}

@router.post("/{interview_id}/message", response_model=schemas.MessageResponse)
async def send_message(interview_id: int, msg: schemas.MessageSend, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return await process_message_logic(interview_id, msg.content, db, user_id)

@router.post("/{interview_id}/voice", response_model=schemas.VoiceResponse)
async def upload_voice(
    interview_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_current_user_id)
):
    # 1. Save uploaded file to temporary location
    temp_dir = tempfile.gettempdir()
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".webm"
    temp_file_path = os.path.join(temp_dir, f"voice_{uuid.uuid4()}{file_extension}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Transcribe using Whisper
        transcript = stt_service.transcribe(temp_file_path)
        if not transcript:
            raise HTTPException(status_code=400, detail="Voice transcription failed. Please try again or type your message.")
        
        # 3. Process the transcribed text as a message
        ai_msg_resp = await process_message_logic(interview_id, transcript, db, user_id)
        return schemas.VoiceResponse(transcription=transcript, ai_message=ai_msg_resp)
        
    finally:
        # 4. Cleanup
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

async def process_message_logic(interview_id: int, content: str, db: Session, user_id: int):
    # 1. Fetch latest interview context & ownership
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    # 2. Save User Message
    user_msg = models.Message(interview_id=interview_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()

    # 3. Get last AI question to provide context to LLM
    last_ai_msg = db.query(models.Message).filter(
        models.Message.interview_id == interview_id, 
        models.Message.sender == "ai"
    ).order_by(models.Message.created_at.desc()).offset(0).first() 
    
    current_question = last_ai_msg.content if last_ai_msg else "请自我介绍"

    # 4. Check if we have already asked sufficient questions
    ai_count = db.query(models.Message).filter(
        models.Message.interview_id == interview_id,
        models.Message.sender == "ai"
    ).count()

    is_final = False
    if ai_count >= 6:
        # Generate a closing message instead of a new question
        ai_response_content = await generate_llm_response(
            role=interview.role,
            question=current_question,
            expected_points="总结评价",
            candidate_response=f"{content} (注：这是最后一题，请给出简短反馈，并富有礼貌地结束面试，提示面试者后续可以在首页查看成长报告)",
            difficulty=interview.difficulty,
            knowledge_points=interview.knowledge_points
        )
        is_final = True
    else:
        # Call Real LLM for next question
        ai_response_content = await generate_llm_response(
            role=interview.role,
            question=current_question,
            expected_points="技术准确性、逻辑清晰度、项目实践经验",
            candidate_response=content,
            difficulty=interview.difficulty,
            knowledge_points=interview.knowledge_points
        )

    # 5. Save AI Message
    ai_msg = models.Message(interview_id=interview_id, sender="ai", content=ai_response_content)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    response = schemas.MessageResponse.model_validate(ai_msg)
    response.is_final = is_final

    return response

@router.get("/history", response_model=List[schemas.EvaluationSummary])
def get_interview_history(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Fetch completed interviews for the specific user
    results = db.query(models.Evaluation).join(models.Interview).filter(
        models.Interview.user_id == user_id,
        models.Interview.status == "completed"
    ).order_by(models.Evaluation.created_at.desc()).all()
    
    return [
        schemas.EvaluationSummary(
            id=e.interview_id,
            role=e.interview.role,
            total_score=e.total_score,
            created_at=e.created_at
        ) for e in results
    ]

@router.post("/{interview_id}/end")
async def end_interview(interview_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    interview.status = "completed"
    interview.end_time = datetime.utcnow()
    db.commit()

    # 1. Gather all messages for evaluation
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    
    # 2. Call Real LLM Evaluator (Async)
    evaluation_data = await evaluate_full_interview(messages)

    # 3. Save Evaluation to DB
    scores = evaluation_data.get("scores", {})
    tech_score = scores.get("technical_depth", 0)
    comm_score = scores.get("communication", 0)
    bus_score = scores.get("business_scenario", 0)
    prob_score = scores.get("problem_solving", 0)
    
    # Calculate average of 4 metrics
    total_val = round((tech_score + comm_score + bus_score + prob_score) / 4, 1)

    eval_record = models.Evaluation(
        interview_id=interview_id,
        content_score=tech_score,
        expression_score=comm_score,
        business_scenario_score=bus_score,
        problem_solving_score=prob_score,
        total_score=total_val,
        report_json=json.dumps({
            "highlights": evaluation_data.get("strengths", []),
            "weaknesses": evaluation_data.get("weaknesses", []),
            "scores": scores
        }),
        recommendations=evaluation_data.get("improvement_suggestions", "继续加油！")
    )
    db.add(eval_record)
    db.commit()
    # 4. Prepare response data using the same schema as get_evaluation
    # This ensures immediate display in the frontend works without a refresh
    evaluation_result = {
        "interview_id": interview_id,
        "role": interview.role,
        "content_score": tech_score,
        "expression_score": comm_score,
        "business_scenario_score": bus_score,
        "problem_solving_score": prob_score,
        "total_score": total_val,
        "highlights": evaluation_data.get("strengths", []),
        "weaknesses": evaluation_data.get("weaknesses", []),
        "recommendations": evaluation_data.get("improvement_suggestions", "继续加油！"),
        "created_at": eval_record.created_at or datetime.utcnow()
    }

    return {"message": "Interview ended and evaluated successfully.", "evaluation": evaluation_result}
