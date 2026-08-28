"""Standalone interactive sky explorer for notebook-derived Cartesian vectors."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_sky_explorer(notebook: dict[str, Any], output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_sky_explorer(notebook), encoding="utf-8")
    return target


def render_sky_explorer(notebook: dict[str, Any]) -> str:
    representations = notebook.get("representations", {})
    candidate = next((item for item in representations.values() if item.get("derived_data_id")), None)
    if not candidate:
        raise ValueError("notebook has no representation with derived data")
    data = notebook.get("derived_data", {}).get(candidate["derived_data_id"])
    if not data or not data.get("rows"):
        raise ValueError("notebook has no explorable derived vector rows")
    rows = json.dumps(data["rows"]).replace("</", "<\\/")
    title = _escape(str(notebook.get("title", "Sky explorer")))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
:root{{--paper:#f5f5f5;--ink:#2d3142;--muted:#4f5d75;--soft:#7a8399;--accent:#eb6c36;--rule:rgba(45,49,66,.16)}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px system-ui,sans-serif}}
main{{max-width:1100px;margin:32px auto;padding:0 24px}} h1{{font:400 40px Georgia,serif;margin:0 0 8px}} p{{color:var(--muted);max-width:760px}}
.layout{{display:grid;grid-template-columns:1fr 260px;gap:32px;align-items:start;margin-top:28px}} .plot{{background:#fff;border:1px solid var(--rule);padding:16px}}
svg{{display:block;width:100%;aspect-ratio:1;background:var(--paper)}} .eyebrow,.meta{{font:11px ui-monospace,monospace;letter-spacing:.08em;color:var(--soft)}}
.controls{{border-top:1px solid var(--rule);padding-top:16px}} label{{display:block;font-size:13px;font-weight:600;margin:0 0 20px}} input{{width:100%;accent-color:var(--accent)}}
.readout{{border:1px solid var(--rule);padding:16px;background:#fff;min-height:120px;font-size:14px}} .readout strong{{display:block;margin-bottom:8px}} .readout code{{color:var(--muted);font-size:12px}}
button{{background:transparent;border:1px solid var(--ink);padding:8px 12px;font:inherit;cursor:pointer}} button:hover{{background:var(--accent);border-color:var(--accent);color:#fff}}
@media(max-width:720px){{.layout{{grid-template-columns:1fr}}h1{{font-size:32px}}}}
</style></head><body><main><div class="eyebrow">ICRS UNIT-SPHERE EXPLORER · DERIVED DATA</div><h1>{title}</h1>
<p>Rotate the Cartesian representation of the catalog. Point position preserves angular direction; the front hemisphere is solid and the rear hemisphere is faint. Select a point to inspect its original coordinates and derived vector.</p>
<div class="layout"><section class="plot"><svg id="sky" viewBox="0 0 720 720" role="img" aria-label="Interactive rotated ICRS unit sphere"></svg></section>
<aside><div class="controls"><label>Longitude rotation <output id="lonOut">0°</output><input id="lon" type="range" min="0" max="360" value="0"></label><label>Latitude rotation <output id="latOut">0°</output><input id="lat" type="range" min="-90" max="90" value="0"></label><button id="reset">Reset view</button></div><div class="readout" id="readout"><strong>Select an object</strong><span>Click a point to inspect the mapping.</span></div></aside></div>
<p class="meta">Representation: { _escape(candidate.get('title', 'Unit sphere')) } · {len(data['rows'])} derived vectors · x/y plot is an orthographic projection.</p>
</main><script>const rows={rows};const svg=document.querySelector('#sky'),lon=document.querySelector('#lon'),lat=document.querySelector('#lat'),readout=document.querySelector('#readout');
const ns='http://www.w3.org/2000/svg'; function el(tag,attrs={{}}){{const node=document.createElementNS(ns,tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);return node}}
function project(p){{const a=Number(lon.value)*Math.PI/180,b=Number(lat.value)*Math.PI/180;const x1=Math.cos(a)*p.x-Math.sin(a)*p.y,y1=Math.sin(a)*p.x+Math.cos(a)*p.y;return {{x:x1,y:Math.cos(b)*y1-Math.sin(b)*p.z,z:Math.sin(b)*y1+Math.cos(b)*p.z}}}}
function render(){{svg.replaceChildren();svg.append(el('circle',{{cx:360,cy:360,r:300,fill:'#fff',stroke:'#2d3142','stroke-width':1}}));svg.append(el('line',{{x1:60,y1:360,x2:660,y2:360,stroke:'rgba(45,49,66,.14)'}}));svg.append(el('line',{{x1:360,y1:60,x2:360,y2:660,stroke:'rgba(45,49,66,.14)'}}));for(const item of rows){{const p=project(item),front=p.z>=0,circle=el('circle',{{cx:360+p.x*300,cy:360-p.y*300,r:front?6:4,fill:front?'rgba(79,93,117,.35)':'rgba(79,93,117,.10)',stroke:front?'#4f5d75':'rgba(79,93,117,.35)','stroke-width':1,tabindex:0}});circle.addEventListener('click',()=>select(item,p));circle.addEventListener('keydown',event=>{{if(event.key==='Enter')select(item,p)}});svg.append(circle)}}}}
function select(item,p){{readout.innerHTML=`<strong>${{escapeHtml(String(item.id))}}</strong><code>RA ${{item.ra_deg}}° · Dec ${{item.dec_deg}}°</code><br><code>x=${{item.x.toFixed(4)}} · y=${{item.y.toFixed(4)}} · z=${{item.z.toFixed(4)}}</code><br><span>${{p.z>=0?'front':'rear'}} hemisphere in this view</span>`}}
function escapeHtml(value){{const div=document.createElement('div');div.textContent=value;return div.innerHTML}} function update(){{document.querySelector('#lonOut').value=lon.value+'°';document.querySelector('#latOut').value=lat.value+'°';render()}} lon.oninput=update;lat.oninput=update;document.querySelector('#reset').onclick=()=>{{lon.value=0;lat.value=0;update()}};update();</script></body></html>"""


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
