"""Editorial, evidence-linked SVG renderers for representation candidates."""
from __future__ import annotations

from html import escape

from .model import CanonicalModel
from .views import Candidate

PAPER, INK, MUTED, SOFT, ACCENT, ACCENT_TINT, RULE = "#f5f5f5", "#2d3142", "#4f5d75", "#7a8399", "#eb6c36", "rgba(235,108,54,.08)", "rgba(45,49,66,.12)"


def render(candidate: Candidate, model: CanonicalModel) -> str:
    if candidate.spec.id == "timeline":
        return timeline(model)
    if candidate.spec.id == "contradiction-matrix":
        return contradiction_swimlanes(model)
    return dependency_graph(model)


def shell(title: str, description: str, svg: str, caption: str) -> str:
    return f"""<!doctype html><title>{escape(title)}</title><style>body{{margin:0;background:{PAPER};color:{INK};font:16px system-ui,sans-serif}}main{{max-width:1120px;margin:36px auto;padding:0 24px}}h1{{font:400 40px Georgia,serif;margin:0 0 6px}}p{{color:{MUTED};max-width:720px}}svg{{width:100%;height:auto;display:block;margin-top:28px}}.caption{{font:13px ui-monospace,monospace;border-top:1px solid {RULE};padding-top:12px}}</style><main><a href='javascript:history.back()'>← Back to candidates</a><h1>{escape(title)}</h1><p>{escape(description)}</p>{svg}<p class='caption'>{escape(caption)}</p></main>"""


def dependency_graph(model: CanonicalModel) -> str:
    project = next((item for item in model.entities.values() if item.type == "project"), next(iter(model.entities.values())))
    dependencies = [item for item in model.assertions.values() if item.subject == project.id and item.predicate in {"depends_on", "blocked_by", "at_risk_due_to"}]
    labels = [item.object for item in dependencies] or ["No explicit dependency claim"]
    nodes = "".join(_box(80 + index * 240, 250, label, "DEPENDENCY", focal=False) for index, label in enumerate(labels[:3]))
    connectors = "".join(f"<path d='M {160 + index * 240} 250 V {204 + index * 16} H {440 + index * 40} V 176' fill='none' stroke='{MUTED}' stroke-width='1.2' marker-end='url(#arrow)'/>" for index in range(min(3, len(labels))))
    svg = f"""<svg viewBox='0 0 960 400' role='img' aria-labelledby='dep-title dep-desc'><title id='dep-title'>Dependency graph for {escape(project.name)}</title><desc id='dep-desc'>Dependencies converge on the project launch.</desc><defs><marker id='arrow' markerWidth='8' markerHeight='6' refX='7' refY='3' orient='auto'><polygon points='0 0,8 3,0 6' fill='{MUTED}'/></marker></defs><rect width='960' height='400' fill='{PAPER}'/><text x='48' y='48' fill='{SOFT}' font-size='10' font-family='ui-monospace,monospace' letter-spacing='1.4'>DEPENDENCY GRAPH · EVIDENCE-BACKED</text>{connectors}{nodes}{_box(400, 120, project.name, 'PROJECT', focal=True)}<text x='480' y='356' text-anchor='middle' fill='{SOFT}' font-size='11' font-family='ui-monospace,monospace'>Each edge is derived from a source-backed assertion.</text></svg>"""
    return shell("Why this is blocked", "A dependency view makes the bottleneck visible before the detailed evidence.", svg, "Focus: upstream dependencies converge on the project. Open the source batch to inspect evidence.")


