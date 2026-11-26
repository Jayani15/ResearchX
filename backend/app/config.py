from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("RESEARCHX_DATA_DIR", PROJECT_ROOT / "data"))
PAPERS_DIR = DATA_DIR / "papers"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://researchx:researchx_dev_password@localhost:5432/researchx",
)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))