import os
from pathlib import Path
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import models
from app.db.default_code_problem_bank import get_default_code_problems
from app.db.seed_code_problems import seed_code_problems


def _build_alembic_config(db_path: Path) -> Config:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    return config


def test_seed_code_problems_is_idempotent():
    fd, raw_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_path = Path(raw_path)
    original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    engine = None
    try:
        command.upgrade(_build_alembic_config(db_path), "head")

        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        expected_problems = get_default_code_problems()
        expected_problem_count = len(expected_problems)

        with SessionLocal() as db:
            seed_code_problems(db)
            first_problem_count = db.query(models.CodeProblem).count()
            first_case_count = db.query(models.CodeTestCase).count()

            seed_code_problems(db)
            second_problem_count = db.query(models.CodeProblem).count()
            second_case_count = db.query(models.CodeTestCase).count()

        assert first_problem_count == expected_problem_count
        assert second_problem_count == first_problem_count
        assert second_case_count == first_case_count
        assert expected_problem_count == 10
    finally:
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url
        if engine is not None:
            engine.dispose()
        db_path.unlink(missing_ok=True)
