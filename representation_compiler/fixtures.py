from .model import Assertion, AssertionStatus, CanonicalModel, Entity, Evidence, Origin, Perspective


def empty_reality() -> CanonicalModel:
    return CanonicalModel(perspectives={"shared": Perspective("shared", "Shared record")})


def project_alpha() -> CanonicalModel:
    """Small, deliberately messy corpus used by tests and the CLI demo."""
    model = CanonicalModel()
    model.entities = {
        "project-alpha": Entity("project-alpha", "Project Alpha", "project"),
        "api-team": Entity("api-team", "API Team", "team"),
        "sales": Entity("sales", "Sales", "team"),
    }
    model.perspectives = {
        "shared": Perspective("shared", "Shared record"),
        "engineering": Perspective("engineering", "Engineering", "API Team"),
        "commercial": Perspective("commercial", "Commercial", "Sales"),
    }
    model.evidence = {
        "ev-1": Evidence("ev-1", "roadmap", "API dependency moved to 15 September.", "roadmap:12"),
        "ev-2": Evidence("ev-2", "eng-update", "Alpha cannot ship without API v2.", "email:2026-08-20"),
        "ev-3": Evidence("ev-3", "sales-note", "Customer was promised an August launch.", "meeting:2026-08-21"),
        "ev-4": Evidence("ev-4", "status", "Project Alpha is on track.", "status:4"),
    }
    model.assertions = {
        "as-1": Assertion("as-1", "project-alpha", "depends_on", "API v2", "2026-08-20T09:00:00Z", "Maya", .95, "engineering", Origin.OBSERVED, ("ev-2",), valid_from="2026-08-20"),
        "as-2": Assertion("as-2", "project-alpha", "launch_date", "2026-09-15", "2026-08-20T09:00:00Z", "Maya", .9, "engineering", Origin.OBSERVED, ("ev-1",), valid_from="2026-08-20", relations={"supersedes": ("as-6",)}),
        "as-3": Assertion("as-3", "project-alpha", "launch_date", "2026-08-31", "2026-08-21T09:00:00Z", "Rui", .8, "commercial", Origin.OBSERVED, ("ev-3",), valid_from="2026-08-21", relations={"contradicts": ("as-2",)}),
        "as-4": Assertion("as-4", "project-alpha", "health", "on track", "2026-08-22T09:00:00Z", "status bot", .6, "shared", Origin.OBSERVED, ("ev-4",), valid_from="2026-08-22"),
        "as-5": Assertion("as-5", "project-alpha", "health", "at risk", "2026-08-23T09:00:00Z", "compiler", .85, "engineering", Origin.INFERRED, ("ev-1", "ev-2"), valid_from="2026-08-23", relations={"contradicts": ("as-4",), "derived_from": ("as-1", "as-2")}),
        "as-6": Assertion("as-6", "project-alpha", "launch_date", "2026-08-31", "2026-08-01T09:00:00Z", "Maya", .7, "shared", Origin.OBSERVED, ("ev-3",), valid_from="2026-08-01", valid_to="2026-08-20", status=AssertionStatus.SUPERSEDED),
    }
    model.validate()
    return model
