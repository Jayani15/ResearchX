
import pytest

from app.services.insights.insight_service import InsightService

def test_parse_json_plain_object():
    parsed = InsightService._parse_json(
        '{"insights": []}'
    )

    assert parsed == {"insights": []}

def test_parse_json_markdown_fence():
    parsed = InsightService._parse_json(
        '```json\n{"insights": []}\n```'
    )

    assert parsed == {"insights": []}

def test_parse_json_rejects_invalid_content():
    with pytest.raises(ValueError):
        InsightService._parse_json("not json")
