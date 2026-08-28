from representation_compiler.extraction import batch_from_agent_file


def test_host_agent_file_creates_pending_review_proposals():
    batch = batch_from_agent_file({
        "source_id": "email-thread", "source_text": "Project Alpha depends on API v2.", "entities": [{"id": "project-alpha", "name": "Project Alpha", "type": "project"}],
        "claims": [{"subject": "project-alpha", "predicate": "depends_on", "object": "API v2", "evidence_excerpt": "Project Alpha depends on API v2.", "confidence": .9, "rationale": "Explicit statement."}],
    })
    assert batch.source_id == "email-thread"
    assert batch.proposals[0].status == "pending"
    assert batch.entities[0]["id"] == "project-alpha"
