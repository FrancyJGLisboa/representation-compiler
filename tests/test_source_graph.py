from representation_compiler.source_graph import enrich_notebook_payload, extract_source_graph


def test_ai_infrastructure_graph_has_evidence_backed_mechanism_edges():
    rows = ({"fragment_id": "one", "text": "A GPU needs VRAM. A model server performs prefill and keeps a KV cache before decode."}, {"fragment_id": "two", "text": "Batching, sharding, routing, llm-d, and Kubernetes operate the fleet."})

    graph = extract_source_graph(rows, "AI infrastructure")

    assert {"gpu", "vram", "prefill", "kv-cache", "decode", "routing", "kubernetes"} <= {node.id for node in graph.nodes}
    assert any(edge.source_id == "prefill" and edge.target_id == "kv-cache" for edge in graph.edges)
    assert all(node.evidence_ids for node in graph.nodes)


def test_existing_notebook_can_be_enriched_with_a_graph():
    payload = {"title": "Notes", "derived_data": {"source-items": {"rows": [{"fragment_id": "one", "text": "Ideas repeat. Ideas connect."}]}}, "representations": {"concept-map": {"family": "concept graph"}}}

    enriched = enrich_notebook_payload(payload)

    assert enriched["representations"]["concept-map"]["graph_id"] == "source-concept-graph"
    assert enriched["graphs"]["source-concept-graph"]["nodes"]
