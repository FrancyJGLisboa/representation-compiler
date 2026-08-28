"""SQLite audit store. Sources and review events are append-only records."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .extraction import ClaimProposal, ProposalBatch, ProposalStatus
from .model import CanonicalModel
from .model import Assertion, AssertionStatus, Evidence, Origin, Entity


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS proposal_batches (
  id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(id), model TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS batch_entities (
  batch_id TEXT NOT NULL REFERENCES proposal_batches(id), id TEXT NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL,
  PRIMARY KEY(batch_id, id)
);
CREATE TABLE IF NOT EXISTS proposals (
  id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES proposal_batches(id), subject TEXT NOT NULL,
  predicate TEXT NOT NULL, object TEXT NOT NULL, evidence_excerpt TEXT NOT NULL, confidence REAL NOT NULL,
  rationale TEXT NOT NULL, status TEXT NOT NULL, reviewer TEXT, reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS review_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, proposal_id TEXT NOT NULL REFERENCES proposals(id), decision TEXT NOT NULL,
  reviewer TEXT NOT NULL, occurred_at TEXT NOT NULL, proposal_snapshot TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approved_claims (
  assertion_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES proposal_batches(id), proposal_id TEXT NOT NULL REFERENCES proposals(id),
  committed_at TEXT NOT NULL, assertion_json TEXT NOT NULL, evidence_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS representation_tournaments (
  id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES proposal_batches(id), objective TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS representation_candidates (
  tournament_id TEXT NOT NULL REFERENCES representation_tournaments(id), candidate_id TEXT NOT NULL, rank INTEGER NOT NULL,
  candidate_json TEXT NOT NULL, PRIMARY KEY(tournament_id, candidate_id)
);
CREATE TABLE IF NOT EXISTS learning_sessions (
  id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES proposal_batches(id), goal TEXT NOT NULL, familiarity TEXT NOT NULL, question TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES learning_sessions(id), candidate_id TEXT NOT NULL, reaction TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS explanations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES learning_sessions(id), answer TEXT NOT NULL, confidence REAL NOT NULL, score REAL NOT NULL, missing_terms TEXT NOT NULL, next_candidate_id TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class SQLiteStore:
    def __init__(self, path: str | Path = "representation_compiler.db"):
        database_path = Path(path)
        if database_path.parent != Path("."):
            database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def create_batch(self, source_id: str, source_text: str, model: str, batch: ProposalBatch) -> str:
        now, batch_id = _now(), f"batch-{uuid.uuid4().hex}"
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO sources(id, content, created_at) VALUES (?, ?, ?)", (source_id, source_text, now))
            self.connection.execute("INSERT INTO proposal_batches(id, source_id, model, created_at) VALUES (?, ?, ?, ?)", (batch_id, source_id, model, now))
            self.connection.executemany(
                "INSERT INTO proposals(id, batch_id, subject, predicate, object, evidence_excerpt, confidence, rationale, status, reviewer, reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(p.id, batch_id, p.subject, p.predicate, p.object, p.evidence_excerpt, p.confidence, p.rationale, p.status, p.reviewer, p.reviewed_at) for p in batch.proposals],
            )
            self.connection.executemany("INSERT INTO batch_entities(batch_id, id, name, type) VALUES (?, ?, ?, ?)", [(batch_id, item["id"], item["name"], item["type"]) for item in batch.entities])
        return batch_id

    def record_review(self, batch_id: str, proposal: ClaimProposal) -> None:
        if proposal.status is ProposalStatus.PENDING or not proposal.reviewer or not proposal.reviewed_at:
            raise ValueError("only a completed human review can be persisted")
        with self.connection:
            self.connection.execute(
                "UPDATE proposals SET subject=?, predicate=?, object=?, evidence_excerpt=?, confidence=?, rationale=?, status=?, reviewer=?, reviewed_at=? WHERE id=? AND batch_id=?",
                (proposal.subject, proposal.predicate, proposal.object, proposal.evidence_excerpt, proposal.confidence, proposal.rationale, proposal.status, proposal.reviewer, proposal.reviewed_at, proposal.id, batch_id),
            )
            self.connection.execute(
                "INSERT INTO review_events(proposal_id, decision, reviewer, occurred_at, proposal_snapshot) VALUES (?, ?, ?, ?, ?)",
                (proposal.id, proposal.status, proposal.reviewer, proposal.reviewed_at, json.dumps(asdict(proposal), default=str, sort_keys=True)),
            )

    def save_proposal(self, batch_id: str, proposal: ClaimProposal) -> None:
        """Persist an edit even if the reviewer leaves the proposal pending."""
        with self.connection:
            self.connection.execute(
                "UPDATE proposals SET subject=?, predicate=?, object=?, evidence_excerpt=?, confidence=?, rationale=?, status=?, reviewer=?, reviewed_at=? WHERE id=? AND batch_id=?",
                (proposal.subject, proposal.predicate, proposal.object, proposal.evidence_excerpt, proposal.confidence, proposal.rationale, proposal.status, proposal.reviewer, proposal.reviewed_at, proposal.id, batch_id),
            )

    def record_commits(self, batch_id: str, model: CanonicalModel, assertion_ids: list[str]) -> None:
        with self.connection:
            for assertion_id in assertion_ids:
                assertion = model.assertions[assertion_id]
                proposal_id = assertion_id.removeprefix("as-")
                evidence = model.evidence[assertion.evidence_ids[0]]
                self.connection.execute(
                    "INSERT INTO approved_claims(assertion_id, batch_id, proposal_id, committed_at, assertion_json, evidence_json) VALUES (?, ?, ?, ?, ?, ?)",
                    (assertion_id, batch_id, proposal_id, _now(), json.dumps(asdict(assertion), default=str, sort_keys=True), json.dumps(asdict(evidence), default=str, sort_keys=True)),
                )

    def record_tournament(self, batch_id: str, objective: str, candidates: list) -> str:
        tournament_id = f"tournament-{uuid.uuid4().hex}"
        with self.connection:
            self.connection.execute("INSERT INTO representation_tournaments(id, batch_id, objective, created_at) VALUES (?, ?, ?, ?)", (tournament_id, batch_id, objective, _now()))
            self.connection.executemany("INSERT INTO representation_candidates(tournament_id, candidate_id, rank, candidate_json) VALUES (?, ?, ?, ?)", [(tournament_id, candidate.id, index, json.dumps(candidate.to_dict(), sort_keys=True)) for index, candidate in enumerate(candidates, 1)])
        return tournament_id

    def create_learning_session(self, batch_id: str, goal: str, familiarity: str, question: str) -> str:
        session_id = f"learn-{uuid.uuid4().hex}"
        with self.connection:
            self.connection.execute("INSERT INTO learning_sessions(id, batch_id, goal, familiarity, question, created_at) VALUES (?, ?, ?, ?, ?, ?)", (session_id, batch_id, goal, familiarity, question, _now()))
        return session_id

    def record_learning_feedback(self, session_id: str, candidate_id: str, reaction: str) -> None:
        if reaction not in {"clicked", "too_abstract", "another_way", "go_deeper"}:
            raise ValueError("unsupported learning reaction")
        with self.connection:
            self.connection.execute("INSERT INTO learning_feedback(session_id, candidate_id, reaction, created_at) VALUES (?, ?, ?, ?)", (session_id, candidate_id, reaction, _now()))

    def record_explanation(self, session_id: str, answer: str, confidence: float, assessment) -> None:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        with self.connection:
            self.connection.execute("INSERT INTO explanations(session_id, answer, confidence, score, missing_terms, next_candidate_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (session_id, answer, confidence, assessment.score, json.dumps(assessment.missing_terms), assessment.next_representation_id, _now()))

    def learning_session(self, session_id: str) -> dict:
        row = self.connection.execute("SELECT * FROM learning_sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            raise KeyError(f"unknown learning session {session_id}")
        return dict(row)

    def latest_explanation(self, session_id: str) -> dict | None:
        row = self.connection.execute("SELECT * FROM explanations WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,)).fetchone()
        return dict(row) if row else None

    def batch_history(self, batch_id: str) -> dict:
        batch = self.connection.execute("SELECT * FROM proposal_batches WHERE id = ?", (batch_id,)).fetchone()
        if not batch:
            raise KeyError(f"unknown batch {batch_id}")
        source = self.connection.execute("SELECT * FROM sources WHERE id = ?", (batch["source_id"],)).fetchone()
        proposals = [dict(row) for row in self.connection.execute("SELECT * FROM proposals WHERE batch_id = ? ORDER BY id", (batch_id,))]
        events = [dict(row) for row in self.connection.execute("SELECT * FROM review_events WHERE proposal_id IN (SELECT id FROM proposals WHERE batch_id = ?) ORDER BY id", (batch_id,))]
        commits = [dict(row) for row in self.connection.execute("SELECT * FROM approved_claims WHERE batch_id = ? ORDER BY committed_at", (batch_id,))]
        return {"batch": dict(batch), "source": dict(source), "proposals": proposals, "review_events": events, "approved_claims": commits}

    def list_batches(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute(
            "SELECT b.id, b.source_id, b.model, b.created_at, COUNT(p.id) AS proposal_count, SUM(p.status = 'pending') AS pending_count FROM proposal_batches b LEFT JOIN proposals p ON p.batch_id = b.id GROUP BY b.id ORDER BY b.created_at DESC"
        )]

    def load_batch(self, batch_id: str) -> ProposalBatch:
        history = self.batch_history(batch_id)
        items = []
        for row in history["proposals"]:
            items.append(ClaimProposal(
                row["id"], row["subject"], row["predicate"], row["object"], row["evidence_excerpt"], row["confidence"], row["rationale"],
                ProposalStatus(row["status"]), row["reviewer"], row["reviewed_at"],
            ))
        return ProposalBatch(history["source"]["id"], history["source"]["content"], items)

    def hydrate_committed_claims(self, batch_id: str, model: CanonicalModel) -> CanonicalModel:
        """Rebuild claims for a persisted batch on a supplied entity/perspective context."""
        for entity in self.connection.execute("SELECT id, name, type FROM batch_entities WHERE batch_id = ?", (batch_id,)):
            model.entities[entity["id"]] = Entity(**dict(entity))
        for row in self.batch_history(batch_id)["approved_claims"]:
            assertion_data, evidence_data = json.loads(row["assertion_json"]), json.loads(row["evidence_json"])
            assertion_data["origin"] = Origin(assertion_data["origin"])
            assertion_data["status"] = AssertionStatus(assertion_data["status"])
            assertion_data["evidence_ids"] = tuple(assertion_data["evidence_ids"])
            assertion_data["relations"] = {key: tuple(value) for key, value in assertion_data["relations"].items()}
            model.evidence[evidence_data["id"]] = Evidence(**evidence_data)
            model.assertions[assertion_data["id"]] = Assertion(**assertion_data)
        model.validate()
        return model


def _now() -> str:
    return datetime.now(UTC).isoformat()
