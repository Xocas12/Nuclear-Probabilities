"""The atlas: one self-contained HTML page with every dataset on a world map (milestone M9).

    python -m nucprob.viz.atlas [--datasets a,b] [--out docs/atlas/index.html]

For each dataset it shows every place:
- coloured by its out-of-fold probability under spatial cross-validation (LightGBM, the
  sealed test left out);
- with its own list's targets outlined.

A side panel holds the dataset's leaderboard from the playground (population rule, logit,
LightGBM) and, if runs/m7-levels/ exists, the transfer matrix. The page loads deck.gl and
MapLibre from a CDN and carries its data inline, so it can be served from GitHub Pages
(docs/). The base map has no borders, so no anachronistic ones.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.model.evaluate import metrics
from nucprob.paths import ROOT, RUNS
from nucprob.playground.algos import algorithms
from nucprob.playground.datasets import load, transfer_lists
from nucprob.playground.evaluate import fold_ids

DEFAULT = ["sac1956", "napb90:very_high", "pooled"]
OUT = ROOT / "docs" / "atlas" / "index.html"
ALGOS = ["logit", "lgbm"]


def oof(d, algo: str) -> np.ndarray:
    ids = fold_ids(d)
    p = np.full(len(d.frame), np.nan)
    for f in np.unique(ids):
        t = ids == f
        if d.y[~t].nunique() < 2:
            continue
        m = algorithms(algo)[algo].factory().fit(d.X[~t], d.y[~t])
        p[t] = m.predict_proba(d.X[t])[:, 1]
    return p


def dataset_payload(name: str) -> dict:
    d = load(name)
    preds = {a: oof(d, a) for a in ALGOS}
    pop = next((c for c in ("log_pop", "log_pop_1959") if c in d.frame), None)
    board = []
    y = d.y.to_numpy()
    for a, p in [
        *preds.items(),
        ("population rank", d.frame[pop].rank(pct=True).to_numpy() if pop else None),
    ]:
        if p is None:
            continue
        ok = ~np.isnan(p)
        m = metrics(y[ok], p[ok]) or {}
        board.append(
            {
                "model": a,
                "pr_auc": round(m.get("pr_auc", np.nan), 3),
                "roc_auc": round(m.get("roc_auc", np.nan), 3),
            }
        )
    f = d.frame
    pts = [
        [
            round(lo, 3),
            round(la, 3),
            int(t),
            None if np.isnan(p) else round(float(p), 3),
            str(n)[:40],
            str(c)[:20],
        ]
        for lo, la, t, p, n, c in zip(
            f["lon"], f["lat"], y, preds["lgbm"], f["name"], f["country"], strict=True
        )
    ]
    return {
        "name": name,
        "summary": d.summary(),
        "note": d.note,
        "board": board,
        "points": pts,
    }


def transfer_matrix() -> dict | None:
    path = RUNS / "m7-levels" / "transfer_matrix.csv"
    if not path.exists():
        return None
    m = pd.read_csv(path, index_col=0)
    return {
        "rows": m.index.tolist(),
        "cols": m.columns.tolist(),
        "values": m.round(2).where(m.notna(), None).values.tolist(),
    }


def build(names: list[str], out: Path) -> Path:
    data = []
    for n in names:
        try:
            data.append(dataset_payload(n))
            print(f"{n}: {len(data[-1]['points'])} places")
        except (FileNotFoundError, KeyError) as err:
            print(f"{n}: skipped ({err})")
    html = TEMPLATE.replace(
        "__DATA__", json.dumps({"datasets": data, "transfer": transfer_matrix()})
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nuclear targeting atlas</title>
<script src="https://unpkg.com/deck.gl@9.0.38/dist.min.js"></script>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<style>
:root{--bg:#f7f6f2;--fg:#1d1d1b;--panel:#ffffffee;--muted:#6b6b66;--line:#ddd}
@media (prefers-color-scheme: dark){:root{--bg:#121212;--fg:#ececec;--panel:#1e1e1ef0;--muted:#a0a0a0;--line:#333}}
html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif}
#map{position:absolute;inset:0}
#panel{position:absolute;top:12px;left:12px;width:min(360px,calc(100% - 24px));max-height:calc(100% - 24px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;box-sizing:border-box}
h1{font-size:16px;margin:0 0 6px} select{width:100%;padding:6px;margin:6px 0;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:12px;margin:6px 0} td,th{padding:2px 4px;border-bottom:1px solid var(--line);text-align:right} td:first-child,th:first-child{text-align:left}
.muted{color:var(--muted);font-size:12px} .legend{height:10px;border-radius:5px;background:linear-gradient(90deg,#2c7bb6,#ffffbf,#d7191c);margin:4px 0}
#tip{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:12px;display:none}
</style></head><body>
<div id="map"></div>
<div id="panel"><h1>Nuclear targeting atlas</h1>
<div class="muted">Out-of-fold probability that a place is targeted (LightGBM, 300 km spatial blocks). Ringed places are on the list.</div>
<select id="ds"></select><div id="summary" class="muted"></div><div id="note" class="muted"></div>
<div class="legend"></div><div class="muted" style="display:flex;justify-content:space-between"><span>0</span><span>probability</span><span>1</span></div>
<table id="board"></table><div id="tm"></div></div>
<div id="tip"></div>
<script>
const DATA = __DATA__;
const ramp = p => { if (p == null) return [150,150,150,120];
  const a=[44,123,182], b=[255,255,191], c=[215,25,28];
  const [u,v,t] = p<0.5 ? [a,b,p*2] : [b,c,(p-0.5)*2];
  return [0,1,2].map(i=>Math.round(u[i]+(v[i]-u[i])*t)).concat([210]); };
const sel = document.getElementById('ds');
DATA.datasets.forEach((d,i)=>{ const o=document.createElement('option'); o.value=i; o.textContent=d.name; sel.appendChild(o); });
const deckgl = new deck.DeckGL({container:'map', mapStyle:'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json',
  initialViewState:{longitude:60,latitude:45,zoom:2.2}, controller:true,
  getTooltip: null});
const tip = document.getElementById('tip');
function show(i){ const d = DATA.datasets[i];
  document.getElementById('summary').textContent = d.summary;
  document.getElementById('note').textContent = d.note ? ('Note: ' + d.note) : '';
  document.getElementById('board').innerHTML = '<tr><th>model</th><th>PR-AUC</th><th>ROC-AUC</th></tr>' +
    d.board.map(r=>`<tr><td>${r.model}</td><td>${r.pr_auc}</td><td>${r.roc_auc}</td></tr>`).join('');
  const lons = d.points.map(p=>p[0]), lats = d.points.map(p=>p[1]);
  const lon = lons.reduce((a,b)=>a+b,0)/lons.length, lat = lats.reduce((a,b)=>a+b,0)/lats.length;
  deckgl.setProps({initialViewState:{longitude:lon, latitude:lat, zoom:3, transitionDuration:600},
    layers:[new deck.ScatterplotLayer({id:'pts'+i, data:d.points, getPosition:p=>[p[0],p[1]],
      getFillColor:p=>ramp(p[3]), getLineColor:[0,0,0,230], stroked:true, getLineWidth:p=>p[2]?1.5:0,
      lineWidthUnits:'pixels', radiusUnits:'pixels', getRadius:p=>p[2]?5:3, pickable:true,
      onHover:({object,x,y})=>{ if(!object){tip.style.display='none';return;}
        tip.style.display='block'; tip.style.left=(x+12)+'px'; tip.style.top=(y+12)+'px';
        tip.innerHTML=`<b>${object[4]}</b> (${object[5]})<br>listed: ${object[2]?'yes':'no'}<br>P(target): ${object[3]==null?'n/a':object[3]}`; }})]}); }
sel.onchange = e => show(+e.target.value);
if (DATA.datasets.length) show(0);
if (DATA.transfer){ const t=DATA.transfer;
  document.getElementById('tm').innerHTML = '<div class="muted" style="margin-top:8px">Transfer matrix (ROC-AUC): fitted on the row country, scored on the column.</div><table>' +
   '<tr><th></th>'+t.cols.map(c=>`<th>${c.slice(0,6)}</th>`).join('')+'</tr>' +
   t.rows.map((r,i)=>'<tr><td>'+r+'</td>'+t.values[i].map(v=>{ if(v==null) return '<td></td>';
     const c=ramp(v); return `<td style="background:rgba(${c[0]},${c[1]},${c[2]},.6)">${v}</td>`;}).join('')+'</tr>').join('') + '</table>'; }
</script></body></html>
"""


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m nucprob.viz.atlas")
    p.add_argument("--datasets", default=",".join(DEFAULT))
    p.add_argument("--transfer", action="store_true", help="add every transfer list")
    p.add_argument("--out", default=str(OUT))
    a = p.parse_args(argv)
    names = a.datasets.split(",") + (
        [f"transfer:{t}" for t in transfer_lists()] if a.transfer else []
    )
    build(names, Path(a.out))


if __name__ == "__main__":
    main()
