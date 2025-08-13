from dataclasses import dataclass
import os
@dataclass(frozen=True)
class Settings:
    tmdb_token: str = os.environ.get("TMDB_TOKEN", "")
    db_host: str = os.environ.get("DB_HOST", "localhost")
    db_port: int = int(os.environ.get("DB_PORT", "5432"))
    db_name: str = os.environ.get("DB_NAME", "tmdb")
    db_user: str = os.environ.get("DB_USER", "tmdb")
    db_password: str = os.environ.get("DB_PASSWORD", "tmdb")
    max_pages: int = int(os.environ.get("MAX_PAGES", "1"))
    sleep_between_req_ms: int = int(os.environ.get("SLEEP_BETWEEN_REQ_MS", "250"))
    @property
    def pg_dsn(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
SETTINGS = Settings()
