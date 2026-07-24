#!/usr/bin/env python3
"""Build the local multi-profile discovery site from emitted profile JSON.

Reads profiles/*.json, embeds them into a single self-contained index.html
(the map + preference sliders + cards + compare), and copies each engine-rendered
profiles/<slug>.html in as the per-profile detail page. Deterministic, no network,
opens from file:// and serves statically. Visual language is inherited from the
report's tokens; all user-facing copy uses plain words (see the plain-language rule).
"""

from __future__ import annotations

import glob
import json
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES = os.path.join(REPO, "profiles")
# Tool-neutral build output (gitignored). The deploy uploads this directory to Pages.
OUT = os.path.join(REPO, "dist")

# Report design tokens (kept in sync with agentic_atlas/report.py _HTML_CSS).
CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#6b7280;--faint:#9ca3af;--card:#f7f7f8;--line:#e5e7eb;--track:#e9eaed;
--neg:#0891b2;--pos:#9333ea;--cov-good:#16a34a;--cov-mid:#d97706;--cov-low:#dc2626;--accent:#4f46e5;--pill-fg:#fff;
--t1:#4f46e5;--t2:#b45309;--t3:#be123c;--scrim:rgba(17,20,28,.46);
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--faint:#6e7681;--card:#161b22;
--line:#30363d;--track:#21262d;--neg:#22d3ee;--pos:#c084fc;--cov-good:#3fb950;--cov-mid:#d29922;--cov-low:#f85149;
--accent:#818cf8;--pill-fg:#0d1117;--t1:#818cf8;--t2:#f59e0b;--t3:#fb7185;--scrim:rgba(1,4,9,.62)}}
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
.panel h2{font-size:.9rem;margin:0}
.phead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 6px}
.clr{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;padding:0;border:1px solid var(--line);border-radius:8px;background:none;color:var(--muted);cursor:pointer;flex:none}
.clr:hover{border-color:var(--accent);color:var(--accent)}
.panel .sub{color:var(--muted);font-size:.8rem;margin:0 0 12px}
.group{margin:0 0 6px;border-top:1px solid var(--line);padding-top:8px}
.group>summary{cursor:pointer;font-size:.8rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.slider{margin:12px 0}
.prow{display:grid;grid-template-columns:1fr auto 1fr;align-items:baseline;gap:8px;font-size:.82rem;color:var(--fg);margin-bottom:3px}
.prow .hl{font-weight:600;text-align:left}
.prow .hr{font-weight:600;text-align:right}
.prow .hvs{font-style:italic;font-weight:400;color:var(--muted);text-align:center}
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
.srange input[type=range]{width:100%;display:block;accent-color:var(--accent)}
/* center tick shows only while the slider is active (thumb is off-center); at rest the thumb marks center */
.srange::before{content:"";position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:2px;height:12px;background:var(--faint);pointer-events:none;display:none}
.slider:not(.off) .srange::before{display:block}
.slider.off .srange input[type=range]{filter:grayscale(1);opacity:.5}
.btnrow{display:flex;gap:8px;margin-top:10px}
button.act{font:inherit;font-size:.8rem;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:5px 10px;cursor:pointer}
button.act:hover{border-color:var(--accent);color:var(--accent)}
#plot{width:100%;height:380px;border:1px solid var(--line);border-radius:12px;background:var(--card);display:block;margin:0 0 22px}
.tline{cursor:pointer}
.tline:hover{opacity:1 !important;stroke-width:2.5}
.hint{color:var(--muted);font-size:.8rem;margin:8px 0 0}
.dot{cursor:pointer}
.matches{margin:14px 0 0}
.matches h3{font-size:.85rem;margin:0 0 6px}
.matches .mcard{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:12px 14px;margin:0 0 10px}
.matches .mname{display:block;font-weight:650;font-size:.95rem}
.matches .msum{font-size:.72rem;color:var(--muted);margin:1px 0 8px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.pcard{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:14px 16px}
/* The card title IS the link to the profile (no separate "open profile" control). Same
   button feel as the profile page's home mark: no underline, a subtle lift on hover. On the
   card's own --card surface the hover tint steps to --track so it stays visible. */
.pcard .nm{display:inline-flex;align-items:center;max-width:100%;font-weight:650;font-size:.98rem;line-height:1.2;color:inherit;text-decoration:none;cursor:pointer;margin:-5px -8px 1px;padding:5px 8px;border-radius:9px;transition:background .12s ease,box-shadow .12s ease,color .12s ease}
.pcard .nm:hover{background:var(--track);box-shadow:0 1px 4px rgba(0,0,0,.10);color:var(--accent)}
.pcard .nm:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.pcard .cov2{font-size:.68rem;color:var(--muted);font-family:var(--mono);margin-top:1px}
.sig{margin:10px 0 0}
.sig .row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;margin:5px 0;font-size:.8rem}
.sig .row .word{color:var(--muted)}
.sig .row .sc{font-family:var(--mono);font-weight:700}
.sc.neg{color:var(--neg)}.sc.pos{color:var(--pos)}.sc.none{color:var(--faint);font-weight:500;font-size:.72rem}
.tk{position:relative;height:16px;background:var(--track);border-radius:5px;grid-column:1 / -1}
.tk .c{position:absolute;left:50%;top:-2px;bottom:-2px;width:2px;background:var(--faint)}
.tk .f{position:absolute;top:0;bottom:0}
.tk .f.neg{right:50%;background:var(--neg);border-radius:5px 0 0 5px}
.tk .f.pos{left:50%;background:var(--pos);border-radius:0 5px 5px 0}
.tk .f.prov{opacity:.45;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px)}
.pcard .acts{display:flex;gap:8px;margin-top:12px}
.pcard .fitline{font-size:.78rem;color:var(--muted);margin-top:8px;min-height:1em}
.verdict{font-family:var(--mono);font-size:.74rem;margin:2px 0}
.v-match::before{content:"✓ ";color:var(--accent);font-weight:700}
.v-close::before{content:"~ ";color:var(--faint)}
.v-counter::before{content:"✗ ";color:var(--cov-mid)}
.tray{display:none;position:sticky;bottom:12px;margin-top:22px;border:1.5px solid var(--accent);border-radius:12px;background:var(--card);padding:12px 16px;gap:10px;align-items:center;flex-wrap:wrap;box-shadow:0 10px 34px rgba(0,0,0,.24)}
.tray.active{display:flex}
.tray .traylbl{font-weight:650;font-size:.82rem;margin-right:2px}
.tray .chip{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:.8rem;display:inline-flex;gap:6px;align-items:center}
.tray .chip b{font-weight:600}
.tray .cbtn{background:var(--accent);color:var(--pill-fg);border:1px solid var(--accent);border-radius:8px;padding:6px 14px;font-size:.82rem;font-weight:600;text-decoration:none}
.tray .cbtn:hover{filter:brightness(1.08)}
.act.added{border-color:var(--accent);color:var(--accent);font-weight:600}
.note{font-size:.78rem;color:var(--muted)}

