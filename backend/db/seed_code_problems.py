import json

from app.db import models
from db.default_code_problem_bank import get_default_code_problems


def _dump(value):
    return json.dumps(value, ensure_ascii=False)


def _remove_retired_hot100_problems(db, active_problem_ids):
    retired_problems = (
        db.query(models.CodeProblem)
        .filter(models.CodeProblem.source == "Hot100")
        .filter(models.CodeProblem.id.notin_(active_problem_ids))
        .all()
    )
    for problem in retired_problems:
        db.query(models.CodeTestCase).filter(models.CodeTestCase.problem_id == problem.id).delete(
            synchronize_session=False
        )
        has_submission = (
            db.query(models.CodeSubmission.id)
            .filter(models.CodeSubmission.problem_id == problem.id)
            .first()
        )
        if has_submission:
            problem.is_active = False
        else:
            db.delete(problem)


def seed_code_problems(db):
    """Insert or refresh the default ACM problem metadata and test cases."""
    problems = get_default_code_problems()
    active_problem_ids = [item["id"] for item in problems]
    _remove_retired_hot100_problems(db, active_problem_ids)

    for order_index, item in enumerate(problems, start=1):
        problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == item["id"]).first()
        fields = {
            "title": item["title"],
            "slug": item["slug"],
            "difficulty": item["difficulty"],
            "tags": _dump(item["tags"]),
            "description": item["description"],
            "input_format": item["input_format"],
            "output_format": item["output_format"],
            "samples": _dump(item["samples"]),
            "constraints": _dump(item["constraints"]),
            "starter_code": _dump(item["starter_code"]),
            "source": "Hot100",
            "is_active": True,
            "order_index": order_index,
        }

        if problem is None:
            problem = models.CodeProblem(id=item["id"], **fields)
            db.add(problem)
            db.flush()
        else:
            for key, value in fields.items():
                setattr(problem, key, value)

        db.query(models.CodeTestCase).filter(models.CodeTestCase.problem_id == problem.id).delete()
        for case_index, case in enumerate(item["test_cases"], start=1):
            db.add(
                models.CodeTestCase(
                    problem_id=problem.id,
                    input=case["input"],
                    expected_output=case["expected_output"],
                    is_sample=bool(case.get("is_sample")),
                    explanation=case.get("explanation"),
                    sort_order=case_index,
                )
            )

    db.commit()
