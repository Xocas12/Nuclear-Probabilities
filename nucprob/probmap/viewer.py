"""A static viewer of runs/probmap/: one page with its data inside it, no network requests.

    python -m nucprob.probmap.viewer

Writes runs/probmap/viewer/index.html. Grid cells only; no town appears in it.
"""

import json

import numpy as np
import pandas as pd

from nucprob.paths import RAW, RUNS
from nucprob.probmap.run import load_scenarios

OUT = RUNS / "probmap"
LAND = RAW / "naturalearth" / "ne_50m_land.geojson"
LAND_KEPT = OUT / "viewer" / "land.json"


def land_paths() -> list[list[list[float]]]:
    """The land outline at a degree-tenth, kept in the run folder so the viewer builds without raw data."""
    if not LAND.exists():
        return json.loads(LAND_KEPT.read_text())
    rings = []
    for f in json.loads(LAND.read_text())["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = np.round(np.array(poly[0])[::3], 1)
            if len(ring) >= 4:
                rings.append(ring.tolist())
    LAND_KEPT.parent.mkdir(parents=True, exist_ok=True)
    LAND_KEPT.write_text(json.dumps(rings, separators=(",", ":")))
    return rings


def payload() -> dict:
    summary = pd.read_csv(OUT / "scenarios.csv").set_index("scenario")
    spread = pd.read_csv(OUT / "score_spread.csv").set_index("scenario")
    delivered = pd.read_csv(OUT / "delivered.csv")
    items = []
    for sc in load_scenarios():
        c = pd.read_csv(OUT / "cells" / f"{sc['id']}.csv.gz")
        columns = ["cell_lat", "cell_lon", "p_median", "p_low", "p_high", "holds_sealed_town"]
        s = summary.loc[sc["id"]]
        d = delivered[delivered["scenario"] == sc["id"]]
        items.append(
            {
                "id": sc["id"],
                "label": sc["label"],
                "era": sc["era"],
                "evidence": sc["evidence"],
                "note": sc["note"],
                "deg": sc["cell_deg"],
                "shift_label": "Extrapolation" if sc["era"] == "modern" else "Historical",
                "towns": int(s["towns"]),
                "population_ratio": round(float(spread.loc[sc["id"], "population_ratio"])),
                "score_ratio": round(float(spread.loc[sc["id"], "score_ratio"]), 1),
                "delivered": d[
                    [
                        "attacker",
                        "delivered_low",
                        "delivered_median",
                        "delivered_high",
                        "on_scored_towns_median",
                    ]
                ].to_dict("records"),
                "cells": c[columns].round(2).to_numpy().tolist(),
            }
        )
    return {
        "scenarios": items,
        "land": land_paths(),
        "shift": pd.read_csv(OUT / "domain_shift.csv").round(2).to_dict("records")[:2],
        "score": json.loads((OUT / "manifest.json").read_text())["score"],
    }


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>P(area struck | stockpile scenario)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--land:#ecebe6;--line:#d5d4cc}
@media(prefers-color-scheme:dark){:root{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--land:#2b2b29;--line:#44443f}}
body{margin:0;background:var(--surface);color:var(--ink);font:15px/1.45 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:0 0 4px}
.warn{border-left:4px solid var(--ink);padding:6px 10px;margin:10px 0;font-weight:600}
.note{color:var(--ink2);margin:6px 0}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:10px 0}
select,button{font:inherit;padding:4px 8px;background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:4px}
canvas{width:100%;display:block;border:1px solid var(--line);border-radius:4px;touch-action:none}
#tip{position:fixed;display:none;pointer-events:none;background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:4px 8px;font-size:13px}
#legend{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--ink2)}
#ramp{width:200px;height:12px;border-radius:2px}
table{border-collapse:collapse;font-size:13px;width:100%}
td,th{padding:2px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
details{margin:12px 0}
</style></head><body><main>
<h1>Probability that an area is struck, given a stockpile scenario</h1>
<p class="note" id="method"></p>
<div class="row">
<label>Scenario <select id="sc"></select></label>
<label>Show <select id="band"><option value="2">median</option><option value="3">low end of the interval</option><option value="4">high end of the interval</option></select></label>
<div id="legend"><span>0</span><canvas id="ramp" width="200" height="12" style="border:0"></canvas><span>1</span></div>
</div>
<div class="warn" id="banner"></div>
<canvas id="map" width="1400" height="700"></canvas>
<p class="note" id="info"></p>
<details><summary>Warheads delivered in this scenario (attacker totals, inputs to the map)</summary><table id="del"></table></details>
<details><summary>Cells as a table, by position</summary><div style="max-height:320px;overflow:auto"><table id="tab"></table></div></details>
<div id="tip" role="status"></div>
</main><script>
const D=__DATA__;
document.getElementById("method").textContent=`The score here is the ${D.score}: each delivered warhead falls on a town with chance in proportion to a score that moves only a few times over the range of population, so a cell's probability depends on how many towns it holds as well as on its people (the spread for the scenario shown is under the map). What a town produced, housed or defended plays no part. These are consequences of stated assumptions, not forecasts. Theatre shares have no source. On the 1956 towns the map uses only the part of delivered warheads falling on towns outside the sealed set, shown in the table. The 1965 map has no United Kingdom: its only census table was withdrawn (robots), so the stated share falls on the five continental countries. The interval runs from the 5th to the 95th percentile of draws of the model and the stockpile; it holds the allocation rule, who fires on whom and the list of towns fixed, so it is narrower than what is unknown. See REPORT.md: no score has been shown to beat population on a document it has not seen.`;
const stops=[[205,226,251],[158,197,244],[109,167,236],[57,135,229],[28,92,171],[13,54,107]];
function col(p){const x=Math.min(.9999,Math.max(0,p))*(stops.length-1),i=Math.floor(x),f=x-i,a=stops[i],b=stops[i+1];return `rgb(${a.map((v,k)=>Math.round(v+(b[k]-v)*f)).join(",")})`}
const map=document.getElementById("map"),g=map.getContext("2d"),sel=document.getElementById("sc"),band=document.getElementById("band"),tip=document.getElementById("tip");
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n);
const r=document.getElementById("ramp").getContext("2d");for(let i=0;i<200;i++){r.fillStyle=col(i/199);r.fillRect(i,0,1,12)}
D.scenarios.forEach((s,i)=>sel.add(new Option(`${s.shift_label}: ${s.label}`,i)));
let view;
function frame(s){let a=1e9,b=-1e9,c=1e9,d=-1e9;for(const q of s.cells){a=Math.min(a,q[0]);b=Math.max(b,q[0]);c=Math.min(c,q[1]);d=Math.max(d,q[1])}
a-=2;b+=s.deg+2;c-=3;d+=s.deg+3;const k=Math.cos((a+b)/2*Math.PI/180);const sc=Math.min(map.width/((d-c)*k),map.height/(b-a));return{a,b,c,d,k,sc}}
const X=(v,lon)=>(lon-v.c)*v.k*v.sc,Y=(v,lat)=>map.height-(lat-v.a)*v.sc;
function draw(){const s=D.scenarios[sel.value],v=view=frame(s),b=+band.value;g.fillStyle=css("--surface");g.fillRect(0,0,map.width,map.height);
g.fillStyle=css("--land");for(const ring of D.land){g.beginPath();ring.forEach((p,i)=>i?g.lineTo(X(v,p[0]),Y(v,p[1])):g.moveTo(X(v,p[0]),Y(v,p[1])));g.closePath();g.fill()}
for(const q of s.cells){g.fillStyle=col(q[b]);const w=s.deg*v.k*v.sc,h=s.deg*v.sc;g.fillRect(X(v,q[1])+.5,Y(v,q[0]+s.deg)+.5,w-1,h-1);if(q[5]){g.strokeStyle=css("--ink");g.lineWidth=1;g.strokeRect(X(v,q[1])+1,Y(v,q[0]+s.deg)+1,w-2,h-2)}}
document.getElementById("banner").textContent=(s.era=="modern"?"EXTRAPOLATION. A score from Cold War lists applied to present-day towns from a map-label set. A classifier tells them from the training towns at ROC-AUC "+D.shift[0].value+" on ten features, where 0.5 is no shift. Not a statement about any present plan. ":"HISTORICAL. ")+s.evidence;
document.getElementById("info").textContent=`${s.note} ${s.towns} towns on a ${s.deg}-degree grid. Across them population runs over a ${s.population_ratio}-fold range and the median score over a ${s.score_ratio}-fold range.`+(s.cells.some(q=>q[5])?" Outlined cells hold a town of the sealed test set, which is not scored; a cell with only sealed towns is absent.":"");
document.getElementById("del").innerHTML="<tr><th>Attacker</th><th>5th</th><th>median</th><th>95th</th><th>median on scored towns</th></tr>"+s.delivered.map(d=>`<tr><td>${d.attacker}</td><td>${Math.round(d.delivered_low)}</td><td>${Math.round(d.delivered_median)}</td><td>${Math.round(d.delivered_high)}</td><td>${Math.round(d.on_scored_towns_median)}</td></tr>`).join("");
document.getElementById("tab").innerHTML="<tr><th>Cell (S, W corner)</th><th>median</th><th>5th</th><th>95th</th></tr>"+s.cells.map(q=>`<tr><td>${q[0]}, ${q[1]}</td><td>${q[2]}</td><td>${q[3]}</td><td>${q[4]}</td></tr>`).join("")}
map.addEventListener("mousemove",e=>{const s=D.scenarios[sel.value],v=view,b=map.getBoundingClientRect(),f=map.width/b.width,x=(e.clientX-b.left)*f,y=(e.clientY-b.top)*f,lon=x/(v.k*v.sc)+v.c,lat=(map.height-y)/v.sc+v.a;
const q=s.cells.find(c=>lat>=c[0]&&lat<c[0]+s.deg&&lon>=c[1]&&lon<c[1]+s.deg);if(!q){tip.style.display="none";return}
tip.textContent=`P about ${q[2]} (${q[3]} to ${q[4]})`+(q[5]?" (cell holds a sealed town)":"");tip.style.display="block";tip.style.left=e.clientX+14+"px";tip.style.top=e.clientY+14+"px"});
map.addEventListener("mouseleave",()=>tip.style.display="none");sel.onchange=draw;band.onchange=draw;draw();
</script></body></html>
"""


def render() -> str:
    data = json.dumps(payload(), separators=(",", ":")).replace("</", "<\\/")
    return PAGE.replace("__DATA__", data)


def main() -> None:
    path = OUT / "viewer" / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
