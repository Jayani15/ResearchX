from app.services.knowledge_graph.graph_builder import build_claim_graph, graph_to_dict


def test_graph_builder():
    claims = [
        {"id": "a", "claim_text": "A outperforms B", "paper_id": "p1", "claim_type": "finding", "conditions": {}},
        {"id": "b", "claim_text": "B outperforms A", "paper_id": "p2", "claim_type": "finding", "conditions": {}},
    ]
    relationships = [{
        "id": "r1", "source_claim_id": "a", "target_claim_id": "b",
        "relationship_type": "potential_conflict", "explanation": "Conditions unclear",
        "similarity": 0.8, "condition_differences": {},
    }]
    graph = build_claim_graph(claims, relationships)
    payload = graph_to_dict(graph)
    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1
    assert payload["edges"][0]["relationship_type"] == "potential_conflict"