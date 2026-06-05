import os
from pathlib import Path
import sys
import tempfile
import uuid

from alembic import command
from alembic.config import Config

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"interview_echo_test_{uuid.uuid4().hex}.db"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
ALEMBIC_INI_PATH = Path(__file__).resolve().parents[1] / "alembic.ini"
ALEMBIC_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "alembic"

from app.db.seed_code_problems import seed_code_problems
from app.db.session import SessionLocal


def _build_alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_PATH))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    return config


def pytest_sessionstart(session):
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)
    command.upgrade(_build_alembic_config(), "head")
    db = SessionLocal()
    try:
        seed_code_problems(db)
    finally:
        db.close()
