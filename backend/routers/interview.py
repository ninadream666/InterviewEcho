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
from core.llm_service import generate_llm_response, evaluate_full_interview, polish_text

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

def get_questions_by_category(role_key: str, category: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # Map role key to actual JSON file
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
    
    if not os.path.exists(questions_file):
        return []

    diff_map = {"简单": "easy", "中等": "medium", "困难": "hard"}
    target_diff = diff_map.get(difficulty, "medium")

    try:
        with open(questions_file, "r", encoding="utf-8") as f:
            all_questions = json.load(f)
            
        potential = []
        for q in all_questions:
            if q.get("category") == category and q.get("difficulty") == target_diff:
                # Optional section filter
                if knowledge_points:
                    if q.get("section") in knowledge_points:
                        potential.append(q)
                else:
                    potential.append(q)
        return potential
    except:
        return []

def get_random_starting_question(role_name: str, difficulty: str = "medium", knowledge_points: List[str] = None):
    # This is a fallback/legacy function, we now prefer get_questions_by_category
    role_info = next((r for r in ROLES if r["name"] == role_name), None)
    role_key = role_info["key"] if role_info else "java-backend"
    
    # Always start with Scenario for the first actual question
    questions = get_questions_by_category(role_key, "business_scenario", difficulty, knowledge_points)
    if not questions:
        # Fallback to any if scenario not found
        backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
        except:
            return "请谈谈你对该岗位的理解。"
            
    return random.choice(questions) if questions else "请谈谈你对该岗位的理解。"

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
        total_rounds=data.total_rounds,
        status="in_progress"
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # Round 0: Only Introduction request (First sentence, no questions yet)
    greeting = f"你好，我是你的{data.role}面试官。很高兴见到你。本次面试共设定为 {data.total_rounds} 轮提问。在正式开始前，请先做一个简单的自我介绍。"
    ai_msg = models.Message(interview_id=new_interview.id, sender="ai", content=greeting, category="introduction")
    db.add(ai_msg)
    db.commit()

    return new_interview

@router.get("/roles/{role_key}/sections")
def get_role_sections(role_key: str):
    # Dynamic extraction of sections from consolidated questions.json
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    questions_file = os.path.join(os.path.dirname(backend_path), "knowledge-base", role_key, "questions.json")
    
    sections = set()
    if os.path.exists(questions_file):
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                questions = json.load(f)
                for q in questions:
                    if "section" in q:
                        sections.add(q["section"])
        except Exception as e:
            print(f"Error extracting sections for {role_key}: {e}")
    
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
    
    polished_text = await polish_text(text)
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
        raw_transcript = stt_service.transcribe(temp_file_path)
        if not raw_transcript:
            raise HTTPException(status_code=400, detail="语音转录失败，请重试或手动输入")
        
        # 3. AI Polish for punctuation and homophone correction
        transcript = await polish_text(raw_transcript)
        
        # 4. Process the polished text as a message
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
    # 1. Fetch interview context
    interview = db.query(models.Interview).filter(models.Interview.id == interview_id, models.Interview.user_id == user_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

    # 2. Save User Message
    user_msg = models.Message(interview_id=interview_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()

    # 3. Analyze History
    messages = db.query(models.Message).filter(models.Message.interview_id == interview_id).order_by(models.Message.created_at.asc()).all()
    ai_msgs = [m for m in messages if m.sender == "ai"]
    
    # Identify "Main Questions" (Initial question + Stage transitions)
    # We define a "Main Question" as one that moved the dial.
    # In our new logic, we will tag messages to help us. 
    # For now, let's look at how many times we've moved to a NEXT_TOPIC.
    
    main_questions_asked = []
    current_follow_up_count = 0
    
    for m in ai_msgs[1:]: # Skip intro
        if m.category and "FOLLOW_UP" not in m.category:
            main_questions_asked.append(m)
            current_follow_up_count = 0
        else:
            current_follow_up_count += 1

    question_count = len(main_questions_asked)
    n = interview.total_rounds or 6
    
    # 4. Determine Stage & Next Target
    # Stage 1: scenario, Stage 2: problem_solving
    current_stage = "business_scenario" if question_count < n // 2 else "problem_solving"
    
    # If we are in the middle of a question, we might want the next one ready
    role_info = next((r for r in ROLES if r["name"] == interview.role), None)
    role_key = role_info["key"] if role_info else "java-backend"
    kp_list = json.loads(interview.knowledge_points) if interview.knowledge_points else []
    
    # Logic for picking the "Next Target"
    potential_next = get_questions_by_category(role_key, current_stage, interview.difficulty, kp_list)
    # Filter out already asked
    asked_titles = [m.content.split("接下来，")[-1] for m in main_questions_asked] # Simple heuristic
    available_next = [q for q in potential_next if q["question"] not in asked_titles]
    target_q_obj = random.choice(available_next if available_next else potential_next)
    
    # 5. Prepare LLM Context
    history_str = ""
    for m in messages[-6:]: # Last 3 rounds
        role_name = "面试官" if m.sender == "ai" else "候选人"
        history_str += f"{role_name}: {m.content}\n"

    last_main_q = main_questions_asked[-1] if main_questions_asked else ai_msgs[0]
    
    force_next = ""
    if current_follow_up_count >= 2:
        force_next = "【系统指令：强制切换】当前话题已追问满 2 次，请务必结束当前话题，给出一个简短评价并过渡到下一个问题。"

    # Check if this is the absolute last round
    is_final_move = False
    if question_count >= n:
        is_final_move = True
        target_next_text = "面试即将结束，请做一个结语。"
        force_next = "【系统指令：面试结束】请给出一个礼貌的结束语表示感谢。禁止再提出任何新问题或引导后续对话内容。"
    else:
        target_next_text = target_q_obj["question"]

    # 6. Generate AI Response
    llm_resp = await generate_llm_response(
        role=interview.role,
        question=last_main_q.content,
        expected_points="技术准确性、实践经验", # Can be more dynamic if we store key_points
        conversation_history=history_str,
        target_next_question=target_next_text,
        difficulty=interview.difficulty,
        knowledge_points=interview.knowledge_points,
        force_next_instruction=force_next
    )

    # 7. Update State
    final_is_ended = False
    # Only end if we have asked exactly N main questions AND the AI says MOVE_NEXT (meaning no more follow-ups for the last question)
    if question_count >= n and llm_resp["action"] == "MOVE_NEXT":
        final_is_ended = True
        interview.status = "completed"
        db.commit()

    # Save AI Message
    # Category tag: "Main" vs "FollowUp"
    msg_category = current_stage
    if llm_resp["action"] == "FOLLOW_UP":
        msg_category = f"{current_stage}_FOLLOW_UP"

    ai_msg = models.Message(
        interview_id=interview_id,
        sender="ai",
        content=llm_resp["text"],
        category=msg_category
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    # 8. Format Response for Schema
    # MessageResponse expects id, sender, content, created_at, and is_final.
    response = schemas.MessageResponse.model_validate(ai_msg)
    response.is_final = final_is_ended
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
            difficulty=e.interview.difficulty,
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
    eval_record = models.Evaluation(
        interview_id=interview_id,
        content_score=evaluation_data["content_score"],
        expression_score=evaluation_data["expression_score"],
        business_scenario_score=evaluation_data["business_scenario_score"],
        problem_solving_score=evaluation_data["problem_solving_score"],
        total_score=evaluation_data["total_score"],
        report_json=json.dumps(evaluation_data),
        recommendations=evaluation_data["recommendations"]
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)
    
    # 4. Prepare response data
    evaluation_result = {
        "interview_id": interview_id,
        "role": interview.role,
        "content_score": evaluation_data["content_score"],
        "expression_score": evaluation_data["expression_score"],
        "business_scenario_score": evaluation_data["business_scenario_score"],
        "problem_solving_score": evaluation_data["problem_solving_score"],
        "total_score": evaluation_data["total_score"],
        "highlights": evaluation_data["highlights"],
        "weaknesses": evaluation_data["weaknesses"],
        "recommendations": evaluation_data["recommendations"],
        "created_at": eval_record.created_at
    }

    return {"message": "Interview ended and evaluated successfully.", "evaluation": evaluation_result}

    return {"message": "Interview ended and evaluated successfully.", "evaluation": evaluation_result}
