from fastapi import APIRouter, Depends, HTTPException
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

def get_random_starting_question(role_name: str):
    # Find the role key from ROLES list
    role_info = next((r for r in ROLES if r["name"] == role_name), None)
    role_key = role_info["key"] if role_info else "java-backend"
    
    # Map role key to actual folder path
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # We expect knowledge-base/<role_key>/questions/behavioral.json etc.
    kb_questions_path = os.path.join(base_path, "knowledge-base", role_key, "questions")
    
    if not os.path.exists(kb_questions_path):
        return "请做一个简单的自我介绍，并聊聊你最近参与的一个技术项目。"

    try:
        # Try different files
        files = ["behavioral.json", "scenarios.json", "projects.json"]
        random.shuffle(files)
        
        for f_name in files:
            f_path = os.path.join(kb_questions_path, f_name)
            if os.path.exists(f_path):
                with open(f_path, "r", encoding="utf-8") as f:
                    questions = json.load(f)
                    if questions:
                        q = random.choice(questions)
                        return q.get("question")
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
    new_interview = models.Interview(user_id=user_id, role=data.role, status="in_progress")
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # Initial greeting based on role and randomization
    intro_q = get_random_starting_question(data.role)
    greeting = f"你好，我是你的{data.role}面试官。很高兴见到你。{intro_q}"
    ai_msg = models.Message(interview_id=new_interview.id, sender="ai", content=greeting)
    db.add(ai_msg)
    db.commit()

    return new_interview

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
        total_score=eval_record.total_score,
        highlights=report_data.get("highlights", report_data.get("strengths", [])),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=eval_record.recommendations or report_data.get("improvement_suggestions", "继续加油！"),
        created_at=eval_record.created_at
    )

@router.post("/{interview_id}/message", response_model=schemas.MessageResponse)
async def send_message(interview_id: int, msg: schemas.MessageSend, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 1. Fetch latest interview context & ownership
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    # 2. Save User Message
    user_msg = models.Message(interview_id=interview_id, sender="user", content=msg.content)
    db.add(user_msg)
    db.commit()

    # 3. Get last AI question to provide context to LLM (optional but better)
    last_ai_msg = db.query(models.Message).filter(
        models.Message.interview_id == interview_id, 
        models.Message.sender == "ai"
    ).order_by(models.Message.created_at.desc()).first()
    
    current_question = last_ai_msg.content if last_ai_msg else "请自我介绍"

    # 4. Check if we have already asked 6 messages (Greeting + 5 Questions)
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
            candidate_response=f"{msg.content} (注：这是最后一题，请给出简短反馈，并富有礼貌地结束面试，提示面试者后续可以在首页查看成长报告)"
        )
        is_final = True
    else:
        # Call Real LLM for next question
        ai_response_content = await generate_llm_response(
            role=interview.role,
            question=current_question,
            expected_points="技术准确性、逻辑清晰度、项目实践经验",
            candidate_response=msg.content
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
    total_val = round((scores.get("technical_depth", 0) + scores.get("communication", 0)) / 2, 1)
    eval_record = models.Evaluation(
        interview_id=interview_id,
        content_score=scores.get("technical_depth", 0),
        expression_score=scores.get("communication", 0),
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
    # 4. Prepare response data (ensure total_score is included for immediate display)
    evaluation_data["total_score"] = total_val
    evaluation_data["content_score"] = scores.get("technical_depth", 0)
    evaluation_data["expression_score"] = scores.get("communication", 0)

    return {"message": "Interview ended and evaluated successfully.", "evaluation": evaluation_data}
