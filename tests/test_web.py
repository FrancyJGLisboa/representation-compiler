import http.client
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

from representation_compiler.extraction import ClaimProposal, ProposalBatch
from representation_compiler.store import SQLiteStore
from representation_compiler.web import App


def test_browser_lists_and_reviews_persisted_proposals(tmp_path):
    database_path = tmp_path / "history.db"
    store = SQLiteStore(database_path)
    batch = ProposalBatch("source-web", "Project Alpha depends on API v2.", [
        ClaimProposal("pr-web-1", "project-alpha", "depends_on", "API v2", "Project Alpha depends on API v2.", .9, "explicit"),
    ])
    batch_id = store.create_batch(batch.source_id, batch.source_text, "test", batch)
    store.close()
    App.database_path = str(database_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), App)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 200
        assert b"source-web" in response.read()

        body = urlencode({"subject": "project-alpha", "predicate": "depends_on", "object": "API v2", "evidence_excerpt": "Project Alpha depends on API v2.", "confidence": "0.9", "rationale": "explicit", "reviewer": "Fran", "decision": "approved"})
        connection.request("POST", f"/batches/{batch_id}/proposals/pr-web-1", body, {"Content-Type": "application/x-www-form-urlencoded"})
        assert connection.getresponse().status == 303

        connection.request("GET", f"/batches/{batch_id}/diagrams/timeline?question=What%20changed%20over%20time%3F")
        response = connection.getresponse()
        assert response.status == 200
        assert b"<svg" in response.read()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    verified = SQLiteStore(database_path).batch_history(batch_id)
    assert verified["review_events"][0]["decision"] == "approved"
