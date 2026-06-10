import json
from collections import Counter
from pathlib import Path


def test_each_existing_section_difficulty_combo_has_at_least_five_questions():
    root = Path(__file__).resolve().parents[2] / "knowledge-base"
    for role in ["java-backend", "web-frontend", "python-algorithm"]:
        data = json.loads((root / role / "questions.json").read_text(encoding="utf-8"))
        combo_counts = Counter((item["section"], item["difficulty"]) for item in data)
        assert combo_counts, f"{role} 题库为空"
        assert min(combo_counts.values()) >= 5, f"{role} 存在题量不足 5 的组合: {combo_counts}"