/* ---- compare modal ---- */
.scrim{position:fixed;inset:0;background:var(--scrim);backdrop-filter:blur(3px);display:none;align-items:center;justify-content:center;padding:18px;z-index:60}
.scrim.on{display:flex}
.cmp{background:var(--bg);border:1px solid var(--line);border-radius:16px;width:min(1200px,93vw);max-height:90vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 24px 70px rgba(0,0,0,.4)}
.cmp-hd{display:flex;align-items:center;gap:12px 14px;flex-wrap:wrap;padding:15px 18px;border-bottom:1px solid var(--line)}
.cmp-hd h2{font-size:1.02rem;margin:0;font-weight:700}
.cmp-tools{display:flex;gap:7px;flex-wrap:wrap;flex:1;min-width:160px}
.tchip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:999px;padding:3px 5px 3px 10px;font-size:.8rem}
.tchip .tdot{width:9px;height:9px;border-radius:50%;flex:none}
.tchip .rm{border:none;background:none;color:var(--faint);cursor:pointer;font-size:1rem;line-height:1;padding:0 4px;border-radius:6px}
.tchip .rm:hover{color:var(--cov-low)}
.cmp-x{flex:none;width:32px;height:32px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--muted);cursor:pointer;font-size:1.1rem;line-height:1}
.cmp-x:hover{border-color:var(--cov-low);color:var(--cov-low)}
.cmp-sum{padding:11px 18px;font-size:.86rem;color:var(--fg);border-bottom:1px solid var(--line);background:var(--card)}
.cmp-sum .k{font-weight:650}
.cmp-sum .pn{color:var(--neg);font-weight:600}.cmp-sum .pp{color:var(--pos);font-weight:600}
.cmp-body{flex:1;overflow-y:auto;overflow-x:hidden;padding:16px 18px 20px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.seg button{font:inherit;font-size:.78rem;font-weight:600;color:var(--muted);background:var(--bg);border:none;padding:6px 13px;cursor:pointer}
.seg button+button{border-left:1px solid var(--line)}
.seg button[aria-pressed="true"]{background:var(--accent);color:var(--pill-fg)}
.bctl{display:flex;align-items:center;gap:10px;margin:0 0 14px;flex-wrap:wrap}
.bctl .lbl{font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:650}
.shape-sec{margin:0 0 18px}
.shape-hd{display:flex;align-items:center;gap:12px;margin:2px 0 10px}
.shape-tog{flex:none;display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;padding:0;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--muted);cursor:pointer}
.shape-tog:hover{border-color:var(--accent);color:var(--accent)}
.shape-tog svg{width:13px;height:13px;transition:transform .15s ease}
.shape-tog[aria-expanded="true"] svg{transform:rotate(90deg)}
.plegend{display:flex;gap:16px;flex-wrap:wrap;font-size:.82rem;margin:0}
.plegend .li{display:inline-flex;align-items:center;gap:8px}
.plegend svg{overflow:visible}
.plotscroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:10px}
#cmpplot{height:210px;background:var(--bg);border:1px solid var(--line);border-radius:10px;display:block;width:100%}
.plottip{font-size:.74rem;color:var(--faint);margin:8px 0 0}
.mxscroll{overflow-x:auto}
.mx{display:grid;gap:0;min-width:520px}
.mx>div{padding:9px 12px;border-bottom:1px solid var(--line)}
.mx .h{position:sticky;top:0;background:var(--bg);z-index:2;border-bottom:1px solid var(--line)}
.mx .gut{position:sticky;left:0;background:var(--bg);z-index:1}
.mx .h.gut{z-index:3}
.mx .thead{display:flex;flex-direction:column;gap:2px}
.mx .tname{font-weight:650;font-size:.92rem;display:inline-flex;align-items:center;gap:7px}
.mx .tdot{width:10px;height:10px;border-radius:50%;flex:none}
.mx .tcov{font-size:.68rem;color:var(--muted);font-family:var(--mono)}
.ax-t{font-weight:600;font-size:.86rem;display:flex;align-items:center;gap:6px}
.ax-p{font-size:.72rem;color:var(--muted);margin-top:2px}
.ax-p .pn{color:var(--neg)}.ax-p .pp{color:var(--pos)}
.ax-spread{margin-top:6px;font-size:.66rem;font-family:var(--mono);display:inline-flex;align-items:center;gap:6px;color:var(--muted)}
.spread-pip{height:4px;border-radius:2px;background:var(--accent);display:inline-block;min-width:6px;opacity:.8}
.sig-link{margin-top:7px;display:block;font:inherit;font-size:.7rem;color:var(--muted);background:none;border:none;padding:0;cursor:pointer}
.sig-link:hover{color:var(--accent)}
.cell{display:flex;flex-direction:column;gap:6px;justify-content:center}
.cell .num{font-family:var(--mono);font-weight:700;font-size:.82rem;font-variant-numeric:tabular-nums}
.num.neg{color:var(--neg)}.num.pos{color:var(--pos)}.num.na{color:var(--faint);font-weight:500}
.axtip-btn{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;padding:0;border:1px solid var(--faint);color:var(--muted);background:none;border-radius:50%;font:600 .62rem/1 var(--sans);cursor:help;position:relative;flex:none}
.axtip-btn:hover,.axtip-btn:focus{border-color:var(--accent);color:var(--accent);outline:none}
.axtip{display:none;position:absolute;left:0;top:calc(100% + 7px);z-index:40;width:238px;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:9px 11px;box-shadow:0 8px 28px rgba(0,0,0,.2);font:400 .76rem/1.45 var(--sans);text-align:left;font-weight:400;white-space:normal;text-transform:none;letter-spacing:normal}
.axtip-btn:hover .axtip,.axtip-btn:focus .axtip{display:block}
.axtip .pn{color:var(--neg);font-weight:600}.axtip .pp{color:var(--pos);font-weight:600}
.drill-back{font:inherit;font-size:.8rem;font-weight:600;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:9px;cursor:pointer;padding:7px 13px 7px 11px;margin:0 0 14px;display:inline-flex;gap:6px;align-items:center;transition:border-color .12s ease,color .12s ease,background .12s ease}
.drill-back:hover{border-color:var(--accent);color:var(--accent);background:var(--bg)}
.drill-back:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.drill-back .chev{font-size:1.1em;line-height:1;margin-top:-1px}
.cmp-body.din{animation:drillIn .19s ease both}
.cmp-body.dback{animation:drillBack .19s ease both}
@keyframes drillIn{from{opacity:0;transform:translateX(16px)}to{opacity:1;transform:none}}
@keyframes drillBack{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.cmp-body.din,.cmp-body.dback{animation:none}}
.drill-h{margin:0 0 4px;font-size:1.05rem;font-weight:700}
.drill-sub{margin:0 0 16px;font-size:.82rem;color:var(--muted);max-width:70ch}
.drill-sub .pn{color:var(--neg);font-weight:600}.drill-sub .pp{color:var(--pos);font-weight:600}
.drill-sub b{color:var(--fg);font-weight:650}
.sig-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.sig-tool{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:13px 14px}
.sig-tool .sh{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
.sig-tool .stname{font-weight:650;font-size:.9rem;display:inline-flex;align-items:center;gap:7px}
.sig-tool .stname .tdot{width:10px;height:10px;border-radius:50%}
.sig-tool .stsc{font-family:var(--mono);font-weight:700;font-size:.82rem}
.stsc.neg{color:var(--neg)}.stsc.pos{color:var(--pos)}.stsc.na{color:var(--faint);font-weight:500}
.sig-item{border-top:1px solid var(--line);padding:8px 0}
.sig-item:first-of-type{border-top:none}
.sig-top{display:flex;align-items:center;gap:8px;margin-bottom:3px}
.kind{font-size:.6rem;text-transform:uppercase;letter-spacing:.05em;font-weight:650;border:1px solid var(--line);border-radius:999px;padding:1px 7px;color:var(--muted);flex:none}
.kind.judged{border-color:var(--accent);color:var(--accent)}
.sig-id{font-size:.66rem;color:var(--faint);font-family:var(--mono)}
.sig-v{font-family:var(--mono);font-weight:700;font-size:.72rem;margin-left:auto;font-variant-numeric:tabular-nums}
.sig-v.neg{color:var(--neg)}.sig-v.pos{color:var(--pos)}.sig-v.zero{color:var(--faint)}
.sig-ev{font-size:.76rem;color:var(--fg);opacity:.88;line-height:1.42}
.sig-ev.empty{color:var(--faint);font-style:italic;opacity:1}
.sig-src{font-size:.64rem;color:var(--faint);margin-top:3px;font-family:var(--mono)}
.cmp-ft{padding:12px 18px;border-top:1px solid var(--line);background:var(--card);display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.cmp-ft .principle{font-size:.78rem;color:var(--faint);font-style:italic;margin:0}
.cmp-ft .evi{font-size:.74rem;color:var(--muted);margin:0;display:inline-flex;align-items:center;gap:7px}
.cmp-ft .swatch{width:22px;height:12px;border-radius:3px;background:var(--track);position:relative;overflow:hidden}
.cmp-ft .swatch::after{content:"";position:absolute;inset:0;left:40%;background:var(--pos);opacity:.45;background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.55) 0 3px,transparent 3px 7px)}
.empty{color:var(--muted);font-size:.9rem;padding:30px 6px;text-align:center}
.cmp :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:640px){
  .cmp{max-height:94vh;width:100%}
  .cmp-hd{gap:10px}
  .cmp-tools{order:3;flex-basis:100%}
  .cmp-body{padding:14px 12px 18px}
  #cmpplot{height:180px}
}
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
const TCOL=["--t1","--t2","--t3"];
let cmpSort="diff",cmpShapeOpen=true,cmpDrillAxis=null,cmpLastFocus=null;
const prof=s=>DATA.find(d=>d.slug===s);
const cmpMeta=id=>AXES.find(a=>a.id===id);

