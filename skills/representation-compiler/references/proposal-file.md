# Proposal JSON file

Write a JSON object in this shape before importing it into the local engine.

```json
{
  "source_id": "alpha-email-thread",
  "source_text": "The exact full text supplied by the user.",
  "entities": [
    {"id": "project-alpha", "name": "Project Alpha", "type": "project"}
  ],
  "claims": [
    {
      "subject": "project-alpha",
      "predicate": "depends_on",
      "object": "API v2",
      "evidence_excerpt": "Project Alpha cannot ship without API v2.",
      "confidence": 0.9,
      "rationale": "The dependency is stated explicitly."
    }
  ]
}
```

Rules:

- `subject` must match an ID in `entities` or an entity already known to the system.
- `evidence_excerpt` must be a contiguous exact quote from `source_text`.
- `confidence` is from `0` through `1`.
- Treat all imported claims as proposals. The browser review step controls approval.
