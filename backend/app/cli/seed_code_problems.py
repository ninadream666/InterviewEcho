from app.db.seed_code_problems import seed_code_problems
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        seed_code_problems(db)
        print("Code problem seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