function axScore(p,id){const a=p.axes.find(x=>x.axis_id===id);return a?{score:a.score,cov:a.coverage,poles:a.poles}:null;}
// The four axes shown on every card. When the reader sets preferences, show the ones they
// weight most (by absolute value) so every card lines up on what the reader cares about;
// otherwise fall back to the first four in the canonical order. Same four on all cards.
function sharedAxes(){
  const active=AXES.filter(a=>prefs[a.id].active).map(a=>({id:a.id,mag:Math.abs(prefs[a.id].value)})).sort((x,y)=>y.mag-x.mag||ORDER.indexOf(x.id)-ORDER.indexOf(y.id));
  const ids=active.map(o=>o.id);
  for(const id of ORDER){if(ids.length>=4)break;if(!ids.includes(id))ids.push(id);}
  return ids.slice(0,4);
}
function poleWord(a){return a.score<0?a.poles.negative:a.poles.positive;}
function esc(s){return (s||"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

// ---- cards ----
function bar(score,scale,prov){
  const cls = score<0?"neg":"pos"; const pct = Math.min(100,Math.abs(score)/scale*50);
  return `<div class="tk"><div class="c"></div><div class="f ${cls}${prov?' prov':''}" style="${score<0?'right:50%;width':'left:50%;width'}:${pct}%"></div></div>`;
}
function covPct(p){return Math.round(p.axes.reduce((s,a)=>s+a.coverage,0)/p.axes.length*100);}
function renderCards(){
  const g = $("#gallery"); g.innerHTML="";
  DATA.forEach(p=>{
    const el = document.createElement("div"); el.className="pcard";
    el.innerHTML = `<a class="nm" href="profiles/${p.slug}.html" title="Open the ${esc(p.name)} profile">${esc(p.name)}</a>
      <div class="cov2">${covPct(p)}% evidence</div>
      <div class="sig" data-sig="${p.slug}"></div>
      <div class="fitline" data-fit="${p.slug}"></div>
      <div class="acts"><button class="act cmpbtn" data-slug="${p.slug}" onclick="toggleCompare('${p.slug}')">+ compare</button></div>`;
    g.appendChild(el);
  });
  renderSignatures();
  renderFitLines();
}
// Fill every card's signature block with the shared four axes, each showing where that tool
// sits. Re-run on preference change so the cards track what the reader cares about.
function renderSignatures(){
  const ids=sharedAxes();
  $$('.sig[data-sig]').forEach(box=>{
    const p=DATA.find(d=>d.slug===box.dataset.sig);
    const rows=ids.map(id=>{
      const a=p.axes.find(x=>x.axis_id===id);
      if(!a||a.score===null) return `<div class="row"><span class="word">${esc((AXES.find(x=>x.id===id)||{}).title||id)}</span><span class="sc none">no reading</span></div>`;
      return `<div class="row"><span class="word">${esc(poleWord(a))}</span><span class="sc ${a.score<0?'neg':'pos'}">${a.score>0?'+':''}${a.score.toFixed(1)}</span>${bar(a.score,a.scale,a.coverage<0.5)}</div>`;
    }).join("");
    box.innerHTML=rows||'<div class="note">partial profile</div>';
  });
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
      return `<div class="verdict ${cls}">${esc(ax.title)}: you want ${esc(word)}${r.tool!==null?`, this is ${r.tool>0?'+':''}${r.tool.toFixed(1)}`:', no reading'}</div>`;}).join("");
    return `<div class="mcard"><a class="mname" href="profiles/${p.slug}.html">${esc(p.name)}</a><div class="msum">leans your way on ${f.aligned} of ${f.total}</div>${vs}</div>`;
  }).join("");
}

