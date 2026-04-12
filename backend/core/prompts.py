import os

class PromptManager:
    def __init__(self, prompt_file_path: str):
        self.prompt_file_path = prompt_file_path
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        if not os.path.exists(self.prompt_file_path):
            return
        
        with open(self.prompt_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Very basic parser for the markdown sections defined in system_prompts.md
        import re
        sections = re.split(r"## \d+\. ", content)
        for section in sections:
            if "System Prompt:" in section:
                title_match = re.search(r"^(.*?)\n", section)
                prompt_match = re.search(r"```text\n(.*?)\n```", section, re.DOTALL)
                if title_match and prompt_match:
                    title = title_match.group(1).strip()
                    prompt = prompt_match.group(1).strip()
                    if "面试官" in title:
                        self.prompts["interviewer"] = prompt
                    elif "评估" in title:
                        self.prompts["evaluator"] = prompt

    def get_interviewer_prompt(self, role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction="", rag_context=""):
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

    def get_evaluator_prompt(self, interview_transcript, excellent_answers_context):
        template = self.prompts.get("evaluator", "")
        return template.format(
            interview_transcript=interview_transcript,
            excellent_answers_context=excellent_answers_context
        )

PROMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base", "system_prompts.md"))
prompt_manager = PromptManager(PROMPT_FILE)
