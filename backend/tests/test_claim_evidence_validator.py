from app.services.claims.evidence_validator import quote_is_supported, locate_quote


def test_quote_verification_exact_and_normalized():
    source = "Model A achieved 91% accuracy on Dataset X."
    assert quote_is_supported("Model A achieved 91% accuracy on Dataset X.", source)
    assert quote_is_supported("model a achieved 91% accuracy on dataset x", source)
    assert not quote_is_supported("Model B achieved 99% accuracy.", source)


def test_locate_quote_offsets():
    source = "Results: Model A achieved 91% accuracy."
    start, end = locate_quote("Model A achieved 91% accuracy.", source)
    assert source[start:end] == "Model A achieved 91% accuracy."


def test_claims_without_source_quote_are_rejected(monkeypatch):
    from app.services.claims.claim_extractor import ClaimExtractor

    class FakeLLM:
        def generate(self, prompt):
            return '''{"claims":[
              {"claim":"The proposed method improves performance.",
               "claim_type":"finding",
               "evidence_quote":"This sentence is not in the source.",
               "conditions":{},"limitations":null,"confidence":0.9},
              {"claim":"Model A achieved 91% accuracy.",
               "claim_type":"finding",
               "evidence_quote":"Model A achieved 91% accuracy on Dataset X.",
               "conditions":{"dataset":"Dataset X","metric":"accuracy"},
               "limitations":null,"confidence":0.95}
            ]}'''

    extractor = ClaimExtractor.__new__(ClaimExtractor)
    extractor.llm = FakeLLM()
    result = extractor.extract_from_chunk({
        "paper_id": "paper1", "page_number": 3, "chunk_id": 2,
        "text": "Model A achieved 91% accuracy on Dataset X."
    })
    assert len(result) == 1
    assert result[0]["claim_text"] == "Model A achieved 91% accuracy."
    assert result[0]["page_number"] == 3
