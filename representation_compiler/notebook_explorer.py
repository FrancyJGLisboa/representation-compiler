"""Dependency-free browser explorer for any portable understanding notebook."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_notebook_explorer(notebook: dict[str, Any], output: str | Path) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_notebook_explorer(notebook), encoding="utf-8")
    return target


def render_notebook_explorer(notebook: dict[str, Any]) -> str:
    title = _escape(str(notebook.get("title", "Understanding notebook")))
    payload = json.dumps(notebook).replace("</", "<\\/")
    return f"""<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title>
<style>:root{{--paper:#f6f5f2;--ink:#20252d;--muted:#52606d;--accent:#eb6c36;--rule:#d9e0e8}}*{{box-sizing:border-box}}body{{max-width:1080px;margin:auto;padding:32px 20px 64px;background:var(--paper);color:var(--ink);font:16px system-ui,sans-serif}}h1{{font:400 42px Georgia,serif;margin:6px 0}}h2{{font-size:18px}}p{{color:var(--muted);line-height:1.5}}.meta{{font:11px ui-monospace,monospace;letter-spacing:.1em;color:#687386;text-transform:uppercase}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}article{{background:#fff;border:1px solid var(--rule);border-radius:12px;padding:18px}}article.selected{{border:2px solid var(--accent)}}button,textarea,input{{font:inherit;border-radius:7px;padding:10px;border:1px solid #c9d1db}}button{{background:var(--ink);color:#fff;cursor:pointer;margin:8px 6px 0 0}}button.primary{{background:var(--accent);border-color:var(--accent)}}textarea,input{{width:100%;background:#fff}}textarea{{min-height:100px}}pre{{white-space:pre-wrap;max-height:280px;overflow:auto;font-size:13px}}.hidden{{display:none}}</style>
<main><div class='meta'>Portable understanding notebook</div><h1>{title}</h1><p id='question'></p><h2>Choose the representation that helps</h2><div id='candidates' class='grid'></div><section id='learn' class='hidden'><h2>Check your understanding</h2><p id='challenge'></p><label>Explain it in your own words<textarea id='explanation'></textarea></label><label>Confidence (0–1)<input id='confidence' type='number' min='0' max='1' step='.1' value='.5'></label><button class='primary' id='save'>Add to learning ledger and download notebook</button><p id='result'></p></section><details><summary>Inspect indexed source material</summary><pre id='source'></pre></details></main>
<script>
const notebook={payload};
const reps=Object.values(notebook.representations).filter(r=>r.family!=='source index');
let selected=null,reaction='clicked';
const cards=document.querySelector('#candidates'),learn=document.querySelector('#learn');
document.querySelector('#question').textContent=notebook.question;
document.querySelector('#source').textContent=JSON.stringify(notebook.derived_data,null,2);
function esc(value){{const node=document.createElement('span');node.textContent=value;return node.innerHTML}}
function candidateCard(r){{return `<article class="${{selected===r.id?'selected':''}}"><div class="meta">${{esc(r.family)}}</div><h2>${{esc(r.title)}}</h2><p>${{esc(r.encode)}}</p><p><b>Preserves:</b> ${{esc(r.preserves.join(', '))}}<br><b>Hides:</b> ${{esc(r.discards.join(', '))}}<br><b>Easier:</b> ${{esc(r.makes_easier.join(', '))}}</p><details><summary>How this could fail</summary><p>${{esc(r.falsification_test||'Compare against source material.')}}</p></details><button class="primary" onclick="choose('${{r.id}}','clicked')">This clicked</button><button onclick="choose('${{r.id}}','too_abstract')">Too abstract</button><button onclick="choose('${{r.id}}','another way')">Another way</button><button onclick="choose('${{r.id}}','go_deeper')">Go deeper</button></article>`}}
function render(){{cards.innerHTML=reps.map(candidateCard).join('')}}
function choose(id,kind){{selected=id;reaction=kind;learn.classList.remove('hidden');document.querySelector('#challenge').textContent='Explain the central relationship in your own words. What changes if an important relationship disappears?';render();learn.scrollIntoView({{behavior:'smooth'}})}}
window.choose=choose;
document.querySelector('#save').onclick=()=>{{if(!selected)return;const answer=document.querySelector('#explanation').value.trim(),terms=(JSON.stringify(notebook.derived_data).match(/[A-Za-z]{{5,}}/g)||[]).map(x=>x.toLowerCase()),gaps=[...new Set(terms)].filter(x=>!answer.toLowerCase().includes(x)).slice(0,5),next=reaction==='too_abstract'||reaction==='another way'?'concept-matrix':selected==='mechanism-map'?'state-machine':'mechanism-map';notebook.learning_ledger=notebook.learning_ledger||[];notebook.learning_ledger.push({{goal:notebook.question,representation_id:selected,reaction,explain_back:answer,confidence:Number(document.querySelector('#confidence').value),challenge:document.querySelector('#challenge').textContent,gaps,recommended_representation_id:next}});const blob=new Blob([JSON.stringify(notebook,null,2)],{{type:'application/json'}}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=(notebook.id||'understanding-notebook')+'.json';link.click();URL.revokeObjectURL(url);document.querySelector('#result').textContent=`Saved learning record. Next recommended view: ${{next}}.`}};
render();
</script>"""


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
