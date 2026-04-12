import os
import json
from openai import AsyncOpenAI
from core.config import settings
from core.prompts import prompt_manager
from services.rag_service import rag_service

# Initialize the OpenAI-compatible client
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL
)

async def generate_llm_response(role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction=""):
    """
    Generate conversational follow-up or next question using AI logic.
    Returns: {"action": "FOLLOW_UP" | "MOVE_NEXT", "text": "..."}
    """
    # 1. Query RAG for expert context
    # Use the current question and the last user message as query for better relevance
    last_user_msg = ""
    if isinstance(conversation_history, list):
        for msg in reversed(conversation_history):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
    elif isinstance(conversation_history, str):
        # Extract the last "候选人" (Candidate) message from the formatted string
        lines = conversation_history.strip().split("\n")
        for line in reversed(lines):
            if "候选人:" in line:
                last_user_msg = line.split("候选人:")[-1].strip()
                break
            
    rag_query = f"{question} {last_user_msg}"
    rag_context = await rag_service.query_context_async(rag_query)

    # 2. Get system prompt template
    system_prompt = prompt_manager.get_interviewer_prompt(
        role=role,
        question=question,
        expected_points=expected_points,
        conversation_history=conversation_history,
        target_next_question=target_next_question,
        difficulty=difficulty,
        knowledge_points=knowledge_points,
        force_next_instruction=force_next_instruction,
        rag_context=rag_context
    )
    
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "action": data.get("action", "MOVE_NEXT"),
            "text": data.get("text", "好了，我们进行下一个话题。")
        }
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {
            "action": "MOVE_NEXT",
            "text": "抱歉，刚才信号有点不好。我们直接看下一个话题： " + target_next_question
        }

async def polish_text(text: str):
    """
    Add punctuation and fix minor typos in transcribed text.
    """
    if not text.strip():
        return text
        
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的语音转文字校对专家。你的任务是对面试者的语音转录结果进行微调：1. 加入恰当的中文标点符号。2. 修正明显的谐音错误或技术词错误（例如将“加瓦”修正为“Java”）。3. **保留**原句的所有信息、语气词和口语化倾向（如“呃”、“那个”、“然后”等），不要进行任何润色或改写。4. 保持最小限度的修改，只做必要的纠错和标点添加。直接返回处理后的文本。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error polishing text: {e}")
        return text

async def evaluate_full_interview(history: list):
    """
    Generate the final evaluation report for the complete interview.
    """
    # 1. Build a rich transcript with categories and context
    transcript_parts = []
    for m in history:
        if m.sender == "ai":
            category_text = f"【分类: {m.category}】" if m.category else ""
            transcript_parts.append(f"面试官: {m.content} {category_text}")
        else:
            transcript_parts.append(f"面试者: {m.content}")
    
    transcript = "\n".join(transcript_parts)
    
    # 2. Get system prompt with the new structure
    system_prompt = prompt_manager.get_evaluator_prompt(
        interview_transcript=transcript,
        excellent_answers_context="（参考 questions.json 中的 key_points）"
    )
    
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        # 3. Process the evaluations to get the average
        evals = data.get("evaluations", [])
        scores = {
            "content_score": [],
            "expression_score": [],
            "business_scenario_score": [],
            "problem_solving_score": []
        }
        
        for e in evals:
            for k in scores.keys():
                val = e.get(k)
                if val is not None and isinstance(val, (int, float)):
                    scores[k].append(val)
        
        # Calculate averages for non-null values
        final_scores = {}
        for k, v in scores.items():
            final_scores[k] = round(sum(v) / len(v), 1) if v else 0.0
            
        # Total score is average of the averages
        active_averages = [v for v in final_scores.values() if v > 0]
        total_score = round(sum(active_averages) / len(active_averages), 1) if active_averages else 0.0
        
        summary = data.get("overall_summary", {})
        
        return {
            "content_score": final_scores["content_score"],
            "expression_score": final_scores["expression_score"],
            "business_scenario_score": final_scores["business_scenario_score"],
            "problem_solving_score": final_scores["problem_solving_score"],
            "total_score": total_score,
            "highlights": summary.get("strengths", []),
            "weaknesses": summary.get("weaknesses", []),
            "recommendations": summary.get("recommendations", "继续努力！")
        }
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return {
            "content_score": 0, "expression_score": 0, "business_scenario_score": 0, "problem_solving_score": 0,
            "total_score": 0, "highlights": ["评估生成失败"], "weaknesses": [], "recommendations": "请重试。"
        }
