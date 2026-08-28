"""Local, dependency-free browser UI for the representation compiler v0."""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .extraction import ProposalStatus, apply_approved, review
from .fixtures import empty_reality, project_alpha
from .store import SQLiteStore
from .views import search
from .diagrams import render as render_diagram
from .learning import assess_explanation, make_challenge, start_candidates


STYLE = """*{box-sizing:border-box}body{font:16px system-ui,sans-serif;max-width:1060px;margin:0 auto;padding:28px 20px 64px;background:#f6f5f2;color:#20252d}a{color:#184b9b;text-decoration:none}nav{display:flex;justify-content:space-between;margin-bottom:40px;font-size:14px}.eyebrow{font:11px ui-monospace,monospace;letter-spacing:.12em;color:#687386;text-transform:uppercase}.lead{font:20px Georgia,serif;color:#4f5d75;max-width:650px;line-height:1.45}.step{display:flex;gap:8px;margin:24px 0}.step span{padding:6px 10px;border:1px solid #d9e0e8;border-radius:99px;font-size:13px;color:#52606d}.step span:first-child{border-color:#eb6c36;color:#9a451f;background:#fff4ed}article{background:#fff;border:1px solid #d9e0e8;border-radius:12px;padding:20px;margin:14px 0}h1{font:400 42px Georgia,serif;letter-spacing:-.03em;margin:0 0 8px}h2{font-size:18px;margin:0 0 8px}small{color:#52606d}.pending{color:#a15c00}.approved{color:#087443}.rejected{color:#a61b1b}input,textarea,select,button{font:inherit;padding:10px;margin:5px 0;border-radius:7px;border:1px solid #c9d1db}input,textarea,select{width:100%;background:#fff}button{width:auto;background:#20252d;color:#fff;border-color:#20252d;cursor:pointer;margin-right:6px}button[value=clicked],button:first-of-type{background:#eb6c36;border-color:#eb6c36}textarea{min-height:110px}label{display:block;font-size:14px;font-weight:650;margin-top:10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.score{font:12px ui-monospace,monospace;color:#687386}.primary{border:2px solid #eb6c36}.muted{color:#52606d}details summary{cursor:pointer;color:#52606d}pre{white-space:pre-wrap;max-height:340px;overflow:auto;font-size:13px;line-height:1.45}"""


def page(title: str, body: str, subtitle: str = "") -> bytes:
    return f"<!doctype html><title>{escape(title)}</title><style>{STYLE}</style><nav><a href='/'>Representation Compiler</a><span class='eyebrow'>understanding workspace</span></nav><h1>{escape(title)}</h1><p class='lead'>{escape(subtitle)}</p>{body}".encode()


