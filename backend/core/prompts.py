"""
模块名称：提示词管理器（prompts）
功能描述：从 Markdown 文件中加载和管理 LLM 系统提示词模板。

工作原理：
1. 读取 knowledge-base/system_prompts.md 文件
2. 用正则解析各个 System Prompt 段落
3. 将模板按用途分类存储（面试官/评估者/简历解析/项目深挖/自由发挥/学习计划/表达分析）
4. 对外暴露 get_xxx_prompt() 方法，支持动态参数格式化

提示词模板命名规则：
- interviewer：面试官角色提示词
- evaluator：面试评估者角色提示词
- resume_parser：简历解析结构化提示词
- resume_question_gen：简历深挖问题生成
- repo_question_gen：项目深挖问题生成
- free_question：自由发挥知识题生成
- study_plan：学习计划生成
- expression_evaluator：表达评分提示词
"""

import os
import re


class PromptManager:
    """管理所有 LLM 系统提示词模板的加载与格式化。"""

    def __init__(self, prompt_file_path: str):
        """
        Args:
            prompt_file_path: system_prompts.md 文件的路径。
        """
        self.prompt_file_path = prompt_file_path
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        """从 Markdown 文件中解析所有 System Prompt 模板并存储到 self.prompts 字典。"""
        if not os.path.exists(self.prompt_file_path):
            return

        with open(self.prompt_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按 "## N. 标题" 分段
        sections = re.split(r"## \d+\. ", content)
        for section in sections:
            if "System Prompt:" in section:
                title_match = re.search(r"^(.*?)\n", section)
                prompt_match = re.search(r"```text\n(.*?)\n```", section, re.DOTALL)
                if title_match and prompt_match:
                    title = title_match.group(1).strip()
                    prompt = prompt_match.group(1).strip()
                    # 注意匹配顺序：先匹配具体的子类，再匹配普通的"评估/面试官"等泛词
                    if "学习计划" in title:
                        self.prompts["study_plan"] = prompt
                    elif "项目深挖" in title:
                        self.prompts["repo_question_gen"] = prompt
                    elif "表达分析" in title:
                        self.prompts["expression_evaluator"] = prompt
                    elif "简历提问" in title:
                        self.prompts["resume_question_gen"] = prompt
                    elif "简历" in title:
                        self.prompts["resume_parser"] = prompt
                    elif "自由发挥" in title:
                        self.prompts["free_question"] = prompt
                    elif "面试官" in title:
                        self.prompts["interviewer"] = prompt
                    elif "评估" in title:
                        self.prompts["evaluator"] = prompt

    # ============================================================
    # 各类 Prompt 获取方法
    # ============================================================

    def get_interviewer_prompt(self, role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction="", rag_context=""):
        """
        获取面试官角色的 System Prompt（已填入当前上下文）。

        Args:
            role: 岗位名称。
            question: 当前正在问的问题文本。
            expected_points: 期望候选人回答的关键点。
            conversation_history: 对话历史（list[dict] 或格式化字符串）。
            target_next_question: 下一道要问的题目文本。
            difficulty: 难度。
            knowledge_points: 知识点范围。
            force_next_instruction: 强制跳题指令（打断策略输出）。
            rag_context: RAG 检索到的知识库上下文。

        Returns:
            str: 格式化后的完整 System Prompt。
        """
        template = self.prompts.get("interviewer", "")
        return template.format(
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

    def get_evaluator_prompt(
        self,
        interview_transcript,
        excellent_answers_context="",
        role="",
        role_specific_criteria="",
        resume_summary="",
    ):
        """
        获取评估者角色的 System Prompt。

        Args:
            interview_transcript: 完整面试对话记录。
            excellent_answers_context: RAG 检索到的优秀回答参考。
            role: 岗位名称。
            role_specific_criteria: 岗位特定的评估侧重标准。
            resume_summary: 候选人结构化简历摘要。

        Returns:
            str: 格式化后的评估 Prompt。
        """
        template = self.prompts.get("evaluator", "")
        # 兼容老 prompt 不含某些占位符的情况：仅替换存在的占位符
        format_kwargs = {
            "interview_transcript": interview_transcript,
            "excellent_answers_context": excellent_answers_context,
            "role": role or "通用计算机岗位",
            "role_specific_criteria": role_specific_criteria or "（按通用计算机岗位标准评估）",
            "resume_summary": resume_summary or "（本场面试未提供简历画像）",
        }
        try:
            return template.format(**format_kwargs)
        except KeyError as e:
            # 如果模板里有未提供的占位符，转用 .replace 兜底
            result = template
            for k, v in format_kwargs.items():
                result = result.replace("{" + k + "}", str(v))
            return result

    def get_expression_evaluator_prompt(self):
        """
        获取表达分析评估专家的 Prompt。

        注意：此 Prompt 中没有动态变量占位符，且包含原生 JSON 格式，
        因此直接返回，避免使用 .format() 导致花括号冲突。
        """
        return self.prompts.get("expression_evaluator", "")

    def get_study_plan_prompt(self, role: str, evaluation_data: dict, transcript_excerpt: str) -> str:
        """
        获取学习计划生成的 Prompt。

        Args:
            role: 岗位。
            evaluation_data: evaluate_full_interview 返回的 dict。
            transcript_excerpt: 面试对话精选片段。
        """
        template = self.prompts.get("study_plan", "")
        if not template:
            return ""
        weaknesses = evaluation_data.get("weaknesses") or []
        weaknesses_list = "\n".join(f"- {w}" for w in weaknesses) if weaknesses else "（未识别到明显不足）"
        return template.format(
            role=role,
            total_score=evaluation_data.get("total_score", 0),
            content_score=evaluation_data.get("content_score", 0),
            expression_score=evaluation_data.get("expression_score", 0),
            business_scenario_score=evaluation_data.get("business_scenario_score", 0),
            problem_solving_score=evaluation_data.get("problem_solving_score", 0),
            weaknesses_list=weaknesses_list,
            transcript_excerpt=transcript_excerpt,
        )

    def get_resume_parser_prompt(self) -> str:
        """
        获取简历解析的 Prompt（无动态占位符，直接返回模板）。

        简历文本由 services.resume_parser.parse_resume_text 在 user message 中传入，
        不在 system prompt 中插值，避免 .format() 解析简历内容里的花括号导致报错。
        """
        return self.prompts.get("resume_parser", "")

    def get_repo_question_prompt(self, role: str, repo_summary: dict) -> str:
        """
        获取项目深挖问题生成的 Prompt。

        Args:
            role: 岗位名（如 "Java后端开发工程师"）。
            repo_summary: repo_analyzer.analyze_repo() 的返回值。
        """
        template = self.prompts.get("repo_question_gen", "")
        if not template:
            return ""

        # 格式化关键代码文件（每个加上 path 标记 + 代码围栏）
        key_files_str = ""
        for kf in (repo_summary.get("key_files") or []):
            path = kf.get("path", "")
            content = kf.get("content", "")
            if path and content:
                key_files_str += f"\n### 文件：{path}\n```\n{content}\n```\n"
        if not key_files_str.strip():
            key_files_str = "（未抓取到可用的代码文件）"

        return template.format(
            role=role,
            full_name=repo_summary.get("full_name", ""),
            description=repo_summary.get("description", ""),
            main_language=repo_summary.get("main_language", ""),
            languages=repo_summary.get("languages", {}),
            stars=repo_summary.get("stars", 0),
            tech_keywords=repo_summary.get("tech_keywords", []),
            top_level_files=repo_summary.get("top_level_files", []),
            recent_commits=repo_summary.get("recent_commits", []),
            readme_excerpt=repo_summary.get("readme_excerpt", ""),
            key_files=key_files_str,
        )

    def get_resume_question_prompt(self, persona: dict) -> str:
        """获取简历提问生成的 Prompt（纯按简历内容，不引入岗位角色）。"""
        template = self.prompts.get("resume_question_gen", "")
        if not template:
            return ""

        projects = persona.get("projects") or []
        projects_summary = ""
        for p in projects[:3]:
            name = p.get("name", "")
            tech = ", ".join(p.get("tech", [])[:4])
            highlights = p.get("highlights", "")
            role_in_proj = p.get("role", "")
            projects_summary += f"  * {name}"
            if role_in_proj:
                projects_summary += f" ({role_in_proj})"
            if tech:
                projects_summary += f"：{tech}"
            if highlights:
                projects_summary += f" - {highlights}"
            projects_summary += "\n"
        if not projects_summary:
            projects_summary = "（未提及具体项目）"

        return template.format(
            skills=", ".join(persona.get("skills", [])[:10]) or "（未提及）",
            projects_summary=projects_summary.strip(),
            work_years=str(persona.get("work_years", 0)),
            education=persona.get("education", "（未提及）"),
            summary=persona.get("summary", "（未提及）"),
        )

    def get_free_question_prompt(self, role: str, category: str, difficulty: str, asked_questions: str, knowledge_points: str) -> str:
        """获取自由发挥提问的 Prompt（题库耗尽时补位）。"""
        template = self.prompts.get("free_question", "")
        if not template:
            return ""
        return template.format(
            role=role,
            category=category,
            difficulty=difficulty,
            knowledge_points=knowledge_points or "不限",
            asked_questions=asked_questions or "（尚无已问问题）",
        )


# 全局单例：自动从 knowledge-base 加载提示词模板
PROMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base", "system_prompts.md"))
prompt_manager = PromptManager(PROMPT_FILE)