// ---- parallel-coordinates plot: one vertical axis per preference you set ----
function renderPlot(){
  const svg=$("#plot");
  const axs=ORDER.filter(id=>prefs[id]&&prefs[id].active).map(id=>AXES.find(a=>a.id===id));
  if(!axs.length){svg.style.display="none";svg.innerHTML="";return;}
  svg.style.display="block";
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
    s+=`<polyline class="tline" data-slug='${p.slug}' points='${pts.join(' ')}' fill='none' stroke='${col}' stroke-width='1.5' opacity='${op}'><title>${esc(p.name)}, leans your way on ${f.aligned}/${f.total}</title></polyline>`;});
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
    w.innerHTML=`<div class="prow"><span class="hl">${tp[0]||esc(a.title)}</span>${tp[1]?`<em class="hvs">vs</em><span class="hr">${tp[1]}</span>`:''}</div>
      <div class="srange"><input type="range" min="-10" max="10" value="0" step="1"></div>
      <div class="state"><button class="info" type="button" aria-label="What ${esc(a.title)} means">i</button><span class="tip" role="tooltip"><span class="th">${esc(a.title)}</span><span class="pn">${esc(a.neg)}</span>: ${esc(a.eneg)}<br><span class="pp">${esc(a.pos)}</span>: ${esc(a.epos)}</span><span class="np">no preference</span></div>`;
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
function syncCompareButtons(){$$(".cmpbtn").forEach(b=>{const on=compare.includes(b.dataset.slug);b.classList.toggle("added",on);b.textContent=on?"✓ added":"+ compare";});}
function toggleCompare(slug){const i=compare.indexOf(slug);if(i>=0)compare.splice(i,1);else if(compare.length<3)compare.push(slug);renderTray();syncCompareButtons();if($("#cmpscrim")&&$("#cmpscrim").classList.contains("on"))cmpRender();}
function renderTray(){const t=$("#tray");
  if(!compare.length){t.className="tray";t.innerHTML="";return;}
  t.className="tray active";
  t.innerHTML=`<span class="traylbl">Compare (${compare.length})</span>`+
    compare.map(s=>`<span class="chip"><b>${esc(DATA.find(d=>d.slug===s).name)}</b> <a href="#" aria-label="remove from compare" onclick="toggleCompare('${s}');return false">×</a></span>`).join("")+
    (compare.length>=2?`<a class="cbtn" href="#" onclick="showCompare();return false">Compare →</a>`:`<span class="note">add one more</span>`);}
