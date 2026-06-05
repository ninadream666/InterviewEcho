import os
from pathlib import Path
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_creates_expected_tables():
    fd, raw_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_path = Path(raw_path)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    engine = None
    try:
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "users",
            "questions",
            "interviews",
            "messages",
            "evaluations",
            "voice_metrics",
            "code_problems",
            "code_test_cases",
            "code_submissions",
        }.issubset(tables)
        interview_columns = {column["name"] for column in inspector.get_columns("interviews")}
        assert {
            "phase",
            "knowledge_round_index",
            "active_code_problem_id",
            "active_code_submission_id",
            "asked_question_titles",
        }.issubset(interview_columns)
    finally:
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url
        if engine is not None:
            engine.dispose()
        db_path.unlink(missing_ok=True)
