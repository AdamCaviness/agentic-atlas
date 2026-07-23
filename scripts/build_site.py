#!/usr/bin/env python3
"""Build the local multi-profile discovery site from emitted profile JSON.

Reads profiles/*.json, embeds them into a single self-contained index.html
(the map + preference sliders + cards + compare), and copies each engine-rendered
profiles/<slug>.html in as the per-profile detail page. Deterministic, no network,
opens from file:// and serves statically. Visual language is inherited from the
report's tokens; all user-facing copy uses plain words (see the plain-language rule).
"""
from __future__ import annotations
import json, glob, os, shutil, html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(REPO, "profiles")
OUT = os.path.join(REPO, "_bmad-output", "site")

# Report design tokens (kept in sync with agentic_atlas/report.py _HTML_CSS).
CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#6b7280;--faint:#9ca3af;--card:#f7f7f8;--line:#e5e7eb;--track:#e9eaed;
--neg:#0891b2;--pos:#9333ea;--cov-good:#16a34a;--cov-mid:#d97706;--cov-low:#dc2626;--accent:#4f46e5;--pill-fg:#fff;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;--card:#161b22;
--line:#30363d;--track:#21262d;--neg:#22d3ee;--pos:#c084fc;--cov-good:#3fb950;--cov-mid:#d29922;--cov-low:#f85149;
--accent:#818cf8;--pill-fg:#0d1117}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.5}
a{color:var(--accent)}
.wrap{max-width:1200px;margin:0 auto;padding:20px 22px 60px}
header.top{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:18px}
header.top h1{font-size:1.15rem;margin:0}
header.top .tag{color:var(--muted);font-size:.85rem}
header.top .spacer{flex:1}
header.top a.repo{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;color:var(--muted);border:1px solid var(--line);border-radius:50%}
header.top a.repo:hover{border-color:var(--accent);color:var(--accent)}
.hero{margin:0 0 22px}
.hero .lead{font-size:1.08rem;margin:0 0 8px}
.hero .sub2{color:var(--muted);font-size:.9rem;margin:0 0 8px}
.hero .principle{font-size:.82rem;color:var(--faint);margin:0;font-style:italic}
.brand{display:flex;align-items:center;gap:11px}
.brand .mark{width:30px;height:31px;flex:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.14))}
.brand .word{font-size:1.4rem;font-weight:750;letter-spacing:-.01em;line-height:1;
  background:linear-gradient(100deg,var(--neg),var(--accent) 52%,var(--pos));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.layout{display:grid;grid-template-columns:280px 1fr;gap:22px}
@media (max-width:860px){.layout{grid-template-columns:1fr}}
.panel{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:14px 16px}
.panel h2{font-size:.9rem;margin:0 0 4px}
.panel .sub{color:var(--muted);font-size:.8rem;margin:0 0 12px}
.group{margin:0 0 6px;border-top:1px solid var(--line);padding-top:8px}
.group>summary{cursor:pointer;font-size:.8rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.slider{margin:12px 0}
.prow{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:.82rem;color:var(--fg);margin-bottom:3px}
.prow .hl{font-weight:600}
.prow .hr{font-weight:600;text-align:right}
.prow em{font-style:italic;font-weight:400;color:var(--muted)}
.state{position:relative;display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:.72rem;margin-top:3px;min-height:1.1em}
.state .np{font-style:italic;color:var(--faint)}
.slider:not(.off) .state .np{color:var(--accent);font-style:normal}
.info{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;padding:0;border:1px solid var(--faint);color:var(--muted);background:none;border-radius:50%;font:600 .62rem/1 var(--sans);cursor:help}
.info:hover,.info:focus{border-color:var(--accent);color:var(--accent);outline:none}
.tip{display:none;position:absolute;left:0;bottom:calc(100% + 7px);z-index:30;width:230px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:9px 11px;box-shadow:0 8px 28px rgba(0,0,0,.2);font:400 .76rem/1.45 var(--sans);font-style:normal;text-transform:none;letter-spacing:normal}
.tip .th{display:block;font-weight:650;color:var(--muted);margin-bottom:5px}
.tip .pn{color:var(--neg);font-weight:600}.tip .pp{color:var(--pos);font-weight:600}
.info:hover ~ .tip,.info:focus ~ .tip,.tip.show{display:block}
.srange{position:relative}
.srange input[type=range]{width:100%;display:block;accent-color:var(--accent);position:relative;z-index:1;background:transparent}
.srange::before{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:2px;height:16px;background:var(--faint);pointer-events:none;z-index:0}
.slider.off .srange input[type=range]{filter:grayscale(1);opacity:.5}
.btnrow{display:flex;gap:8px;margin-top:10px}
button.act{font:inherit;font-size:.8rem;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:5px 10px;cursor:pointer}
button.act:hover{border-color:var(--accent);color:var(--accent)}
#plot{width:100%;height:380px;border:1px solid var(--line);border-radius:12px;background:var(--card);display:block}
.tline{cursor:pointer}
.tline:hover{opacity:1 !important;stroke-width:2.5}
.hint{color:var(--muted);font-size:.8rem;margin:8px 0 0}
.dot{cursor:pointer}
.matches{margin:14px 0 0}
.matches h3{font-size:.85rem;margin:0 0 6px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:22px}
.pcard{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:14px 16px}
.pcard .nm{font-weight:650;font-size:.98rem;line-height:1.2}
.pcard .cov2{font-size:.68rem;color:var(--muted);font-family:var(--mono);margin-top:1px}
.sig{margin:10px 0 0}
.sig .row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;margin:5px 0;font-size:.8rem}
.sig .row .word{color:var(--muted)}
.sig .row .sc{font-family:var(--mono);font-weight:700}
.sc.neg{color:var(--neg)}.sc.pos{color:var(--pos)}
.tk{position:relative;height:16px;background:var(--track);border-radius:5px;grid-column:1 / -1}
.tk .c{position:absolute;left:50%;top:-2px;bottom:-2px;width:2px;background:var(--faint)}
.tk .f{position:absolute;top:0;bottom:0}
.tk .f.neg{right:50%;background:var(--neg);border-radius:5px 0 0 5px}
.tk .f.pos{left:50%;background:var(--pos);border-radius:0 5px 5px 0}
.tk .f.prov{opacity:.45;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px)}
.pcard .acts{display:flex;gap:8px;margin-top:12px}
.pcard .fitline{font-size:.78rem;color:var(--muted);margin-top:8px;min-height:1em}
.verdict{font-family:var(--mono);font-size:.74rem;margin:2px 0}
.v-match::before{content:"[match] "}.v-close::before{content:"[close] "}.v-counter::before{content:"[opposite] "}
.tray{position:sticky;bottom:0;margin-top:22px;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:10px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.tray .chip{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:.8rem;display:inline-flex;gap:6px;align-items:center}
.tray .chip b{font-weight:600}
.note{font-size:.78rem;color:var(--muted)}
"""

JS = r"""
const $ = (s,r=document)=>r.querySelector(s);
const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
const AXES = DATA[0] ? DATA[0].axes.map(a=>({id:a.axis_id,title:a.title,neg:a.poles.negative,pos:a.poles.positive,eneg:(a.explain||{}).negative||"",epos:(a.explain||{}).positive||""})) : [];
// Flat, ordered by user-centricity: axes you can answer about YOURSELF first
// (your context, then how you want to work), then task-dependent, then tool build/cost.
const ORDER = [
  "greenfield-vs-brownfield","solo-vs-team","autonomous-vs-human-in-loop",
  "spec-light-vs-spec-driven","prescriptive-vs-composable","generalist-vs-specialist",
  "test-optional-vs-test-first","prototype-vs-production","small-scope-vs-large-scope",
  "fresh-vs-mature","interrogative-vs-opinionated","single-agent-vs-multi-agent",
  "lightweight-vs-heavyweight",
];
const prefs = {}; // axisId -> {value:-10..10, active:bool}
AXES.forEach(a=>prefs[a.id]={value:0,active:false});
const compare = [];

function axScore(p,id){const a=p.axes.find(x=>x.axis_id===id);return a?{score:a.score,cov:a.coverage,poles:a.poles}:null;}
function sigAxes(p){return p.axes.filter(a=>a.score!==null&&a.coverage>=0.5).map(a=>({...a,mag:Math.abs(a.score)})).sort((x,y)=>y.mag-x.mag).slice(0,4);}
function poleWord(a){return a.score<0?a.poles.negative:a.poles.positive;}
function esc(s){return (s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// ---- cards ----
function bar(score,scale){
  const cls = score<0?"neg":"pos"; const pct = Math.min(100,Math.abs(score)/scale*50);
  return `<div class="tk"><div class="c"></div><div class="f ${cls}" style="${score<0?'right:50%;width':'left:50%;width'}:${pct}%"></div></div>`;
}
function covPct(p){return Math.round(p.axes.reduce((s,a)=>s+a.coverage,0)/p.axes.length*100);}
function renderCards(){
  const g = $("#gallery"); g.innerHTML="";
  DATA.forEach(p=>{
    const sig = sigAxes(p);
    const rows = sig.map(a=>`<div class="row"><span class="word">${esc(poleWord(a))}</span><span class="sc ${a.score<0?'neg':'pos'}">${a.score>0?'+':''}${a.score.toFixed(1)}</span>${bar(a.score,a.scale)}</div>`).join("");
    const el = document.createElement("div"); el.className="pcard";
    el.innerHTML = `<div class="nm">${esc(p.name)}</div>
      <div class="cov2">${covPct(p)}% evidence</div>
      <div class="sig">${rows||'<div class="note">partial profile</div>'}</div>
      <div class="fitline" data-fit="${p.slug}"></div>
      <div class="acts"><a class="act" href="profiles/${p.slug}.html">open profile</a>
      <button class="act" onclick="toggleCompare('${p.slug}')">+ compare</button></div>`;
    g.appendChild(el);
  });
  renderFitLines();
}

// ---- fit ----
function activePrefs(){return AXES.filter(a=>prefs[a.id].active).map(a=>({id:a.id,v:prefs[a.id].value}));}
// Direction is what matters: same side = aligned. Magnitude only refines the label.
function verdict(userV, toolScore){
  if(toolScore===null) return null;
  const sameSide=(userV<0&&toolScore<0)||(userV>0&&toolScore>0);
  if(sameSide) return Math.abs(toolScore)>=1?"match":"close"; // strong vs mild, both aligned
  if(Math.abs(toolScore)<0.5) return "close";                 // near-neutral: not opposing
  return "counter";                                            // clearly the other way
}
function fitFor(p){
  const ap=activePrefs(); if(!ap.length) return null;
  const rows=ap.map(x=>{const a=axScore(p,x.id);const tv=a?a.score:null;return {id:x.id,v:x.v,tool:tv,verdict:tv!==null?verdict(x.v,tv):null};});
  const aligned=rows.filter(r=>r.verdict==="match"||r.verdict==="close").length; // leans your way (primary)
  const strong=rows.filter(r=>r.verdict==="match").length;                        // and strongly so (tiebreak)
  const dist=rows.reduce((s,r)=>s+(r.tool!==null?Math.abs(r.v-r.tool):20),0);      // numeric closeness (last)
  return {rows,aligned,strong,total:ap.length,dist};
}
function renderFitLines(){
  const ap=activePrefs();
  $$(".fitline").forEach(el=>{
    const p=DATA.find(d=>d.slug===el.dataset.fit); const f=fitFor(p);
    el.textContent = f? `leans your way on ${f.aligned} of the ${f.total} you set` : "";
  });
  renderMatches();
}
function renderMatches(){
  const box=$("#matches"); const ap=activePrefs();
  if(!ap.length){box.innerHTML="";return;}
  const scored=DATA.map(p=>({p,f:fitFor(p)})).filter(x=>x.f).sort((a,b)=>b.f.aligned-a.f.aligned||b.f.strong-a.f.strong||a.f.dist-b.f.dist);
  const axName=id=>AXES.find(a=>a.id===id);
  box.innerHTML = `<h3>Best matches for your preferences</h3>` + scored.slice(0,6).map(({p,f})=>{
    const ord={match:0,close:1,counter:2};
    const vs=[...f.rows].sort((x,y)=>(ord[x.verdict]??9)-(ord[y.verdict]??9)).map(r=>{const ax=axName(r.id);const cls=r.verdict==="match"?"v-match":r.verdict==="close"?"v-close":"v-counter";
      const word = r.v<0?ax.neg:ax.pos;
      return `<div class="verdict ${cls}">${esc(ax.title)} — you want ${esc(word)}${r.tool!==null?`, this is ${r.tool>0?'+':''}${r.tool.toFixed(1)}`:', no reading'}</div>`;}).join("");
    return `<div class="pcard"><div class="nm"><a href="profiles/${p.slug}.html">${esc(p.name)}</a><span class="cov">leans your way on ${f.aligned} of ${f.total}</span></div>${vs}</div>`;
  }).join("");
}

// ---- parallel-coordinates plot: one vertical axis per preference you set ----
function renderPlot(){
  const svg=$("#plot"), hint=$("#plothint");
  const axs=ORDER.filter(id=>prefs[id]&&prefs[id].active).map(id=>AXES.find(a=>a.id===id));
  if(!axs.length){svg.style.display="none";if(hint)hint.style.display="block";svg.innerHTML="";return;}
  svg.style.display="block";if(hint)hint.style.display="none";
  const W=svg.clientWidth||760,H=380,padX=64,padT=30,padB=30,scale=10;
  const xF=i=>axs.length===1?W/2:padX+i*(W-2*padX)/(axs.length-1);
  const yF=v=>padT+(scale-v)/(2*scale)*(H-padT-padB);
  let s="";
  axs.forEach((a,i)=>{const x=xF(i);
    s+=`<line x1='${x}' y1='${padT}' x2='${x}' y2='${H-padB}' stroke='var(--line)' stroke-width='1'/>`;
    s+=`<line x1='${x-5}' y1='${yF(0)}' x2='${x+5}' y2='${yF(0)}' stroke='var(--faint)'/>`;
    s+=`<text x='${x}' y='${padT-8}' text-anchor='middle' font-size='10' fill='var(--pos)' font-family='var(--sans)'>${esc(a.pos)}</text>`;
    s+=`<text x='${x}' y='${H-padB+15}' text-anchor='middle' font-size='10' fill='var(--neg)' font-family='var(--sans)'>${esc(a.neg)}</text>`;});
  DATA.map(p=>({p,f:fitFor(p)})).filter(o=>o.f).forEach(({p,f})=>{
    const pts=axs.map((a,i)=>{const v=axScore(p,a.id);return (v&&v.score!==null)?`${xF(i)},${yF(v.score).toFixed(1)}`:null;}).filter(Boolean);
    if(!pts.length)return;
    const r=f.aligned/f.total,op=(0.1+0.55*r).toFixed(2),col=r>=1?"var(--accent)":"var(--muted)";
    s+=`<polyline class="tline" data-slug='${p.slug}' points='${pts.join(' ')}' fill='none' stroke='${col}' stroke-width='1.5' opacity='${op}'><title>${esc(p.name)} — leans your way on ${f.aligned}/${f.total}</title></polyline>`;});
  const ypts=axs.map((a,i)=>`${xF(i)},${yF(prefs[a.id].value).toFixed(1)}`).join(' ');
  s+=`<polyline points='${ypts}' fill='none' stroke='var(--accent)' stroke-width='3'/>`;
  axs.forEach((a,i)=>{s+=`<circle cx='${xF(i)}' cy='${yF(prefs[a.id].value).toFixed(1)}' r='4' fill='var(--accent)'/>`;});
  s+=`<text x='${xF(0)+7}' y='${(yF(prefs[axs[0].id].value)-8).toFixed(1)}' font-size='11' font-weight='700' fill='var(--accent)' font-family='var(--sans)'>You</text>`;
  svg.innerHTML=s;
}

// ---- preference panel ----
function buildPanel(){
  const box=$("#prefs");
  ORDER.forEach(id=>{const a=AXES.find(x=>x.id===id); if(!a)return;
    const w=document.createElement("div"); w.className="slider off"; w.dataset.axis=id;
    const tp=esc(a.title).split(' vs ');
    w.innerHTML=`<div class="prow"><span class="hl">${tp[0]||esc(a.title)}${tp[1]?' <em>vs</em>':''}</span>${tp[1]?`<span class="hr">${tp[1]}</span>`:''}</div>
      <div class="srange"><input type="range" min="-10" max="10" value="0" step="1"></div>
      <div class="state"><button class="info" type="button" aria-label="What ${esc(a.title)} means">i</button><span class="tip" role="tooltip"><span class="th">${esc(a.title)}</span><span class="pn">${esc(a.neg)}</span> — ${esc(a.eneg)}<br><span class="pp">${esc(a.pos)}</span> — ${esc(a.epos)}</span><span class="np">no preference</span></div>`;
    const inp=$("input",w), st=$(".np",w);
    inp.addEventListener("input",()=>{const v=+inp.value;
      if(v===0){prefs[id]={value:0,active:false};w.classList.add("off");st.textContent="no preference";inp.style.accentColor="";}
      else{prefs[id]={value:v,active:true};w.classList.remove("off");st.textContent=`${v<0?a.neg:a.pos} ${v>0?'+':''}${v}`;inp.style.accentColor=v<0?"var(--neg)":"var(--pos)";}
      update();});
    inp.addEventListener("dblclick",()=>{prefs[id]={value:0,active:false};inp.value=0;w.classList.add("off");st.textContent="no preference";inp.style.accentColor="";update();});
    const info=$(".info",w), tip=$(".tip",w);
    info.addEventListener("click",e=>{e.stopPropagation();tip.classList.toggle("show");});
    box.appendChild(w);
  });
}
function clearAll(){AXES.forEach(a=>prefs[a.id]={value:0,active:false});$$("#prefs .slider").forEach(w=>{w.classList.add("off");const i=$("input",w);i.value=0;i.style.accentColor="";$(".np",w).textContent="no preference";});update();}

// ---- compare ----
function toggleCompare(slug){const i=compare.indexOf(slug);if(i>=0)compare.splice(i,1);else if(compare.length<3)compare.push(slug);renderTray();}
function renderTray(){const t=$("#tray");if(!compare.length){t.innerHTML='<span class="note">Pick up to 3 tools to compare them side by side.</span>';return;}
  t.innerHTML=compare.map(s=>`<span class="chip"><b>${esc(DATA.find(d=>d.slug===s).name)}</b> <a href="#" onclick="toggleCompare('${s}');return false">×</a></span>`).join("")+
    (compare.length>=2?` <a class="act" href="#" onclick="showCompare();return false">Compare →</a>`:"");}
function showCompare(){
  const rows=AXES.map(a=>{const cells=compare.map(s=>{const v=axScore(DATA.find(d=>d.slug===s),a.id);return v&&v.score!==null?`${DATA.find(d=>d.slug===s).name}: ${v.score>0?'+':''}${v.score.toFixed(1)}`:`${DATA.find(d=>d.slug===s).name}: —`;}).join(" | ");
    return `${a.title} — ${cells}`;}).join("\n");
  alert("Side-by-side (rubric order, no total by design):\n\n"+rows);
}

function update(){renderPlot();renderFitLines();}
document.addEventListener("DOMContentLoaded",()=>{
  buildPanel();renderCards();renderPlot();renderTray();
  $("#plot").addEventListener("click",e=>{const t=e.target.closest("[data-slug]");if(t)location.href="profiles/"+t.dataset.slug+".html";});
  document.addEventListener("click",()=>$$(".tip.show").forEach(t=>t.classList.remove("show")));
  window.addEventListener("resize",renderPlot);
});
"""

GH_MARK = (
    "<svg viewBox='0 0 16 16' width='17' height='17' fill='currentColor' aria-hidden='true'>"
    "<path d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82"
    "-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01"
    " 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0"
    "-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0"
    " 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07"
    "-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013"
    " 8.013 0 0016 8c0-4.42-3.58-8-8-8z'></path></svg>"
)


def _display_name(target: str) -> str:
    """Last path segment, matching report.py's pill (full target stays in the JSON)."""
    name = target.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name or target


def build():
    files = sorted(glob.glob(os.path.join(PROFILES, "*.json")))
    data = []
    for f in files:
        slug = os.path.splitext(os.path.basename(f))[0]
        try:
            p = json.load(open(f))
        except Exception as e:
            print(f"skip {slug}: {e}"); continue
        p["slug"] = slug
        p["name"] = _display_name(p.get("target", ""))
        data.append(p)
    if not data:
        print("no profiles found in", PROFILES); return 1
    os.makedirs(os.path.join(OUT, "profiles"), exist_ok=True)
    for p in data:
        src = os.path.join(PROFILES, p["slug"] + ".html")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, "profiles", p["slug"] + ".html"))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Atlas — find your fit</title><style>{CSS}</style></head><body><div class="wrap">
<header class="top"><div class="brand"><svg class="mark" viewBox="0 0 30 31" aria-hidden="true"><polygon points="15,1 4,11 15,11" fill="var(--neg)"/><polygon points="15,1 26,11 15,11" fill="var(--pos)"/><polygon points="4,11 15,11 15,30" fill="var(--neg)" opacity=".8"/><polygon points="26,11 15,11 15,30" fill="var(--pos)" opacity=".8"/><polygon points="15,1 4,11 15,30 26,11" fill="none" stroke="var(--accent)" stroke-width="1" opacity=".55"/></svg><span class="word">Agentic Atlas</span></div><span class="spacer"></span><a class="repo" href="https://github.com/AdamCaviness/agentic-atlas" target="_blank" rel="noopener" aria-label="Open agentic-atlas on GitHub (opens in a new tab)" title="Open agentic-atlas on GitHub (new tab)">{GH_MARK}</a></header>
<section class="hero">
<p class="lead">Profile agentic development approaches, frameworks, and skill collections on shared axes, and see if one fits you and your projects.</p>
<p class="sub2">A deterministic engine over an open, versioned, community-driven rubric. Hosted profiles of popular tools, run it yourself and help improve it.</p>
<p class="principle">Positions, not rankings. Both ends of every axis are legitimate, and there's no overall score.</p>
</section>
<div class="layout">
  <aside class="panel"><h2>Your preferences</h2><p class="sub">Set only what matters. Untouched sliders mean no preference. The map updates as you go.</p><div id="prefs"></div><div class="btnrow"><button class="act" onclick="clearAll()">Clear all</button></div><div id="matches" class="matches"></div></aside>
  <main>
  <svg id="plot" style="display:none"></svg><p id="plothint" class="hint">Set a preference on the left and the tools line up against it, one vertical axis per preference you set, with your line running through them. Or just scan the cards below.</p>
  <div id="gallery" class="gallery"></div>
  <div id="tray" class="tray"></div></main>
</div>
<p class="note" style="margin-top:26px">Draft profiles for local design review — evidence is engine-validated but not yet human-vouched. No aggregate score anywhere: fit is per-axis only.</p>
</div>
<script>const DATA={json.dumps(data)};</script><script>{JS}</script></body></html>"""
    out_index = os.path.join(OUT, "index.html")
    open(out_index, "w").write(page)
    print(f"built {out_index} with {len(data)} profiles")
    print("profiles:", ", ".join(p["slug"] for p in data))
    return 0

if __name__ == "__main__":
    raise SystemExit(build())
