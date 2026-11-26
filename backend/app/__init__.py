from dotenv import load_dotenv
from pathlib import Path

# backend/app/__init__.py -> repository root is parents[2]
load_dotenv(Path(__file__).resolve().parents[2] / ".env")