class App(BaseHTTPRequestHandler):
    database_path = "representation_compiler.db"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.batches()
        if parsed.path.startswith("/learning/"):
            return self.learning_session(parsed.path.split("/")[2])
        if parsed.path.startswith("/batches/"):
            if "/diagrams/" in parsed.path:
                parts = parsed.path.split("/")
                return self.diagram(parts[2], parts[4], parse_qs(parsed.query))
            return self.batch(parsed.path.split("/")[2], parse_qs(parsed.query))
        self.send_error(404)

    def do_POST(self):
        parts = self.path.strip("/").split("/")
        size = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(size).decode())
        if len(parts) == 4 and parts[0] == "batches" and parts[2] == "proposals":
            return self.decide(parts[1], parts[3], form)
        if len(parts) == 3 and parts[0] == "batches" and parts[2] == "learn":
            return self.start_learning(parts[1], form)
        if len(parts) == 3 and parts[0] == "learning" and parts[2] == "feedback":
            return self.learning_feedback(parts[1], form)
        if len(parts) == 3 and parts[0] == "learning" and parts[2] == "explain":
            return self.learning_explain(parts[1], form)
        if len(parts) == 3 and parts[0] == "batches" and parts[2] == "commit":
            return self.commit(parts[1])
        self.send_error(404)

    def batches(self):
        store = SQLiteStore(self.database_path)
        try:
            rows = store.list_batches()
        finally:
            store.close()
        body = "<div class='step'><span>1 Add material</span><span>2 Find a view that clicks</span><span>3 Explain it back</span></div>"
        body += "<h2>Continue understanding</h2>" + "".join(f"<article><a href='/batches/{escape(row['id'])}'><h2>{escape(row['source_id'])}</h2><small>{row['pending_count'] or 0} ideas waiting for review · last updated {escape(row['created_at'][:10])}</small></a></article>" for row in rows) or "<article class='primary'><h2>Start with material that feels confusing</h2><p class='muted'>Ask your agent to import an email thread, notes, document, or roadmap. This workspace will help you see it in a way that clicks.</p></article>"
        self.respond(page("Make the subject easier to understand", body, "Bring the messy material. We will find a representation that helps you reason about it."))

    def batch(self, batch_id: str, query: dict):
        store = SQLiteStore(self.database_path)
        try:
            history = store.batch_history(batch_id)
        except KeyError:
            store.close(); return self.send_error(404)
        finally:
            store.close()
        question = query.get("question", ["Where do teams disagree?"])[0]
        selected = next((p for p in history["proposals"] if p["status"] == "pending"), None)
        source = f"<details><summary>See original material</summary><pre>{escape(history['source']['content'])}</pre></details>"
        review_html = self.proposal_form(batch_id, selected) if selected else "<article><h2>Review</h2><p>No pending proposals. Approved and rejected decisions remain in the audit history.</p></article>"
        store = SQLiteStore(self.database_path)
        try:
            comparison_model = store.hydrate_committed_claims(batch_id, empty_reality())
        finally:
            store.close()
        views = search(comparison_model, question, top_k=7)
        cards = "".join(f"<article><span class='score'>{item.score}</span> — <a href='/batches/{escape(batch_id)}/diagrams/{escape(item.spec.id)}?question={escape(question, quote=True)}'>{escape(item.spec.name)}</a><br><small>{escape('; '.join(item.rationale))}</small></article>" for item in views)
        compare = f"<article><h2>Choose a way to see this</h2><p class='muted'>Start with the view that best matches your question. You can switch later.</p><form method='get'><label>What are you trying to understand?<input name='question' value='{escape(question, quote=True)}'></label><button>Find views</button></form><div class='grid'>{cards}</div></article>"
        commit = "<form method='post' action='/batches/%s/commit'><button>Use reviewed ideas</button></form>" % escape(batch_id)
        learn = f"<article class='primary'><h2>Ready to check your understanding?</h2><form method='post' action='/batches/{escape(batch_id)}/learn'><label>I want to understand…<input required name='goal' value='{escape(question, quote=True)}'></label><label>I am<select name='familiarity'><option value='new'>New to this</option><option value='partial'>Somewhat familiar</option><option value='confident'>Already confident</option></select></label><button>Start guided understanding</button></form></article>"
        self.respond(page("Understand this material", "<div class='step'><span>Review evidence</span><span>Choose a view</span><span>Check understanding</span></div>" + learn + compare + review_html + commit + source, "Move from noisy source material to a representation you can explain in your own words."))

    def start_learning(self, batch_id: str, form: dict):
        goal, familiarity = form.get("goal", [""])[0].strip(), form.get("familiarity", ["new"])[0]
        if not goal: return self.respond(page("Learning error", "<p>A learning goal is required.</p>"), 400)
        store = SQLiteStore(self.database_path)
        try:
            model = store.hydrate_committed_claims(batch_id, empty_reality())
            if not model.assertions: raise ValueError("Approve and commit at least one claim before starting a learning session")
            session_id = store.create_learning_session(batch_id, goal, familiarity, goal)
        except (KeyError, ValueError) as error:
            store.close(); return self.respond(page("Learning error", f"<p>{escape(str(error))}</p>"), 400)
        store.close(); self.redirect(f"/learning/{session_id}")

    def learning_session(self, session_id: str):
        store = SQLiteStore(self.database_path)
        try:
            session = store.learning_session(session_id)
            model = store.hydrate_committed_claims(session["batch_id"], empty_reality())
            candidates, challenge, assessment = start_candidates(model, session["goal"]), make_challenge(model), store.latest_explanation(session_id)
        except KeyError:
            store.close(); return self.send_error(404)
        finally:
            store.close()
        cards = "".join(f"<article><b>{escape(item.family)}</b><br><small>{escape(item.definition)}</small><form method='post' action='/learning/{escape(session_id)}/feedback'><input type='hidden' name='candidate_id' value='{escape(item.id)}'><button name='reaction' value='clicked'>This clicked</button><button name='reaction' value='too_abstract'>Too abstract</button><button name='reaction' value='another_way'>Another way</button><button name='reaction' value='go_deeper'>Go deeper</button></form></article>" for item in candidates[:3])
        result = "" if not assessment else f"<article><h2>Your next representation</h2><p>Explanation score: {assessment['score']}. Missing: {escape(', '.join(__import__('json').loads(assessment['missing_terms'])) or 'none detected')}.</p><p><b>Try: {escape(assessment['next_candidate_id'])}</b></p></article>"
        explain = f"<article><h2>Explain it back</h2><p>{escape(challenge.prompt)}</p><form method='post' action='/learning/{escape(session_id)}/explain'><label>Your explanation<textarea required name='answer'></textarea></label><label>Confidence (0 to 1)<input name='confidence' value='0.5'></label><button>Check my understanding</button></form></article>"
        self.respond(page("Learning session", f"<p>{escape(session['goal'])} · familiarity: {escape(session['familiarity'])}</p><h2>Which representation helps?</h2>{cards}{explain}{result}"))

    def learning_feedback(self, session_id: str, form: dict):
        store = SQLiteStore(self.database_path)
        try: store.record_learning_feedback(session_id, form["candidate_id"][0], form["reaction"][0])
        except (KeyError, ValueError) as error:
            store.close(); return self.respond(page("Feedback error", f"<p>{escape(str(error))}</p>"), 400)
        store.close(); self.redirect(f"/learning/{session_id}")

    def learning_explain(self, session_id: str, form: dict):
        store = SQLiteStore(self.database_path)
        try:
            session = store.learning_session(session_id)
            model = store.hydrate_committed_claims(session["batch_id"], empty_reality())
            assessment = assess_explanation(form["answer"][0], make_challenge(model), start_candidates(model, session["goal"]))
            store.record_explanation(session_id, form["answer"][0], float(form.get("confidence", [".5"])[0]), assessment)
        except (KeyError, ValueError) as error:
            store.close(); return self.respond(page("Explanation error", f"<p>{escape(str(error))}</p>"), 400)
        store.close(); self.redirect(f"/learning/{session_id}")

    def diagram(self, batch_id: str, view_id: str, query: dict):
        store = SQLiteStore(self.database_path)
        try:
            model = store.hydrate_committed_claims(batch_id, empty_reality())
        except KeyError:
            store.close(); return self.send_error(404)
        finally:
            store.close()
        question = query.get("question", [""])[0]
        candidate = next((item for item in search(model, question, top_k=7) if item.spec.id == view_id), None)
        if candidate is None:
            return self.send_error(404)
        self.respond(render_diagram(candidate, model).encode())

    def proposal_form(self, batch_id: str, proposal: dict) -> str:
        status = escape(proposal["status"])
        fields = "".join(f"<label>{name}<input name='{name}' value='{escape(str(proposal[name]), quote=True)}'></label>" for name in ("subject", "predicate", "object", "confidence"))
        fields += f"<label>Evidence excerpt<textarea name='evidence_excerpt'>{escape(proposal['evidence_excerpt'])}</textarea></label><label>Rationale<textarea name='rationale'>{escape(proposal['rationale'])}</textarea></label>"
        return f"<article><h2>Review one proposal <small class='{status}'>{status}</small></h2><p><b>{escape(proposal['id'])}</b></p><form method='post' action='/batches/{escape(batch_id)}/proposals/{escape(proposal['id'])}'>{fields}<label>Your name<input required name='reviewer'></label><button name='decision' value='approved'>Approve</button><button name='decision' value='rejected'>Reject</button></form></article>"

    def decide(self, batch_id: str, proposal_id: str, form: dict):
        store = SQLiteStore(self.database_path)
        try:
            batch = store.load_batch(batch_id)
            proposal = next(item for item in batch.proposals if item.id == proposal_id)
            if proposal.status is not ProposalStatus.PENDING:
                raise ValueError("Only pending proposals can be reviewed")
            for field in ("subject", "predicate", "object", "evidence_excerpt", "rationale"):
                if field in form: setattr(proposal, field, form[field][0])
            if "confidence" in form: proposal.confidence = float(form["confidence"][0])
            reviewer = form.get("reviewer", [""])[0].strip()
            if not reviewer: raise ValueError("Reviewer name is required")
            decision = ProposalStatus(form.get("decision", [""])[0])
            review(batch, proposal_id, decision, reviewer)
            store.record_review(batch_id, proposal)
        except (KeyError, ValueError) as error:
            store.close(); return self.respond(page("Review error", f"<p>{escape(str(error))}</p>"), 400)
        store.close()
        self.redirect(f"/batches/{batch_id}")

    def commit(self, batch_id: str):
        store = SQLiteStore(self.database_path)
        try:
            batch, model = store.load_batch(batch_id), store.hydrate_committed_claims(batch_id, empty_reality())
            if store.batch_history(batch_id)["approved_claims"]:
                raise ValueError("This batch has already been committed")
            committed = apply_approved(model, batch)
            store.record_commits(batch_id, model, committed)
        except (KeyError, ValueError) as error:
            store.close(); return self.respond(page("Commit error", f"<p>{escape(str(error))}</p>"), 400)
        store.close()
        self.redirect(f"/batches/{batch_id}")

    def respond(self, content: bytes, status: int = 200):
        self.send_response(status); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(content))); self.end_headers(); self.wfile.write(content)

    def redirect(self, location: str):
        self.send_response(303); self.send_header("Location", location); self.end_headers()

    def log_message(self, *_):
        pass


def serve(database: str = "representation_compiler.db", port: int = 8000) -> None:
    App.database_path = database
    server = ThreadingHTTPServer(("127.0.0.1", port), App)
    print(f"Open http://127.0.0.1:{port}")
    server.serve_forever()
