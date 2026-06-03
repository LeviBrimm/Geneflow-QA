from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_alembic_upgrade_creates_initial_schema(tmp_path, monkeypatch):
    database_path = tmp_path / "migration-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database_path}")
    inspector = inspect(engine)

    assert {
        "alembic_version",
        "users",
        "genes",
        "variants",
        "variant_queries",
        "analysis_jobs",
        "explanations",
        "variant_embeddings",
    }.issubset(set(inspector.get_table_names()))

    with engine.connect() as connection:
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()

    assert revision == "20260603_0001"
