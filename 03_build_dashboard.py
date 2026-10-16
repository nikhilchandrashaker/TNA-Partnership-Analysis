"""Generate dashboard/index.html (self-contained, no external requests) from data/*.csv + results.json.
Run: python scripts/03_build_dashboard.py
"""
import json
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / "data"
res = json.loads((D / "results.json").read_text())


def recs(name, cols=None):
    df = pd.read_csv(D / name).fillna("")
    if cols:
        df = df[cols]
    return df.to_dict(orient="records")


payload = {
    "results": res,
    "events": recs("events_clean.csv", ["event_id", "date", "partnership_code", "host_promotion", "show_name", "item_type",
                                         "participants", "result_or_outcome", "title_involved", "evidence_tier",
                                         "verification_status", "source_url"]),
    "titles": recs("title_reigns.csv"),
    "talent": recs("talent_movement.csv"),
    "tv": recs("audience_tv_impact_aew_era.csv"),
    "ctx": recs("audience_context.csv"),
    "sources": recs("sources.csv"),
    "audit": recs("completeness_audit.csv"),
}
data_js = json.dumps(payload, default=str).replace("</", "<\\/")

HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>TNA Partnership Analytics: AEW vs WWE/NXT</title>
<style>
:root{--bg:#fafaf9;--panel:#fff;--ink:#1c1917;--mut:#57534e;--line:#e7e5e4;--aew:#c2410c;--nxt:#1d4ed8;--warn-bg:#fef3c7;--warn-ink:#78350f;--ok:#166534;--bad:#991b1b;
box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0c0a09;--panel:#1c1917;--ink:#f5f5f4;--mut:#a8a29e;--line:#2e2a27;--aew:#fb923c;--nxt:#60a5fa;--warn-bg:#422006;--warn-ink:#fde68a;--ok:#4ade80;--bad:#f87171}}
:root[data-theme="dark"]{--bg:#0c0a09;--panel:#1c1917;--ink:#f5f5f4;--mut:#a8a29e;--line:#2e2a27;--aew:#fb923c;--nxt:#60a5fa;--warn-bg:#422006;--warn-ink:#fde68a;--ok:#4ade80;--bad:#f87171}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:1.6rem;margin:0 0 4px;letter-spacing:-.01em} h2{font-size:1.15rem;margin:0 0 10px} h3{font-size:.95rem;margin:14px 0 6px}
.sub{color:var(--mut);margin:0 0 14px}
.banner{background:var(--warn-bg);color:var(--warn-ink);border-radius:10px;padding:10px 14px;font-size:.88rem;margin:12px 0}
nav{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0;border-bottom:1px solid var(--line);padding-bottom:10px}
nav button{background:transparent;border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit;font-size:.88rem;cursor:pointer}
nav button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.kpi{font-size:2rem;font-weight:700;line-height:1.1} .kpi small{font-size:.8rem;font-weight:400;color:var(--mut)}
.aew{color:var(--aew)} .nxt{color:var(--nxt)}
.tbl{width:100%;border-collapse:collapse;font-size:.86rem} .tbl th,.tbl td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.tbl th{font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.scroll{overflow-x:auto;max-width:100%}
.pill{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.72rem;border:1px solid var(--line);white-space:nowrap}
.rel-LOW,.rel-NONE{color:var(--bad)} .rel-MEDIUM,.rel-MEDIUM-LOW{color:var(--warn-ink);background:var(--warn-bg)} .rel-HIGH,.rel-MEDIUM-HIGH{color:var(--ok)}
a{color:var(--nxt)} .mut{color:var(--mut)} .small{font-size:.8rem}
select,input{font:inherit;font-size:.88rem;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink)}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
svg text{fill:var(--mut);font-size:11px;font-family:inherit}
.legend span{display:inline-block;margin-right:14px;font-size:.82rem} .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
.hidden{display:none}
</style></head><body><div class="wrap">
<h1>TNA partnership analytics</h1>
<p class="sub">Which outside partnership delivered more measurable benefit to TNA: the 2020&ndash;21 AEW/Impact crossover or the 2024&ndash;26 WWE/NXT partnership? Last data refresh: October 2026.</p>
<div class="banner"><b>Read this first.</b> Match counts are research <i>leads</i> from a partly community-sourced seed list, not a verified census. TNA TV viewership exists for the AEW era only; the NXT era has no usable audience series, so the business-impact question cannot be answered head-to-head. No composite winner is declared on purpose.</div>
<nav id="nav"></nav>
<div id="view"></div>
<p class="small mut" style="margin-top:28px">Reproducible package: cleaned CSVs, scripts, notebook and paper accompany this page. Blank = unknown, never zero.</p>
</div>
<script>
const DATA = __DATA__;
const R = DATA.results;
const $ = (s,el=document)=>el.querySelector(s);
const esc = s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const link = u=>u? `<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">source</a>`:'';
const fmt = n=> typeof n==='number'? n.toLocaleString():esc(n);
const tabs = [['score','Head-to-head'],['tv','TV audience'],['titles','Title reigns'],['talent','Talent movement'],['events','Event explorer'],['quality','Data quality & sources']];
let cur = 'score';
function nav(){ $('#nav').innerHTML = tabs.map(([k,l])=>`<button class="${k===cur?'on':''}" data-k="${k}">${l}</button>`).join('');
  $('#nav').querySelectorAll('button').forEach(b=>b.onclick=()=>{cur=b.dataset.k;render();}); }
function relCls(r){const k=r.split(' ')[0].replace('-','_'); const m=r.split(' ')[0]; return 'rel-'+m;}

function viewScore(){
  const A=R.titles[0], N=R.titles[1], t=R.tv_event_study;
  const rows = R.scorecard.map(r=>`<tr><td><b>${esc(r.dimension)}</b></td><td>${esc(r.metric)}</td><td class="aew">${fmt(r.AEW)}</td><td class="nxt">${fmt(r.NXT)}</td><td><span class="pill ${relCls(r.reliability)}">${esc(r.reliability.split(' - ')[0])}</span><div class="small mut">${esc(r.reliability.split(' - ').slice(1).join(' - '))}</div></td></tr>`).join('');
  return `<div class="grid">
   <div class="card"><div class="mut small">AEW era: TNA TV lift vs baseline</div><div class="kpi aew">+${t.lift_pct.toFixed(0)}%<small> (95% CI +${t.boot95_lift_pct[0].toFixed(0)} to +${t.boot95_lift_pct[1].toFixed(0)}%)</small></div><div class="small mut">Before/after only, no control series. Dec 8 2020 spike faded within a week.</div></div>
   <div class="card"><div class="mut small">TNA-title reigns in crossover context</div><div class="kpi"><span class="aew">${A.reigns_in_crossover_context}</span> <small>AEW</small> &nbsp; <span class="nxt">${N.reigns_in_crossover_context}</span> <small>NXT</small></div><div class="small mut">Not era-adjusted; NXT window is longer (2025&ndash;26 vs Apr&ndash;Aug 2021).</div></div>
   <div class="card"><div class="mut small">TNA talent who moved to WWE (reported)</div><div class="kpi"><span class="aew">${R.talent.tna_to_aew}</span> <small>to AEW</small> &nbsp; <span class="nxt">${R.talent.tna_to_wwe}</span> <small>to WWE</small></div><div class="small mut">Ambiguous: pipeline benefit or talent loss.</div></div>
  </div>
  <div class="card"><h2>Scorecard by dimension</h2><div class="scroll"><table class="tbl"><thead><tr><th>Dimension</th><th>Metric</th><th>AEW era</th><th>NXT era</th><th>Reliability</th></tr></thead><tbody>${rows}</tbody></table></div>
  <p class="small mut">Each dimension is shown separately. A partnership can lead on booking and trail on business impact; combining them would need weights this evidence cannot justify.</p></div>
  <div class="card"><h2>What the evidence supports</h2><ul>
   <li><b>Booking value:</b> NXT-era crossover gave TNA titles to more outside-context champions across more belts (7 vs 2), including the world title once and Knockouts title six times. AEW-era delivered two world-title reigns, both marquee.</li>
   <li><b>Business impact:</b> only the AEW era is measurable: roughly +23% above the pre-Omega baseline across 9 episodes, with no difference between episodes that had AEW talent and those that did not (permutation p=${R.tv_partner_vs_not.perm_p_two_sided.toFixed(2)}).</li>
   <li><b>Cannot conclude:</b> which partnership was better overall. Audience, attendance and revenue data for the NXT era are missing or confounded (AXS&rarr;AMC move in Jan 2026).</li></ul></div>`;
}

function lineChart(){
  const tv=DATA.tv; const W=980,H=320,m={l:52,r:16,t:16,b:34};
  const xs=tv.map(r=>new Date(r.date).getTime()); const x0=Math.min(...xs), x1=Math.max(...xs);
  const y0=80000,y1=240000;
  const X=t=>m.l+(t-x0)/(x1-x0)*(W-m.l-m.r), Y=v=>H-m.b-(v-y0)/(y1-y0)*(H-m.t-m.b);
  let s=`<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Weekly Impact viewership Dec 2020 to Apr 2021">`;
  for(let v=100000;v<=240000;v+=40000){s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${m.l-6}" y="${Y(v)+4}" text-anchor="end">${v/1000}k</text>`;}
  s+=`<line x1="${m.l}" x2="${W-m.r}" y1="${Y(141000)}" y2="${Y(141000)}" stroke="var(--mut)" stroke-dasharray="5 4"/><text x="${m.l+6}" y="${Y(141000)-5}">pre-Omega baseline 141k</text>`;
  s+=`<polyline fill="none" stroke="var(--line)" stroke-width="2" points="${tv.map(r=>X(new Date(r.date).getTime())+','+Y(r.viewers)).join(' ')}"/>`;
  tv.forEach(r=>{const cx=X(new Date(r.date).getTime()),cy=Y(r.viewers);
    const c=r.special_repeat_episode==1?'var(--mut)':(r.partner_on_show==1?'var(--aew)':'var(--ink)');
    s+=r.special_repeat_episode==1?`<text x="${cx}" y="${cy+4}" text-anchor="middle" style="fill:var(--mut);font-size:14px">&times;</text>`:`<circle cx="${cx}" cy="${cy}" r="5" fill="${c}"><title>${r.date}: ${r.viewers.toLocaleString()} viewers. ${esc(r.note)}</title></circle>`;});
  [['2020-12-01','Dec 20'],['2021-01-01','Jan 21'],['2021-02-01','Feb 21'],['2021-04-01','Apr 21']].forEach(([d,l])=>{s+=`<text x="${X(new Date(d).getTime())}" y="${H-10}" text-anchor="middle">${l}</text>`;});
  return s+'</svg>';
}
function viewTV(){
  const t=R.tv_event_study;
  const sens=R.tv_sensitivity.map(s=>`<tr><td>${esc(s.scenario)}</td><td>${s.n}</td><td>${Math.round(s.mean).toLocaleString()}</td><td>${s.lift_pct>=0?'+':''}${s.lift_pct.toFixed(1)}%</td></tr>`).join('');
  const ctx=DATA.ctx.map(c=>`<tr><td>${esc(c.period)}</td><td>${esc(c.measure)}</td><td>${fmt(c.value)} <span class="mut">${esc(c.unit)}</span></td><td class="small mut">${esc(c.caveat)} ${link(c.source_url)}</td></tr>`).join('');
  return `<div class="card"><h2>TNA/Impact weekly viewers, AEW crossover era</h2><div class="legend"><span><i class="dot" style="background:var(--aew)"></i>AEW talent on show</span><span><i class="dot" style="background:var(--ink)"></i>other episode</span><span>&times; holiday repeat</span></div>${lineChart()}
  <p class="small mut">Source: F4WOnline reports of Nielsen data (AXS TV). Hover points for notes. Baseline (141k) is a published mean without variance.</p></div>
  <div class="card"><h2>Result</h2><p>Post-debut mean (Dec 8&ndash;Feb 16, n=${t.n_post}, repeats excluded): <b>${Math.round(t.post_mean).toLocaleString()}</b> vs baseline <b>141,000</b> &rarr; <b>+${t.lift_pct.toFixed(1)}%</b> (bootstrap 95% CI +${t.boot95_lift_pct[0].toFixed(0)}% to +${t.boot95_lift_pct[1].toFixed(0)}%). The CI reflects post-period spread only. Episodes with AEW talent averaged ${Math.round(R.tv_partner_vs_not.mean_partner).toLocaleString()} vs ${Math.round(R.tv_partner_vs_not.mean_other).toLocaleString()} for others (permutation p=${R.tv_partner_vs_not.perm_p_two_sided.toFixed(2)}), so the lift is not attributable to individual crossover appearances. Possible confounds: storylines, season, and the Jan 2021 news cycle.</p>
  <h3>Sensitivity</h3><div class="scroll"><table class="tbl"><thead><tr><th>Scenario</th><th>n</th><th>Mean viewers</th><th>Lift vs baseline</th></tr></thead><tbody>${sens}</tbody></table></div>
  <p class="small mut">Using the single week before (Dec 1, 166k) as baseline cuts the lift to about +5%. The headline depends on baseline choice.</p></div>
  <div class="card"><h2>NXT era: not estimable</h2><ul>${R.nxt_era_tv.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>
  <h3>Reference points (different metrics; do not compare directly)</h3><div class="scroll"><table class="tbl"><thead><tr><th>Period</th><th>Measure</th><th>Value</th><th>Caveat</th></tr></thead><tbody>${ctx}</tbody></table></div></div>`;
}

function viewTitles(){
  const rows=DATA.titles.map(t=>`<tr><td><span class="pill" style="border-color:${t.partnership==='AEW'?'var(--aew)':'var(--nxt)'}">${esc(t.partnership)}</span></td><td><b>${esc(t.champion)}</b><div class="small mut">${esc(t.title)}</div></td><td>${esc(t.date_won)}<div class="small mut">${esc(t.won_at_event)} (${esc(t.won_on_host_show)})</div></td><td>${esc(t.date_lost)||'&mdash;'}<div class="small mut">${esc(t.lost_at_event)} ${t.lost_on_host_show?'('+esc(t.lost_on_host_show)+')':''}</div></td><td>${t.days_computed===''?'&mdash;':fmt(Number(t.days_computed))}</td><td class="small">${esc(t.verification_status)}<br>${link(t.source_url)}<div class="mut">${esc(t.notes)}</div></td></tr>`).join('');
  const A=R.titles[0],N=R.titles[1];
  return `<div class="card"><h2>Crossover-era title reigns</h2>
  <p class="small mut">Recorded by <b>where the title was won</b> (host show), not by the wrestler's promotion. Titles are TNA-owned except the Hardys' NXT Tag Team reign (reverse direction). Not yet a census of every TNA lineage.</p>
  <div class="grid"><div class="card"><div class="aew kpi">${A.tna_title_reigns}<small> TNA-title reigns, ${A.total_days_held} days</small></div><div class="small mut">${A.world_title_reigns} world-title reigns; 1 won on AEW Rampage</div></div>
  <div class="card"><div class="nxt kpi">${N.tna_title_reigns}<small> TNA-title reigns, ${N.total_days_held} days</small></div><div class="small mut">${N.world_title_reigns} world, ${N.knockouts_world_reigns} Knockouts World, ${N.distinct_titles} distinct titles; ${N.won_on_partner_programming} won on NXT shows; +${N.reverse_direction_reigns} NXT-owned reign</div></div></div>
  <div class="scroll"><table class="tbl"><thead><tr><th>Era</th><th>Champion / title</th><th>Won</th><th>Lost</th><th>Days</th><th>Verification</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

function viewTalent(){
  const rows=DATA.talent.map(t=>`<tr><td><b>${esc(t.wrestler)}</b></td><td>${esc(t.previous_promotion)} &rarr; ${esc(t.new_promotion)}</td><td>${esc(t.movement_date)}</td><td class="small">${esc(t.contract_status)}<div class="mut">${esc(t.notes)}</div></td><td><span class="pill">${esc(t.partnership)}</span></td><td class="small">${esc(t.source_type)}<br>${link(t.source_url)}</td></tr>`).join('');
  return `<div class="card"><h2>Talent movement</h2><p class="small mut">Reported signings, departures and retentions tied to either partnership. Three TNA stars (Grace, Hendry, Santana) moved to WWE during the NXT era; no verified TNA-to-AEW move was found in the AEW era. Whether that is pipeline benefit or talent loss for TNA is a judgment this data cannot settle. Official confirmation not checked for any row.</p>
  <div class="scroll"><table class="tbl"><thead><tr><th>Wrestler</th><th>Move</th><th>Date</th><th>Status / notes</th><th>Era</th><th>Source</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

let F={p:'all',t:'all',q:''};
function viewEvents(){
  const tiers={A_primary:'primary verified',C_secondary_lead:'secondary lead',S_segment:'segment'};
  const list=DATA.events.filter(e=>(F.p==='all'||e.partnership_code===F.p)&&(F.t==='all'||e.evidence_tier===F.t)&&(!F.q||(e.participants+' '+e.show_name).toLowerCase().includes(F.q.toLowerCase())));
  const rows=list.slice(0,300).map(e=>`<tr><td>${esc(e.date)||'<span class="mut">undated</span>'}</td><td><span class="pill" style="border-color:${e.partnership_code==='AEW'?'var(--aew)':'var(--nxt)'}">${e.partnership_code}</span></td><td>${esc(e.show_name)}<div class="small mut">${esc(e.host_promotion)}</div></td><td>${esc(e.participants)}</td><td class="small">${tiers[e.evidence_tier]||esc(e.evidence_tier)} ${link(e.source_url)}</td></tr>`).join('');
  return `<div class="card"><h2>Event explorer <span class="mut small">(${list.length} of ${DATA.events.length} rows)</span></h2>
  <div class="filters"><select id="fp"><option value="all">Both partnerships</option><option value="AEW">AEW era</option><option value="NXT">NXT era</option></select>
  <select id="ft"><option value="all">All evidence tiers</option><option value="A_primary">Primary verified</option><option value="C_secondary_lead">Secondary leads</option><option value="S_segment">Segments</option></select>
  <input id="fq" placeholder="Search wrestler or show" value="${esc(F.q)}"></div>
  <div class="scroll"><table class="tbl"><thead><tr><th>Date</th><th>Era</th><th>Show</th><th>Participants</th><th>Evidence</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

function viewQuality(){
  const piv={}; DATA.audit.forEach(a=>{(piv[a.indicator]=piv[a.indicator]||{})[a.partnership]=a.count;});
  const rows=Object.entries(piv).map(([k,v])=>`<tr><td>${esc(k)}</td><td class="aew">${v['TNA/Impact-AEW']}</td><td class="nxt">${v['TNA-WWE/NXT']}</td></tr>`).join('');
  const src=DATA.sources.map(s=>`<tr><td>${esc(s.source)}</td><td class="small">${esc(s.research_use)}</td><td class="small">${esc(s.source_quality)}</td><td>${link(s.url)}</td></tr>`).join('');
  return `<div class="card"><h2>Data completeness audit</h2><div class="scroll"><table class="tbl"><thead><tr><th>Indicator</th><th>AEW era</th><th>NXT era</th></tr></thead><tbody>${rows}</tbody></table></div>
  <p class="small mut">A larger count does not mean a better partnership; it can mean more collection effort. 23 duplicate lead rows were removed from the seed list (94 &rarr; 71). Only 4 NXT-era and 0 AEW-era match rows are primary-source verified.</p></div>
  <div class="card"><h2>Source log</h2><div class="scroll"><table class="tbl"><thead><tr><th>Source</th><th>Used for</th><th>Quality</th><th></th></tr></thead><tbody>${src}</tbody></table></div></div>
  <div class="card"><h2>Known limitations</h2><ul><li>No attendance, gate, PPV, streaming, sponsorship or revenue figures were collected for either era.</li><li>No control group, so no difference-in-differences estimate; pre-trends could not be tested.</li><li>The two eras differ in length, TV network, and TNA's own circumstances; raw counts are not era-adjusted.</li><li>Trade-press reports of talent moves are not official confirmations.</li></ul></div>`;
}

function render(){ nav(); const v={score:viewScore,tv:viewTV,titles:viewTitles,talent:viewTalent,events:viewEvents,quality:viewQuality}[cur]();
  $('#view').innerHTML=v;
  if(cur==='events'){ $('#fp').value=F.p; $('#ft').value=F.t;
    $('#fp').onchange=e=>{F.p=e.target.value;render();}; $('#ft').onchange=e=>{F.t=e.target.value;render();};
    $('#fq').oninput=e=>{F.q=e.target.value;const pos=e.target.selectionStart;render();const q=$('#fq');q.focus();q.setSelectionRange(pos,pos);}; } }
render();
</script></body></html>"""

out = HTML.replace("__DATA__", data_js)
(ROOT / "dashboard").mkdir(exist_ok=True)
(ROOT / "dashboard" / "index.html").write_text(out, encoding="utf-8")
print("dashboard bytes:", len(out))