def timeline(model: CanonicalModel) -> str:
    events = sorted(model.assertions.values(), key=lambda item: item.valid_from or item.asserted_at)[:6]
    positions = [100 + index * (760 / max(1, len(events) - 1)) for index in range(len(events))]
    marks = []
    for index, (claim, x) in enumerate(zip(events, positions)):
        up = index % 2 == 0
        y, text_y = (170, 112) if up else (230, 304)
        color = ACCENT if claim.origin == "inferred" else INK
        marks.append(f"<line x1='{x:.0f}' y1='200' x2='{x:.0f}' y2='{y}' stroke='{MUTED}'/><circle cx='{x:.0f}' cy='200' r='{6 if claim.origin == 'inferred' else 4}' fill='{color}'/><text x='{x:.0f}' y='{text_y}' text-anchor='middle' fill='{INK}' font-size='12' font-weight='600'>{escape(claim.predicate)}</text><text x='{x:.0f}' y='{text_y + 18}' text-anchor='middle' fill='{SOFT}' font-size='10' font-family='ui-monospace,monospace'>{escape((claim.valid_from or claim.asserted_at)[:10])}</text>")
    svg = f"""<svg viewBox='0 0 960 380' role='img' aria-labelledby='time-title time-desc'><title id='time-title'>Timeline of claims</title><desc id='time-desc'>Claims positioned by their observed or valid date.</desc><rect width='960' height='380' fill='{PAPER}'/><text x='48' y='48' fill='{SOFT}' font-size='10' font-family='ui-monospace,monospace' letter-spacing='1.4'>TIMELINE · CLAIMS OVER TIME</text><line x1='100' y1='200' x2='860' y2='200' stroke='{INK}' stroke-width='1.2'/>{''.join(marks)}<text x='480' y='352' text-anchor='middle' fill='{SOFT}' font-size='11' font-family='ui-monospace,monospace'>Orange = inferred claim · Black = observed claim</text></svg>"""
    return shell("What changed over time", "A chronological projection exposes changed dates, state shifts, and inferred risk.", svg, "Time is taken from valid-from where present, otherwise assertion time.")


def contradiction_swimlanes(model: CanonicalModel) -> str:
    perspectives = list(model.perspectives.values())[:3]
    lanes, cards = [], []
    for index, perspective in enumerate(perspectives):
        y = 108 + index * 116
        lanes.append(f"<rect x='40' y='{y}' width='880' height='92' fill='none' stroke='{RULE}'/><text x='56' y='{y+28}' fill='{SOFT}' font-size='10' font-family='ui-monospace,monospace'>{escape(perspective.name.upper())}</text>")
        relevant = [claim for claim in model.assertions.values() if claim.perspective_id == perspective.id][:2]
        for card_index, claim in enumerate(relevant):
            x = 248 + card_index * 300
            accent = bool(claim.relations.get("contradicts"))
            cards.append(f"<rect x='{x}' y='{y+18}' width='244' height='58' rx='6' fill='{ACCENT_TINT if accent else '#fff'}' stroke='{ACCENT if accent else MUTED}'/><text x='{x+12}' y='{y+42}' fill='{INK}' font-size='12' font-weight='600'>{escape(claim.predicate)}: {escape(claim.object)[:22]}</text><text x='{x+12}' y='{y+62}' fill='{SOFT}' font-size='9' font-family='ui-monospace,monospace'>{'CONTRADICTS' if accent else claim.origin.upper()}</text>")
    svg = f"""<svg viewBox='0 0 960 480' role='img' aria-labelledby='conflict-title conflict-desc'><title id='conflict-title'>Perspective contradiction view</title><desc id='conflict-desc'>Claims grouped by perspective, with orange cards marking explicit contradictions.</desc><rect width='960' height='480' fill='{PAPER}'/><text x='40' y='48' fill='{SOFT}' font-size='10' font-family='ui-monospace,monospace' letter-spacing='1.4'>PERSPECTIVE SWIMLANES · DISAGREEMENT VISIBLE</text>{''.join(lanes)}{''.join(cards)}<text x='40' y='442' fill='{SOFT}' font-size='11' font-family='ui-monospace,monospace'>Orange cards carry an explicit contradiction relation; disagreement is preserved, not merged away.</text></svg>"""
    return shell("Where teams disagree", "Separate perspectives make competing claims legible without forcing false consensus.", svg, "Orange marks source-backed claims explicitly linked as contradictions.")


def _box(x: int, y: int, label: str, tag: str, focal: bool) -> str:
    stroke, fill = (ACCENT, ACCENT_TINT) if focal else (INK, "#fff")
    return f"<rect x='{x}' y='{y}' width='160' height='56' rx='6' fill='{fill}' stroke='{stroke}'/><rect x='{x+8}' y='{y+7}' width='56' height='12' rx='2' fill='none' stroke='{stroke}' opacity='.5'/><text x='{x+36}' y='{y+16}' text-anchor='middle' fill='{stroke}' font-size='7' font-family='ui-monospace,monospace'>{escape(tag)}</text><text x='{x+80}' y='{y+38}' text-anchor='middle' fill='{INK}' font-size='12' font-weight='600'>{escape(label[:24])}</text>"
