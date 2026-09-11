from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "papers"
    / "sample.pdf"
)

def test_upload_pdf():

    with open(PDF_PATH, "rb") as pdf:

        response = client.post(
            "/papers/upload",
            files={
                "file": (
                    "sample.pdf",
                    pdf,
                    "application/pdf"
                )
            }
        )

    print("\n========== UPLOAD ==========")
    print(response.json())

    assert response.status_code == 200

    data = response.json()

    assert data["paper_id"]
    assert data["pages"] > 0
    assert data["chunks"] > 0