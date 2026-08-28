from representation_compiler.extraction import ClaimProposal, ProposalBatch, ProposalStatus, apply_approved, review
from representation_compiler.fixtures import project_alpha
from representation_compiler.store import SQLiteStore
from representation_compiler.discovery import discover
from representation_compiler.learning import ExplanationAssessment


def batch():
    return ProposalBatch("source-1", "Alpha depends on API v2.", [
        ClaimProposal("pr-source-1-1", "project-alpha", "depends_on", "API v2", "Alpha depends on API v2.", .9, "explicit"),
    ])


def test_store_persists_source_proposal_review_and_commit(tmp_path):
    database = SQLiteStore(tmp_path / "history.db")
    proposals, model = batch(), project_alpha()
    batch_id = database.create_batch(proposals.source_id, proposals.source_text, "test-model", proposals)
    proposal = proposals.proposals[0]
    proposal.object = "API v2 (confirmed)"
    database.save_proposal(batch_id, proposal)
    review(proposals, proposal.id, ProposalStatus.APPROVED, "Fran")
    database.record_review(batch_id, proposal)
    committed = apply_approved(model, proposals)
    database.record_commits(batch_id, model, committed)
    history = database.batch_history(batch_id)
    database.close()

    assert history["source"]["content"] == "Alpha depends on API v2."
    assert history["proposals"][0]["object"] == "API v2 (confirmed)"
    assert history["review_events"][0]["decision"] == "approved"
    assert history["approved_claims"][0]["assertion_id"] == committed[0]


def test_pending_edit_is_saved_without_a_review_event(tmp_path):
    database = SQLiteStore(tmp_path / "history.db")
    proposals = batch()
    batch_id = database.create_batch(proposals.source_id, proposals.source_text, "test-model", proposals)
    proposals.proposals[0].rationale = "edited rationale"
    database.save_proposal(batch_id, proposals.proposals[0])
    history = database.batch_history(batch_id)
    database.close()
    assert history["proposals"][0]["rationale"] == "edited rationale"
    assert history["review_events"] == []


def test_store_hydrates_entities_from_agent_batch(tmp_path):
    database = SQLiteStore(tmp_path / "history.db")
    proposals = ProposalBatch("new-source", "Beta depends on vendor.", [], [{"id": "project-beta", "name": "Project Beta", "type": "project"}])
    batch_id = database.create_batch(proposals.source_id, proposals.source_text, "agent", proposals)
    model = database.hydrate_committed_claims(batch_id, project_alpha())
    database.close()
    assert model.entities["project-beta"].name == "Project Beta"


def test_store_persists_representation_tournament(tmp_path):
    database = SQLiteStore(tmp_path / "history.db")
    proposals = batch()
    batch_id = database.create_batch(proposals.source_id, proposals.source_text, "agent", proposals)
    tournament_id = database.record_tournament(batch_id, "Where do teams disagree?", discover(project_alpha(), "Where do teams disagree?"))
    count = database.connection.execute("SELECT COUNT(*) FROM representation_candidates WHERE tournament_id = ?", (tournament_id,)).fetchone()[0]
    database.close()
    assert count == 5


def test_store_persists_learning_session_and_explanation(tmp_path):
    database = SQLiteStore(tmp_path / "history.db")
    proposals = batch()
    batch_id = database.create_batch(proposals.source_id, proposals.source_text, "agent", proposals)
    session_id = database.create_learning_session(batch_id, "Understand Alpha", "new", "How does it work?")
    assessment = ExplanationAssessment(.5, ("API v2",), "dependency-network")
    database.record_explanation(session_id, "Alpha has a dependency.", .4, assessment)
    saved = database.connection.execute("SELECT score, next_candidate_id FROM explanations WHERE session_id = ?", (session_id,)).fetchone()
    database.close()
    assert tuple(saved) == (.5, "dependency-network")
