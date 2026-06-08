from app.config.settings import Settings


def test_settings_normalizes_managed_postgres_url():
    settings = Settings(database_url="postgresql://user:pass@host:5432/db")

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_settings_keeps_explicit_sqlalchemy_driver_url():
    settings = Settings(database_url="postgresql+psycopg://user:pass@host:5432/db")

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"
