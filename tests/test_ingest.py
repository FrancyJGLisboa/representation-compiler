from representation_compiler.fixtures import project_alpha
from representation_compiler.ingest import compile_notes


def test_compiler_creates_resolvable_evidence_backed_assertion():
    model = project_alpha()
    ids = compile_notes(model, "note", "Project Alpha | owner | Maya")
    created = model.assertions[ids[0]]
    assert created.evidence_ids[0] in model.evidence
    assert created.subject == "project-alpha"
