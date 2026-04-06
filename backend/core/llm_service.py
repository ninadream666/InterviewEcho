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

async def generate_llm_response(role: str, question: str, expected_points: str, candidate_response: str, difficulty: str = "medium", knowledge_points: str = ""):
    """
    Generate conversational follow-up or answer evaluation using real LLM.
    """
    # 1. Query RAG for context
    rag_context = rag_service.query_context(f"{role} {question}")
    
    # 2. Get system prompt template
    system_prompt = prompt_manager.get_interviewer_prompt(
        role=role,
        question=question,
        expected_points=expected_points,
        rag_context=rag_context,
        candidate_response=candidate_response,
        difficulty=difficulty,
        knowledge_points=knowledge_points
    )
    
    # 3. Request LLM
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": candidate_response}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return "很抱歉，当前面试官遇到点小故障，请您稍后再试。"

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
                {"role": "system", "content": "你是一个文本纠错专家。请为以下没有标点符号的面试回答添加合适的中文标点，并修正明显的音近错别字。保持原意不变，不要增加额外内容，只返回处理后的文本。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error polishing text: {e}")
        return text

async def evaluate_full_interview(interview_history: list):
    """
    Generate the final evaluation report for the complete interview.
    """
    transcript = "\n".join([f"{m.sender}: {m.content}" for m in interview_history])
    
    # Optional: fetch excellent answers context from RAG
    excellent_answers = rag_service.query_context("优秀回答范例 / 最佳实践", k=5)
    
    system_prompt = prompt_manager.get_evaluator_prompt(
        interview_transcript=transcript,
        excellent_answers_context=excellent_answers
    )
    
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating report: {e}")
        # Return a fallback evaluation structure
        return {
            "scores": {"technical_depth": 0, "business_scenario": 0, "problem_solving": 0, "communication": 0},
            "strengths": ["数据生成异常"],
            "weaknesses": ["系统暂无法给出精准评估"],
            "improvement_suggestions": "请检查大模型接口配置。"
        }