function showCompare(){if(compare.length<2)return;openCmp();}

// ---- compare modal ----
function openCmp(){
  cmpLastFocus=document.activeElement;cmpDrillAxis=null;
  $("#cmpscrim").classList.add("on");   // show first so the plot measures the real width
  cmpRender();
  $("#cmp-x").focus();
  document.addEventListener("keydown",cmpKey);
}
function closeCmp(){$("#cmpscrim").classList.remove("on");document.removeEventListener("keydown",cmpKey);if(cmpLastFocus)cmpLastFocus.focus();}
function cmpKey(e){
  if(e.key==="Escape"){closeCmp();return;}
  if(e.key==="Tab"){const f=$$('button, a[href], [tabindex]:not([tabindex="-1"])',$("#cmpbox")).filter(el=>!el.disabled&&el.offsetParent!==null);if(!f.length)return;const first=f[0],last=f[f.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
}
function cmpSpread(id){const vs=compare.map(s=>axScore(prof(s),id)).filter(a=>a&&a.score!==null).map(a=>a.score);return vs.length>1?Math.max(...vs)-Math.min(...vs):0;}
function cmpOrdered(){const ids=ORDER.filter(id=>cmpMeta(id));if(cmpSort==="diff")return ids.map(id=>({id,sp:cmpSpread(id)})).sort((a,b)=>b.sp-a.sp).map(o=>o.id);if(cmpSort==="sim")return ids.map(id=>({id,sp:cmpSpread(id)})).sort((a,b)=>a.sp-b.sp).map(o=>o.id);return ids;}
function cmpRenderTools(){$("#cmp-tools").innerHTML=compare.map((s,i)=>`<span class="tchip"><span class="tdot" style="background:var(${TCOL[i]})"></span>${esc(prof(s).name)}<button class="rm" aria-label="Remove ${esc(prof(s).name)}" onclick="toggleCompare('${s}')">&times;</button></span>`).join("");}
function cmpRenderSummary(){
  const box=$("#cmp-sum");
  if(compare.length<2){box.innerHTML="Add one more methodology to compare.";return;}
  const ranked=ORDER.filter(id=>cmpMeta(id)).map(id=>({id,sp:cmpSpread(id)})).sort((a,b)=>b.sp-a.sp);
  const top=ranked[0];
  if(!top||top.sp<3){box.innerHTML=`These ${compare.length} land close together on every axis, no standout differences.`;return;}
  const a=cmpMeta(top.id);
  const leans=compare.map(s=>{const v=axScore(prof(s),top.id);if(!v||v.score===null)return null;const w=v.score<0?`<span class="pn">${esc(a.neg)}</span>`:`<span class="pp">${esc(a.pos)}</span>`;return `${esc(prof(s).name)} ${w}`;}).filter(Boolean).join(", ");
  box.innerHTML=`<span class="k">Biggest gap</span> &mdash; ${esc(a.title)}: ${leans}.`;
}
function cmpBar(score,scale,cov){
  if(score===null)return `<div class="tk"><div class="c"></div></div>`;
  const cls=score<0?"neg":"pos",pct=Math.min(100,Math.abs(score)/scale*50),prov=cov<0.5?" prov":"";
  return `<div class="tk"><div class="c"></div><div class="f ${cls}${prov}" style="${score<0?'right:50%;width':'left:50%;width'}:${pct}%"></div></div>`;
}
function cmpBarsMatrix(){
  const cols=compare.length,maxSp=Math.max(1,...cmpOrdered().map(id=>cmpSpread(id)));
  const head=`<div class="h gut"></div>`+compare.map((s,i)=>{const p=prof(s),cov=Math.round(p.axes.reduce((a,x)=>a+x.coverage,0)/p.axes.length*100);return `<div class="h thead"><span class="tname"><span class="tdot" style="background:var(${TCOL[i]})"></span>${esc(p.name)}</span><span class="tcov">${cov}% evidence</span></div>`;}).join("");
  const rows=cmpOrdered().map(id=>{
    const a=cmpMeta(id),sp=cmpSpread(id),pipW=6+Math.round(sp/maxSp*46);
    const gut=`<div class="gut"><div class="ax-t">${esc(a.title)}<button class="axtip-btn" type="button" aria-label="What ${esc(a.title)} means">i<span class="axtip"><span class="pn">${esc(a.neg)}</span>: ${esc(a.eneg)}<br><span class="pp">${esc(a.pos)}</span>: ${esc(a.epos)}</span></button></div><div class="ax-p"><span class="pn">${esc(a.neg)}</span> &harr; <span class="pp">${esc(a.pos)}</span></div><div class="ax-spread"><span class="spread-pip" style="width:${pipW}px"></span>${sp>0?sp.toFixed(1)+" apart":"&mdash;"}</div><button class="sig-link" type="button" data-axis="${id}" onclick="cmpDrill('${id}')">signals &rsaquo;</button></div>`;
    const cells=compare.map(s=>{const rax=prof(s).axes.find(x=>x.axis_id===id),sc=rax?rax.score:null,cov=rax?rax.coverage:0,scale=rax&&rax.scale?rax.scale:10;const numCls=sc===null?"na":(sc<0?"neg":"pos"),num=sc===null?"no reading":(sc>0?"+":"")+sc.toFixed(1);return `<div class="cell">${cmpBar(sc,scale,cov)}<span class="num ${numCls}">${num}</span></div>`;}).join("");
    return gut+cells;
  }).join("");
  return `<div class="mxscroll"><div class="mx" style="grid-template-columns:minmax(150px,230px) repeat(${cols},minmax(130px,1fr))">${head}${rows}</div></div>`;
}
function cmpMarker(x,y,i,col){if(i===0)return `<circle cx="${x}" cy="${y}" r="3.6" fill="${col}"/>`;if(i===1)return `<polygon points="${x},${y-4} ${x+4},${y+3} ${x-4},${y+3}" fill="${col}"/>`;return `<rect x="${x-3.2}" y="${y-3.2}" width="6.4" height="6.4" fill="${col}"/>`;}
function cmpRenderLegend(){const el=$("#cmppleg");if(!el)return;el.innerHTML=compare.map((s,i)=>`<span class="li"><svg width="24" height="12">${cmpMarker(12,6,i,`var(${TCOL[i]})`)}<line x1="2" y1="6" x2="22" y2="6" stroke="var(${TCOL[i]})" stroke-width="2.5"/></svg>${esc(prof(s).name)}</span>`).join("");}
function cmpDrawPlot(){
  const svg=$("#cmpplot");if(!svg)return;
  const axs=ORDER.filter(id=>cmpMeta(id)).map(cmpMeta);
  const avail=(svg.parentElement&&svg.parentElement.clientWidth)||820;
  const W=Math.max(avail,axs.length*62+80),H=210,padX=42,padT=24,padB=26,scale=10;
  svg.style.width=W+"px";svg.setAttribute("width",W);svg.setAttribute("height",H);
  const xF=i=>axs.length===1?W/2:padX+i*(W-2*padX)/(axs.length-1);
  const yF=v=>padT+(scale-v)/(2*scale)*(H-padT-padB);
  const half=axs.length>1?(W-2*padX)/(axs.length-1)/2:60;
  let s="";
  axs.forEach((a,i)=>{const x=xF(i);
    s+=`<rect x="${(x-half).toFixed(1)}" y="0" width="${(half*2).toFixed(1)}" height="${H}" fill="transparent" style="cursor:pointer" onclick="cmpDrill('${a.id}')"><title>${esc(a.title)}</title></rect>`;
    s+=`<line x1="${x}" y1="${padT}" x2="${x}" y2="${H-padB}" stroke="var(--line)" style="pointer-events:none"/>`;
    s+=`<line x1="${x-4}" y1="${yF(0)}" x2="${x+4}" y2="${yF(0)}" stroke="var(--faint)" style="pointer-events:none"/>`;
    s+=`<text x="${x}" y="${padT-9}" text-anchor="middle" font-size="8" fill="var(--pos)" font-family="var(--sans)" style="pointer-events:none">${esc(a.pos)}</text>`;
    s+=`<text x="${x}" y="${H-padB+13}" text-anchor="middle" font-size="8" fill="var(--neg)" font-family="var(--sans)" style="pointer-events:none">${esc(a.neg)}</text>`;});
  compare.forEach((slug,ti)=>{const p=prof(slug),col=`var(${TCOL[ti]})`;
    const pts=axs.map((a,i)=>{const v=axScore(p,a.id);return (v&&v.score!==null)?[xF(i),yF(v.score)]:null;});
    s+=`<polyline class="tline" points="${pts.filter(Boolean).map(pt=>pt.map(n=>n.toFixed(1)).join(",")).join(" ")}" fill="none" stroke="${col}" stroke-width="2" opacity=".9"><title>${esc(p.name)}</title></polyline>`;
    pts.forEach(pt=>{if(pt)s+=cmpMarker(pt[0].toFixed(1),pt[1].toFixed(1),ti,col);});});
  svg.innerHTML=s;
}
function cmpToggleShape(){cmpShapeOpen=!cmpShapeOpen;const b=$("#cmpshapebody"),t=$("#cmpshapetog");t.setAttribute("aria-expanded",cmpShapeOpen);b.hidden=!cmpShapeOpen;if(cmpShapeOpen){cmpRenderLegend();cmpDrawPlot();}}
function cmpRenderCombined(){
  const body=$("#cmp-body");
  body.innerHTML=`<div class="bctl"><span class="lbl">Sort by</span><div class="seg" role="group" aria-label="Sort rows by"><button id="cmp-s-diff" aria-pressed="${cmpSort==='diff'}">Most different</button><button id="cmp-s-sim" aria-pressed="${cmpSort==='sim'}">Most similar</button><button id="cmp-s-std" aria-pressed="${cmpSort==='std'}">Default order</button></div></div><div class="shape-sec"><div class="shape-hd"><button class="shape-tog" id="cmpshapetog" aria-expanded="${cmpShapeOpen}" aria-controls="cmpshapebody" aria-label="Show or hide the shape chart"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1 L10 6 L3 11 Z" fill="currentColor"/></svg></button><div class="plegend" id="cmppleg"></div></div><div class="shape-body" id="cmpshapebody"${cmpShapeOpen?"":" hidden"}><div class="plotscroll"><svg id="cmpplot"></svg></div><p class="plottip">Click any axis to see the signals behind it.</p></div></div>${cmpBarsMatrix()}`;
  $("#cmp-s-diff").onclick=()=>{cmpSort="diff";cmpRenderCombined();cmpRenderSummary();};
  $("#cmp-s-sim").onclick=()=>{cmpSort="sim";cmpRenderCombined();cmpRenderSummary();};
  $("#cmp-s-std").onclick=()=>{cmpSort="std";cmpRenderCombined();cmpRenderSummary();};
  $("#cmpshapetog").onclick=cmpToggleShape;
  cmpRenderLegend();
  if(cmpShapeOpen)cmpDrawPlot();
}
function cmpRenderSignals(id){
  const a=cmpMeta(id),body=$("#cmp-body");
  const cols=compare.map((s,i)=>{
    const p=prof(s),rax=p.axes.find(x=>x.axis_id===id),sc=rax?rax.score:null;
    const scCls=sc===null?"na":(sc<0?"neg":"pos"),scTxt=sc===null?"no reading":(sc>0?"+":"")+sc.toFixed(1);
    const inds=(rax&&rax.indicators)?rax.indicators:[];
    const items=inds.length?inds.map(ir=>{const kind=ir.kind==="measured"?"detected":"judged";const v=ir.value,vCls=v==null?"zero":(v<0?"neg":(v>0?"pos":"zero")),vTxt=v==null?"":(v>0?"+":"")+(+v).toFixed(2);const ev=ir.evidence?`<div class="sig-ev">&ldquo;${esc(ir.evidence)}&rdquo;</div>`:`<div class="sig-ev empty">no quote recorded</div>`;const ans=ir.answer&&ir.answer!=="-"?` &middot; ${esc(ir.answer)}`:"";return `<div class="sig-item"><div class="sig-top"><span class="kind ${kind}">${kind}</span><span class="sig-id">${esc(ir.indicator_id)}${ans}</span><span class="sig-v ${vCls}">${vTxt}</span></div>${ev}<div class="sig-src">${esc(ir.source||"")}</div></div>`;}).join(""):`<div class="sig-ev empty">no signals recorded</div>`;
    return `<div class="sig-tool"><div class="sh"><span class="stname"><span class="tdot" style="background:var(${TCOL[i]})"></span>${esc(p.name)}</span><span class="stsc ${scCls}">${scTxt}</span></div>${items}</div>`;
  }).join("");
  body.innerHTML=`<button class="drill-back" type="button" onclick="cmpUndrill()"><span class="chev" aria-hidden="true">&lsaquo;</span> Back to compare</button><h3 class="drill-h">${esc(a.title)}</h3><p class="drill-sub"><span class="pn">${esc(a.neg)}</span> &harr; <span class="pp">${esc(a.pos)}</span> &middot; the signals behind each position, <b>detected</b> by the engine or <b>judged</b> by a reviewer reading the repo.</p><div class="sig-cols">${cols}</div>`;
}
function playDrillAnim(cls){const b=$("#cmp-body");if(!b)return;b.classList.remove("din","dback");void b.offsetWidth;b.classList.add(cls);}
function cmpDrill(id){cmpDrillAxis=id;cmpRender();$("#cmp-body").scrollTop=0;playDrillAnim("din");const back=$(".drill-back");if(back)back.focus();}
function cmpUndrill(){const from=cmpDrillAxis;cmpDrillAxis=null;cmpRender();playDrillAnim("dback");const lnk=from&&$('.sig-link[data-axis="'+from+'"]');if(lnk)lnk.focus();}
function cmpRender(){
  cmpRenderTools();cmpRenderSummary();
  if(compare.length<2){$("#cmp-body").innerHTML='<div class="empty">Add one more methodology to compare.</div>';return;}
  if(cmpDrillAxis){cmpRenderSignals(cmpDrillAxis);return;}
  cmpRenderCombined();
}

function update(){renderPlot();renderSignatures();renderFitLines();}
document.addEventListener("DOMContentLoaded",()=>{
  buildPanel();renderCards();renderPlot();renderTray();syncCompareButtons();
  $("#plot").addEventListener("click",e=>{const t=e.target.closest("[data-slug]");if(t)location.href="profiles/"+t.dataset.slug+".html";});
  document.addEventListener("click",()=>$$(".tip.show").forEach(t=>t.classList.remove("show")));
  window.addEventListener("resize",renderPlot);
  $("#cmp-x").onclick=closeCmp;
  $("#cmpscrim").addEventListener("click",e=>{if(e.target===$("#cmpscrim"))closeCmp();});
  window.addEventListener("resize",()=>{if($("#cmpscrim").classList.contains("on")&&cmpShapeOpen&&!cmpDrillAxis&&$("#cmpplot"))cmpDrawPlot();});
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


BROOM = (
    "<svg viewBox='0 0 24 24' width='16' height='16' fill='currentColor' aria-hidden='true'>"
    "<path d='M19.36 2.72l1.42 1.42-5.72 5.71c1.07 1.54 1.22 3.39.32 4.59L9.06 8.83c1.2-.9 3.05-.75"
    " 4.59.32l5.71-5.72M5.93 17.57c-2.01-2.01-3.24-4.41-3.58-6.65l4.88-2.09 7.44 7.44-2.09 4.88c-2.24"
    "-.34-4.64-1.57-6.65-3.58z'/></svg>"
)


def _display_name(target: str) -> str:
    """Last path segment, matching report.py's pill (full target stays in the JSON)."""
    name = target.rstrip("/").rsplit("/", 1)[-1]
    name = name.removesuffix(".git")
    return name or target


def build():
    files = sorted(glob.glob(os.path.join(PROFILES, "*.json")))
    data = []
    for f in files:
        slug = os.path.splitext(os.path.basename(f))[0]
        try:
            with open(f) as fh:
                p = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"skip {slug}: {e}")
            continue
        p["slug"] = slug
        p["name"] = _display_name(p.get("target", ""))
        data.append(p)
    if not data:
        print("no profiles found in", PROFILES)
        return 1
    os.makedirs(os.path.join(OUT, "profiles"), exist_ok=True)
    for p in data:
        src = os.path.join(PROFILES, p["slug"] + ".html")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, "profiles", p["slug"] + ".html"))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agentic Atlas, find your fit</title><style>{CSS}</style></head><body><div class="wrap">
<header class="top"><div class="brand"><svg class="mark" viewBox="0 0 30 31" aria-hidden="true"><polygon points="15,1 4,11 15,11" fill="var(--neg)"/><polygon points="15,1 26,11 15,11" fill="var(--pos)"/><polygon points="4,11 15,11 15,30" fill="var(--neg)" opacity=".8"/><polygon points="26,11 15,11 15,30" fill="var(--pos)" opacity=".8"/><polygon points="15,1 4,11 15,30 26,11" fill="none" stroke="var(--accent)" stroke-width="1" opacity=".55"/></svg><span class="word">Agentic Atlas</span></div><span class="spacer"></span><a class="repo" href="https://github.com/AdamCaviness/agentic-atlas" target="_blank" rel="noopener" aria-label="Open agentic-atlas on GitHub (opens in a new tab)" title="Open agentic-atlas on GitHub">{GH_MARK}</a></header>
<section class="hero">
<p class="lead">Profile agentic development methodologies, frameworks, and skill collections on shared axes, and see if one fits you and your projects.</p>
<p class="sub2">A deterministic engine over an open, versioned, community-driven rubric. Hosted profiles of popular tools, run it yourself and help improve it.</p>
<p class="principle">There's no right or wrong, and these aren't judgments, just measurements based on our community-driven rubric.</p>
</section>
<div class="layout">
  <aside class="panel"><div class="phead"><h2>Your preferences</h2><button class="clr" onclick="clearAll()" title="Clear all preferences" aria-label="Clear all preferences">{BROOM}</button></div><p class="sub">Set only what matters. Untouched sliders mean no preference.</p><div id="prefs"></div><div id="matches" class="matches"></div></aside>
  <main>
  <svg id="plot" style="display:none"></svg>
  <div id="gallery" class="gallery"></div>
  <div id="tray" class="tray"></div></main>
</div></div>
<div class="scrim" id="cmpscrim" role="dialog" aria-modal="true" aria-labelledby="cmp-title">
  <div class="cmp" id="cmpbox">
    <div class="cmp-hd"><h2 id="cmp-title">Compare</h2><div class="cmp-tools" id="cmp-tools"></div><button class="cmp-x" id="cmp-x" aria-label="Close compare">&times;</button></div>
    <div class="cmp-sum" id="cmp-sum"></div>
    <div class="cmp-body" id="cmp-body"></div>
    <div class="cmp-ft"><p class="principle">There's no right or wrong, and these aren't judgments, just measurements based on our community-driven rubric.</p><p class="evi"><span class="swatch"></span> faded / striped = little evidence behind that reading</p></div>
  </div>
</div>
<script>const DATA={json.dumps(data)};</script><script>{JS}</script></body></html>"""
    out_index = os.path.join(OUT, "index.html")
    with open(out_index, "w") as fh:
        fh.write(page)
    print(f"built {out_index} with {len(data)} profiles")
    print("profiles:", ", ".join(p["slug"] for p in data))
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
