from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

PAPERS_DIR = DATA_DIR / "papers"

PROCESSED_DIR = DATA_DIR / "processed"

VECTOR_STORE_DIR = DATA_DIR / "vector_store"