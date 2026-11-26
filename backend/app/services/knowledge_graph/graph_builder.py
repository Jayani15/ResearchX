import networkx as nx


def build_claim_graph(claims: list[dict], relationships: list[dict]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for claim in claims:
        graph.add_node(
            claim["id"],
            label=claim["claim_text"],
            paper_id=claim["paper_id"],
            claim_type=claim.get("claim_type", "other"),
            conditions=claim.get("conditions") or {},
        )
    for relationship in relationships:
        graph.add_edge(
            relationship["source_claim_id"],
            relationship["target_claim_id"],
            key=relationship["id"],
            relationship_type=relationship["relationship_type"],
            explanation=relationship["explanation"],
            similarity=relationship.get("similarity", 0.0),
            condition_differences=relationship.get("condition_differences") or {},
        )
    return graph


def graph_to_dict(graph: nx.MultiDiGraph) -> dict:
    return {
        "nodes": [
            {"id": node_id, **attributes}
            for node_id, attributes in graph.nodes(data=True)
        ],
        "edges": [
            {"id": key, "source": source, "target": target, **attributes}
            for source, target, key, attributes in graph.edges(keys=True, data=True)
        ],
    }