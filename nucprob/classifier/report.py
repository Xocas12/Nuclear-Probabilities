"""Tables of the classifier report, from the committed outputs of runs/classifier/.

    python -m nucprob.classifier.report

Writes runs/classifier/TABLES.md, REPORT.md at the repository root and the results block of README.md.
Results come from CSVs here; the sealed-set sizes and the SAC audit's figures in the text are from the
cards it names. tests/test_classifier_report.py fails if any of the three differs from a regeneration.
"""

import functools
import json
import re
import textwrap

import numpy as np
import pandas as pd

from nucprob.classifier.divergence import LOSS_RISE, MAX_RAW
from nucprob.classifier.evaluate import MIN_TRAIN_POSITIVES
from nucprob.classifier.identification_fit import DIVERGED_DROP
from nucprob.paths import CURATED, ROOT, RUNS
from nucprob.plans import protocol
from nucprob.probmap.counts import count
from nucprob.probmap.run import N_DRAWS, load_scenarios
from nucprob.probmap.viewer import shift_label

OUT = RUNS / "classifier"
MAP = RUNS / "probmap"
SAC = "us_1956_sac_complexes"
ORDER = [
    "population rule",
    "population + country",
    "logistic, all permitted",
    "LightGBM, all permitted",
]


def markdown(d: pd.DataFrame) -> str:
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    rule = "|" + "---|" * len(d.columns)
    body = ["| " + " | ".join(_cell(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join([head, rule, *body])


def _cell(v) -> str:
    if isinstance(v, float):
        if pd.isna(v):
            return ""
        if v != 0 and round(v, 2) == 0:
            # A nonzero value never prints as 0.00, which the report reserves for an exact zero.
            three = f"{v:.3f}"
            return three if float(three) != 0 else f"{v:.0e}"
        return f"{v:.2f}"
    return str(v)


DIFF_DIGITS = 3


def signed(v: float) -> str:
    """A difference or a bound: three decimals, with its sign. A value within 0.0005 of zero prints as +0.000
    or -0.000, the sign giving its side of zero, which decides a verdict; an exact zero prints as 0.000."""
    if v == 0 and not np.signbit(v):
        return "0.000"
    return f"{v:+.{DIFF_DIGITS}f}"


def point(v: float, *bounds: float) -> str:
    """An estimate of a difference, printed as its bounds are (signed); the bounds are ignored."""
    return signed(v)


def estimate_interval(v: float, low: float, high: float) -> tuple[str, str, str]:
    """The estimate and its bounds as printed. Where the estimate would print equal to a bound it differs from,
    all three take a fourth decimal."""
    est, lo, hi = signed(v), signed(low), signed(high)
    if (est == lo and v != low) or (est == hi and v != high):
        est, lo, hi = (
            "0.0000" if x == 0 and not np.signbit(x) else f"{x:+.4f}" for x in (v, low, high)
        )
    return est, lo, hi


def constant(r) -> bool:
    """A comparison whose two scores never differ on these rows: a family constant within them."""
    return all(r.get(c) == 0 for c in ("delta", "low", "high", "block_low", "block_high"))


def interval(r) -> str:
    if constant(r):
        return "none: constant on these rows"
    est, lo, hi = estimate_interval(r["delta"], r["low"], r["high"])
    return f"{est} [{lo}, {hi}]"


# Fewer blocks than this holding the positives, and resampling blocks cannot measure anything: with 7
# positives in 2 blocks the interval collapsed onto its point. Set after that row had been read (configs/HISTORY.md).
MIN_POSITIVE_BLOCKS = 5


@functools.cache
def _positive_blocks() -> dict[tuple[str, str, str], int]:
    """Distinct 300 km blocks holding the positives of each scope, holdout and set of lists."""
    path = OUT / "held_out_scores.csv.gz"
    if not path.exists():
        return {}
    h = pd.read_csv(path, usecols=["scope", "holdout", "plan_id", "listed", "block"])
    h = h[h["listed"] == 1]
    out = {}
    for (scope, holdout), g in h.groupby(["scope", "holdout"]):
        out[(scope, holdout, "all lists")] = g["block"].nunique()
        out[(scope, holdout, "lists other than SAC")] = g.loc[
            g["plan_id"] != SAC, "block"
        ].nunique()
    return out


@functools.cache
def _scored_in_sealed_blocks() -> tuple[int, int]:
    """Places scored in any committed holdout that lie in a sealed block: (all, SAC 1956 only)."""
    path = OUT / "held_out_scores.csv.gz"
    blocks = ROOT / "data" / "curated" / "splits" / "sealed_blocks.csv"
    if not path.exists() or not blocks.exists():
        return 0, 0
    sealed = set(pd.read_csv(blocks)["block"])
    h = pd.read_csv(path, usecols=["plan_id", "place_id", "block"])
    h = h[h["block"].isin(sealed)]
    return h["place_id"].nunique(), h.loc[h["plan_id"] == SAC, "place_id"].nunique()


def _sealed_block_sentence() -> str:
    total, sac = _scored_in_sealed_blocks()
    if not total:
        return "A sealed block holds no training place, but a training town in a neighbouring block may be close."
    return (
        f"A sealed block is not free of training data: {total} scored places lie in sealed blocks, {sac} of them SAC 1956 "
        "towns the early check had scored before corrected coordinates moved them there (`data/curated/splits/README.md`) "
        f"and {total - sac} towns of other lists. A training town in a neighbouring block may also be close."
    )


def positive_blocks(r) -> int | None:
    keys = ("scope", "holdout", "lists")
    if not all(k in r for k in keys):
        return None
    return _positive_blocks().get(tuple(r[k] for k in keys))


def block_interval(r) -> str:
    if pd.isna(r["block_low"]):
        return "n/a"
    if constant(r):
        return "none"
    k = positive_blocks(r)
    if k is not None and k < MIN_POSITIVE_BLOCKS:
        return f"n/a: positives in {k} blocks"
    return f"[{signed(r['block_low'])}, {signed(r['block_high'])}]"


def block_measured(r) -> bool:
    k = positive_blocks(r)
    return not pd.isna(r["block_low"]) and (k is None or k >= MIN_POSITIVE_BLOCKS)


def claim(r) -> str:
    """Whether the protocol's rule lets a difference be called a gain: both bounds, unrounded."""
    if not block_measured(r):
        return "the block interval is not a measurement here, so it cannot be called a difference"
    if r["low"] > 0 and r["block_low"] > 0:
        return "both intervals exclude zero"
    if r["high"] < 0 and r["block_high"] < 0:
        return "both intervals exclude zero, as a loss"
    return "at least one interval reaches zero, so it cannot be told from no difference"


def verdict(r) -> str:
    """The protocol's fourth amendment, from the unrounded bounds."""
    if r["train_positives_min"] < MIN_TRAIN_POSITIVES or bool(r["constant_score"]):
        return "not a reading"
    if not block_measured(r):
        return "neither"  # a gain or a loss needs both intervals
    if r["low"] > 0 and r["block_low"] > 0:
        return "gain"
    if r["high"] < 0 and r["block_high"] < 0:
        return "loss"
    return "neither"


def both_verdict(r) -> str:
    """Gain, loss or neither by the protocol's rule (both intervals, unrounded), for rows with no training count."""
    if constant(r):
        return "constant"
    if not block_measured(r):
        return "neither"
    if r["low"] > 0 and r["block_low"] > 0:
        return "gain"
    if r["high"] < 0 and r["block_high"] < 0:
        return "loss"
    return "neither"


def verdict_grid(d: pd.DataFrame, index: str, columns: str) -> pd.DataFrame:
    """One cell per row of `d`: its estimate and verdict. The intervals behind each cell are in TABLES.md."""
    cells = d.assign(
        cell=d.apply(
            lambda r: (
                "constant"
                if constant(r)
                else f"{point(r['delta'], r['low'], r['high'])} {both_verdict(r)}"
            ),
            axis=1,
        )
    )
    order = list(dict.fromkeys(d[columns]))
    grid = cells.pivot(index=index, columns=columns, values="cell")[order]
    grid = grid.reindex(list(dict.fromkeys(d[index])))
    return grid.reset_index().rename_axis(columns=None)


def by_list(lists: pd.DataFrame, scope: str, holdout: str) -> pd.DataFrame:
    """PR-AUC of every list the scope holds and model. A list too small to score shows blanks."""
    g = lists[(lists["scope"] == scope) & lists["holdout"].str.startswith(holdout)]
    if g.empty:
        return g
    p = g.pivot_table(
        index=["plan_id", "doc_type", "complete", "towns", "positives"],
        columns="model",
        values="pr_auc",
        dropna=False,
        observed=True,
        sort=False,
    )
    # pivot_table's dropna=False forms every combination of the index: keep those that occurred.
    seen = g[["plan_id", "doc_type", "complete", "towns", "positives"]].drop_duplicates()
    p = p.reset_index().merge(seen, on=list(seen.columns))
    return p.reindex(columns=[*seen.columns, *ORDER]).sort_values("positives", ascending=False)


def other_metrics(lists: pd.DataFrame) -> pd.DataFrame:
    """The protocol's secondary metrics: positive-weighted mean over scored lists, per holdout."""
    d = lists[lists["pr_auc"].notna()].copy()
    d["holdout"] = d["holdout"].str.replace(r" \(.*\)$", "", regex=True)
    rows = []
    for key, g in d.groupby(["scope", "holdout", "model"], sort=False):
        w = g["positives"]
        row = dict(zip(["scope", "holdout", "model"], key, strict=True)) | {
            "positives": int(w.sum())
        }
        for c in ("pr_auc", "roc_auc", "brier", "log_loss", "precision_at_k", "base_rate"):
            row[c] = float((g[c] * w).sum() / w.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def comparison(c: pd.DataFrame, scope: str) -> pd.DataFrame:
    g = c[c["scope"] == scope].copy()
    # Where no SAC row is held out, "lists other than SAC" repeats "all lists".
    same = g.duplicated(["holdout", "model", "against", "positives", "delta"], keep="first")
    g = g[~same]
    g["candidate minus baseline"] = g.apply(interval, axis=1)
    g["block interval"] = g.apply(block_interval, axis=1)
    g["verdict"] = g.apply(verdict, axis=1)
    keep = ["holdout", "lists", "model", "against", "positives", "train_positives_min"]
    keep += ["base_rate", "a_pr_auc", "b_pr_auc"]
    return g[[*keep, "candidate minus baseline", "block interval", "verdict"]]


def _metrics_note(lists: pd.DataFrame) -> str:
    """Why these totals can hold fewer positives than comparison.csv: lists with positives but no per-list score."""
    if _unscored_note(lists) == "no list":
        return "Every list with a positive is scored."
    return (
        f"Lists too small to score ({_unscored_note(lists)} positive) are left out of these weighted totals, so a row "
        "here counts up to that many positives fewer than the same scope and holdout in `comparison.csv`, which scores "
        "all lists pooled."
    )


def tables() -> str:
    lists = pd.read_csv(OUT / "lists.csv")
    comp = pd.read_csv(OUT / "comparison.csv")
    parts = ["# Classifier tables", "", "Generated by `python -m nucprob.classifier.report`.", ""]
    parts += ["## Scopes", "", markdown(pd.read_csv(OUT / "scopes.csv")), ""]
    parts += ["## The gate for a state's own model", ""]
    parts += [markdown(pd.read_csv(OUT / "state_gate.csv")), ""]
    parts += ["## Model selection under spatial blocks", ""]
    parts += [markdown(pd.read_csv(OUT / "selection.csv")), ""]
    parts += ["## All metrics, positive-weighted over scored lists", ""]
    parts += [_metrics_note(lists), ""]
    parts += [markdown(other_metrics(lists)), ""]
    for scope in lists["scope"].unique():
        parts += [f"## {scope}", "", "### Candidates against baselines", ""]
        parts += [markdown(comparison(comp, scope)), ""]
        for holdout, heading in (
            ("spatial blocks", "spatial blocks"),
            ("leave-one-document-out", "leave one document out"),
            ("towns kept", "leave one document out, its towns kept in training"),
            ("temporal: fit up", "fit up to 1956, score later"),
            ("temporal reversed", "fit after 1956, score earlier"),
            ("expectation lists", "expectation lists, not plans"),
        ):
            t = by_list(lists, scope, holdout)
            if len(t):
                parts += [f"### PR-AUC by list: {heading}", "", markdown(t), ""]
    cal = pd.read_csv(OUT / "calibration.csv")
    summary = cal.groupby(["model", "kind"], as_index=False)[
        ["brier", "expected_calibration_error"]
    ].first()
    parts += ["## Calibration, US 1956 complexes under spatial blocks", ""]
    parts += [markdown(summary), ""]
    fam = pd.read_csv(OUT / "family_gain.csv")
    fam["verdict"] = fam.apply(lambda r: "constant" if constant(r) else r["verdict"], axis=1)
    fam["gain"] = fam.apply(interval, axis=1)
    fam["by_blocks"] = fam.apply(block_interval, axis=1)
    keep = [
        "rows",
        "family",
        "base",
        "base_pr_auc",
        "with_family_pr_auc",
        "gain",
        "by_blocks",
        "verdict",
    ]
    parts += ["## Feature families, US 1956 complexes", "", markdown(fam[keep]), ""]
    sens = pd.read_csv(OUT / "sensitivity.csv")
    sens = sens.assign(
        difference=sens.apply(interval, axis=1), by_blocks=sens.apply(block_interval, axis=1)
    )[["scope", "model", "variant", "features", "a_pr_auc", "b_pr_auc", "difference", "by_blocks"]]
    parts += ["## What the gains rest on, every row", ""]
    parts += [
        "Each scope's selected candidate (a) against population plus country (b) under spatial blocks, "
        "with columns removed (`runs/classifier/sensitivity.csv`).",
        "",
        markdown(sens),
        "",
    ]
    parts += ["## Defences, associations only", "", markdown(pd.read_csv(OUT / "defence.csv")), ""]
    extended = _extended_rows()
    if extended is not None:
        parts += ["## Economic and political data, every row", ""]
        parts += [markdown(extended[EXTENDED_COLUMNS]), ""]
    if (MAP / "by_delivery.csv").exists():
        shift = pd.read_csv(MAP / "domain_shift.csv")
        shift["feature"] = shift["comparison"].str.split(": ").str[-1]
        two = shift[shift["measure"] == "two-sample ROC-AUC"].iloc[0]
        parts += ["## Probability map: warheads available and delivered, by state and delivery", ""]
        parts += ["Median with the 5th to 95th percentile (`runs/probmap/by_delivery.csv`).", ""]
        parts += [markdown(_by_delivery_table(pd.read_csv(MAP / "by_delivery.csv"))), ""]
        parts += ["## Probability map: domain shift, feature by feature", ""]
        parts += [
            f"On {int(two['towns_a']):,} training and {int(two['towns_b']):,} modern towns "
            "(`runs/probmap/domain_shift.csv`).",
            "",
            markdown(_shift_table(shift)),
            "",
        ]
    return "\n".join(parts)


SCOPES = {
    "global, all attacker documents": "Global, all attacker documents (exercises included)",
    "global, plan documents only": "Global, plan documents only",
    "Warsaw Pact, pooled, exercise-based": "Warsaw Pact, pooled (exercise-based, not a war-plan model)",
    "single document: SAC 1956 (not a state model)": "SAC 1956 alone (one document, not a state model)",
}
HOLDOUTS = {
    "spatial blocks": "Spatial blocks",
    "leave one document out": "Leave one document out",
    "temporal: fit up to 1956, score later": "Fit to 1956, score later",
    "temporal reversed: fit after 1956, score earlier": "Fit after 1956, score earlier",
}
RULE = "population rule"
PLUS = "population + country"
WORDS = {
    "gain": "gain",
    "loss": "lose",
    "neither": "cannot be told apart",
    "not a reading": "are not readings",
}


def primary_table(comp: pd.DataFrame, selection: pd.DataFrame) -> pd.DataFrame:
    """The protocol's primary comparison: each scope's selected candidate against population +
    country, and against the population rule, on all lists and without SAC."""
    best = selection[selection["selected"]].set_index("scope")["model"]
    rows = []
    for scope, label in SCOPES.items():
        if scope not in best:
            continue
        g = comp[(comp["scope"] == scope) & (comp["model"] == best[scope])]
        g = g[~g.duplicated(["holdout", "against", "positives", "delta"])]
        for holdout, name in HOLDOUTS.items():
            for lists in ("all lists", "lists other than SAC"):
                part = g[(g["holdout"] == holdout) & (g["lists"] == lists)]
                if part.empty:
                    continue
                plus = part[part["against"] == PLUS].iloc[0]
                rule = part[part["against"] == RULE].iloc[0]
                rows.append(
                    {
                        "Scope": label,
                        "Selected": best[scope],
                        "Holdout": name,
                        "Lists": lists,
                        "Positives": int(plus["positives"]),
                        "Trained on": int(plus["train_positives_min"]),
                        "Base rate": float(plus["base_rate"]),
                        "Model": float(plus["a_pr_auc"]),
                        "Pop. + country": float(plus["b_pr_auc"]),
                        "Difference, country": interval(plus),
                        "By blocks": block_interval(plus),
                        "Verdict": verdict(plus),
                        "Pop. rule": float(rule["b_pr_auc"]),
                        "Difference, rule": interval(rule),
                    }
                )
    return pd.DataFrame(rows)


SEED_SUMMARY = OUT / "seed_check_summary.csv"
# A verdict whose deciding bound lies this close to zero is flagged where no other seed was tried.
NEAR_ZERO = 0.005
SEED_KEY = ["scope", "holdout", "lists", "against"]
SEED_VERDICTS = ("gain", "neither", "loss", "not a reading")


def seed_summary() -> pd.DataFrame | None:
    """The eighteenth amendment's check, if it has been run on these outputs."""
    if not SEED_SUMMARY.exists():
        return None
    return pd.read_csv(SEED_SUMMARY)


def seed_distinct(s: pd.DataFrame) -> pd.DataFrame:
    """The check's comparisons counted once: where no SAC row is held out, a "lists other than SAC" row repeats its
    "all lists" row (as in `comparison`), and is dropped here as it is from the primary table."""
    key = [
        "scope",
        "holdout",
        "against",
        "verdict_seed_1956",
        "seeds_gain",
        "seeds_loss",
        "seeds_neither",
    ]
    same = s.duplicated(
        [*key, "min_low", "max_high", "min_block_low", "max_block_high"], keep="first"
    )
    return s[~same]


def seed_counts(s) -> str:
    """How many of the 20 other seeds give each verdict, largest first, e.g. "11 gain, 9 neither"."""
    counts = {v: int(s[f"seeds_{v.replace(' ', '_')}"]) for v in SEED_VERDICTS}
    return ", ".join(f"{n} {v}" for v, n in sorted(counts.items(), key=lambda kv: -kv[1]) if n)


def seed_of(r) -> pd.Series | None:
    s = seed_summary()
    if s is None:
        return None
    hit = s[np.logical_and.reduce([s[k] == r[k] for k in SEED_KEY])]
    return hit.iloc[0] if len(hit) else None


def seed_note(r) -> str:
    """For README and REPORT prose: empty for a seed-stable verdict, else what the other seeds give."""
    s = seed_of(r)
    if s is None or bool(s["seed_stable"]):
        return ""
    return (
        f" That verdict depends on the bootstrap seed: under 20 other seeds, {seed_counts(s)} "
        "(`configs/protocol_amendment_18.yaml`)."
    )


def with_seeds(primary: pd.DataFrame) -> pd.DataFrame:
    """The primary table with, beside its verdict, the verdicts of seeds 1-20 against population + country."""
    s = seed_summary()
    if s is None:
        return primary
    scope = {v: k for k, v in SCOPES.items()}
    holdout = {v: k for k, v in HOLDOUTS.items()}
    s = s[s["against"] == PLUS].set_index(["scope", "holdout", "lists"])
    cells = []
    for r in primary.itertuples():
        key = (scope[r.Scope], holdout[r.Holdout], r.Lists)
        cells.append(seed_counts(s.loc[key]) if key in s.index else "not run")
    out = primary.copy()
    out.insert(out.columns.get_loc("Verdict") + 1, "Seeds 1-20", cells)
    return out


def seed_section() -> str:
    """REPORT's account of the eighteenth amendment's check."""
    s = seed_summary()
    if s is None:
        return (
            "**Bootstrap seed.** The repeat of these comparisons under other seeds "
            "(`configs/protocol_amendment_18.yaml`) has not been run on these outputs."
        )
    rows = len(s)
    s = seed_distinct(s)
    moved = s[~s["seed_stable"].astype(bool)]
    stable = len(s) - len(moved)
    table = pd.DataFrame(
        {
            "Scope": [SCOPES[r.scope] for r in moved.itertuples()],
            "Holdout": [HOLDOUTS[r.holdout] for r in moved.itertuples()],
            "Lists": moved["lists"].tolist(),
            "Against": moved["against"].tolist(),
            "Seed 1956": moved["verdict_seed_1956"].tolist(),
            "Seeds 1-20": [seed_counts(r._asdict()) for r in moved.itertuples()],
        }
    )
    moved_text = (
        f" These {len(moved)} are seed-dependent:\n\n{markdown(table)}\n\n"
        if len(moved)
        else " None is seed-dependent. "
    )
    return f"""**Bootstrap seed.** The protocol fixes one seed for its 2,000 resamples: the number 1956, not the document
year. After the results had been read, one verdict of this table was found to turn on that seed, and
`configs/protocol_amendment_18.yaml` then fixed a repeat of every comparison of this table, against both baselines,
under seeds 1 to 20 with nothing refitted (`runs/classifier/seed_check_summary.csv`, one row per comparison;
`seed_check.csv`, one per seed). That file has {rows} rows; where no SAC row is held out a "lists other than SAC" row
repeats its "all lists" row, and is counted once here, as in the primary table. Of {len(s)} comparisons, {stable} give the seed-1956 verdict under all 20 seeds.{moved_text}The protocol's verdict stays seed 1956's. A
seed-dependent verdict is read as neither a finding nor its absence: a gain that some seeds do not give is a gain
only under the committed draws, and a "neither" that most seeds call a gain is not a gain by the protocol. The feature-family comparisons and the sealed readings rest on seed 1956 alone: the
family fits' scores are not kept, and the sealed set's lock allows one reading. So a verdict there whose bound lies
within {NEAR_ZERO} of zero may not survive another seed."""


def verdicts(table: pd.DataFrame) -> dict[str, int]:
    return table["Verdict"].value_counts().to_dict()


def _row(comp, scope, holdout, model, against, which="all lists"):
    return comp[
        (comp["scope"] == scope)
        & (comp["holdout"] == holdout)
        & (comp["model"] == model)
        & (comp["against"] == against)
        & (comp["lists"] == which)
    ].iloc[0]


# Counts of the sealed set fixed when it was drawn (data/curated/splits/README.md). They are not in a committed
# output, so a test checks them against the built table and scored_before_freeze.csv.
SEALED_PLACES = 467
EARLY_SCORED = 194
AMENDMENT_11_SET = SEALED_PLACES - EARLY_SCORED

SAC_SCOPE = "single document: SAC 1956 (not a state model)"
GLOBAL_ALL = "global, all attacker documents"


def _best(selection: pd.DataFrame, scope: str) -> str:
    b = selection[selection["selected"]].set_index("scope")["model"]
    return b[scope]


def _population_note(model: str) -> str:
    if model != "population rule":
        return ""
    return (
        "\nThe population rule won, so **the map's shares are read from town population and nothing else**. What a town "
        "produced, housed or defended plays no part. The selection rule chose it by PR-AUC, which depends only on the order of towns: on a "
        "left-out document nothing richer has been shown to order them better. The shares use the logistic's fitted values, "
        "and how far those values move with population was not tested by that choice.\n"
    )


def _theatre_table() -> pd.DataFrame:
    """Every theatre share as configs/scenarios.yaml states it, one row per scenario and range. None
    has a source."""
    rows = []
    for sc in load_scenarios():
        for a in sc["attackers"]:
            low, mode, high = a["theatre_share"]
            rows.append({"scenario": sc["id"], "attacker": a["state"], "range": (low, mode, high)})
    t = pd.DataFrame(rows)
    t = t.groupby(["scenario", "range"], sort=False, as_index=False)["attacker"].agg(", ".join)
    return pd.DataFrame(
        {
            "scenario": t["scenario"],
            "attackers": t["attacker"],
            "low": [r[0] for r in t["range"]],
            "mode": [r[1] for r in t["range"]],
            "high": [r[2] for r in t["range"]],
        }
    )


def _median_range(d: pd.DataFrame, prefix: str) -> pd.Series:
    """'median [low, high]' from the columns <prefix>_median, _low and _high, as counts (count())."""
    return d.apply(
        lambda r: (
            f"{count(r[prefix + '_median'])} [{count(r[prefix + '_low'])}, {count(r[prefix + '_high'])}]"
        ),
        axis=1,
    )


def _delivered_table(d: pd.DataFrame) -> pd.DataFrame:
    """runs/probmap/delivered.csv with each interval in one column. Warheads on scored towns differ
    from those delivered only where the sealed set holds people, so elsewhere the column says so."""
    return pd.DataFrame(
        {
            "scenario": d["scenario"],
            "attacker": d["attacker"],
            "delivered": _median_range(d, "delivered"),
            "on_scored_towns": np.where(
                d["share_of_people_in_scored_towns"] < 1,
                _median_range(d, "on_scored_towns"),
                "all",
            ),
            "delivered_shares_at_mode": d.apply(
                lambda r: (
                    f"[{count(r['delivered_low_share_fixed'])}, {count(r['delivered_high_share_fixed'])}]"
                ),
                axis=1,
            ),
        }
    )


def _by_delivery_table(b: pd.DataFrame) -> pd.DataFrame:
    """runs/probmap/by_delivery.csv with each interval in one column."""
    return pd.DataFrame(
        {
            "scenario": b["scenario"],
            "attacker": b["attacker"],
            "stock_year": b["stock_year"],
            "delivery": b["delivery"],
            "available": _median_range(b, "available"),
            "delivered": _median_range(b, "delivered"),
        }
    )


SHIFT_COLUMNS = {
    "share of modern towns": "modern_towns_outside_training_1_99",
    "one-feature ROC-AUC, folded": "roc_auc_this_feature_alone",
    "two-sample ROC-AUC, one feature left out": "roc_auc_without_this_feature",
}


def _shift_table(shift: pd.DataFrame) -> pd.DataFrame:
    """runs/probmap/domain_shift.csv's per-feature rows, one row per feature."""
    per = shift[shift["measure"].isin(SHIFT_COLUMNS)]
    t = per.pivot(index="feature", columns="measure", values="value")
    t = t.reindex(per["feature"].drop_duplicates())[list(SHIFT_COLUMNS)]
    return t.rename(columns=SHIFT_COLUMNS).rename_axis(None, axis=1).reset_index()


def _map_section() -> str:
    if not (MAP / "scenarios.csv").exists():
        return "The probability map has not been run.\n"
    s = pd.read_csv(MAP / "scenarios.csv")
    d = pd.read_csv(MAP / "delivered.csv")
    choice = pd.read_csv(MAP / "model_choice.csv")
    val = pd.read_csv(MAP / "validation.csv")
    rel = pd.read_csv(MAP / "reliability.csv")
    shift = pd.read_csv(MAP / "domain_shift.csv")
    best = choice[choice["selected"]].iloc[0]
    two = shift[shift["measure"] == "two-sample ROC-AUC"]
    shift["feature"] = shift["comparison"].str.split(": ").str[-1]
    outside = shift[shift["measure"] == "share of modern towns"]
    worst = outside.sort_values("value", ascending=False).iloc[0]
    alone = shift[shift["measure"] == "one-feature ROC-AUC, folded"].sort_values("value")
    dropped = shift[shift["measure"] == "two-sample ROC-AUC, one feature left out"]
    dropped = dropped.sort_values("value")
    pop_alone = float(alone.loc[alone["feature"] == "log_pop", "value"].iloc[0])
    variance = pd.read_csv(MAP / "share_variance.csv")
    universe = pd.read_csv(MAP / "modern_universe.csv").set_index("step")["places"]
    by_id = {sc["id"]: sc for sc in load_scenarios()}
    scen = s.assign(
        viewer_label=s["scenario"].map(lambda i: shift_label(by_id[i])),
        cells_over_half=s.apply(
            lambda r: (
                f"{count(r['cells_over_half_median'])} "
                f"[{count(r['cells_over_half_low'])}, {count(r['cells_over_half_high'])}]"
            ),
            axis=1,
        ),
    )[
        [
            "scenario",
            "era",
            "viewer_label",
            "cell_deg",
            "towns",
            "cells",
            "cells_over_half",
            "mean_width_model_only",
            "mean_width_stockpile_only",
            "mean_interval_width",
        ]
    ]
    spatial = val[val["reading"].str.startswith("spatial")].iloc[0]
    left = val[val["reading"].str.startswith("SAC")].iloc[0]
    spread = pd.read_csv(MAP / "score_spread.csv")
    first = spread[spread["scenario"] == "us_1956_on_bloc"].iloc[0]
    bloc_width = s.loc[s["scenario"] == "us_1956_on_bloc", "mean_interval_width"].iloc[0]
    west = s[s["scenario"] == "ussr_1965_on_west"].iloc[0]
    west_d = d[d["scenario"] == "ussr_1965_on_west"].iloc[0]
    bloc_d = d[d["scenario"] == "us_1956_on_bloc"].iloc[0]
    towns_more = spread[
        spread["p_correlation_with_towns_in_cell"] > spread["p_correlation_with_log_people_in_cell"]
    ]
    model_wider = s[s["mean_width_model_only"] > s["mean_width_stockpile_only"]]
    v = variance["variance_share_theatre"]
    v_low, v_high = variance.loc[v.idxmin()], variance.loc[v.idxmax()]
    shown_choice = choice.rename(
        columns={
            "lopo_pr_auc": "left_out_document_pr_auc",
            "lopo_pr_auc_without_sac": "left_out_document_without_sac",
        }
    )
    us50 = _stockpile_1950_us()
    return f"""The map answers: if a stated number of warheads were delivered, and each fell on a town in
proportion to the score of a model of these lists, how likely is it that an area sees at least one?
It is a consequence of stated assumptions, not a forecast of any war. The viewer is
`runs/probmap/viewer/index.html`, built by `make viewer`.

**Stockpile and allocation.** `data/curated/stockpiles/` holds cited inventories by state, year and,
where a source splits them, delivery, with cited or expressly stated assumptions on availability,
reliability and loss to defences. `configs/scenarios.yaml` states who is assumed to fire on whom and what
share of the inventory goes there. Those are assumptions, not findings. **The theatre shares have no source**; these are all of them, as
(low, mode, high) of a triangular draw:

{markdown(_theatre_table())}

Every historical scenario takes its central reliability (0.65, from the abort, operational-loss and
ineffective-bomb fractions) and its range of losses to defences (0.07 for mid-1953 to 0.27 for mid-1955) from one source's estimates for Soviet
bombers attacking the US (Foreign Relations of the United States, FRUS, 1952-54, vol. II part 1, document 66); the
reliability's spread of plus or minus 0.07 is this study's assumption, not the source's. These stand in for SAC's bombers in 1956 and Soviet missiles and bombers in 1965, because no source for those
forces was found. A delivered warhead falls on a town with
probability equal to the town's share of the scenario's total score, and an area's probability is
1 - (1 - share)^warheads. Nothing is optimised, and no count of weapons by area is computed or written. One interceptor
force is drawn once and shared among the attackers it faces. The modern universe is Natural Earth's populated places: a
map-label set of {int(universe["places in the file"]):,} places, not a census, thinner in some countries than others, of which {int(universe.iloc[-1]):,} are kept:
towns with 10,000 or more people, without France's territories outside Europe (`runs/probmap/modern_universe.csv`). The 1965 scenario's towns carry populations of about 1961.

{_no_uk_1965()}
Warheads are shared out per row, so how a country's towns are cut into rows also moves the map: the rows are municipalities,
and how much that matters was not measured.

**Score.** The selection rule in `configs/protocol.yaml` selected **the {best["model"]}**, by highest PR-AUC on a left-out document
({best["lopo_pr_auc"]:.2f}). The candidates ("portable" in the table) use only features that exist in every era without any present-day
facility data: population, its rank within the country, population within 25, 50 and 100 km, distance to a town of
100,000, distance to the capital, distance to a coast, and whether it is the national capital or a regional centre (ten features). So the map's score holds no defence,
military or national-power term. It is fitted on all attacker documents, exercises included, and is not one
state's model, because no state passes the gate with enough outside its largest document.
{_population_note(best["model"])}

{markdown(shown_choice)}

**What that score does.** On the 1956 towns population runs over a {first["population_ratio"]:.0f}-fold range and the median score over a
{first["score_ratio"]:.1f}-fold range, and a town's share of warheads is its share of the score. So a large town gets only a few times the
warheads of a small one, and a cell's probability depends on how many towns it holds as well as on how many people
live there. Across 1956 cells the probability correlates {first["p_correlation_with_towns_in_cell"]:.2f} with the count of towns and {first["p_correlation_with_log_people_in_cell"]:.2f} with log people.
{_follows(spread, towns_more)} (`runs/probmap/score_spread.csv`).

**Scenarios.** Intervals are the 5th to 95th percentile over {int(pd.read_json(MAP / "manifest.json", typ="series")["draws"])} joint draws of model (block resample, one
bag) and stockpile. They hold fixed the allocation rule, who fires on whom and the list of towns, so they are narrower than
what is actually unknown. "Mean width" is the mean over cells of that interval; the two columns before it hold the
stockpile at its median, then the model at its median. Cells over one half are counted within each draw. Cells saturate because warheads can outnumber cells while not outnumbering towns:
`ussr_1965_on_west` has {count(west_d["delivered_median"])} median delivered warheads, {int(west["towns"])} towns and {int(west["cells"])} cells, and a cell of several towns passes one half
before each of its towns would. Where most cells are over one half the map says little beyond that. Sealed towns are not scored, so a 1956 cell holding only sealed towns is absent from the map.
{_width_source(s, model_wider)}

"Delivered" in the tables below is before one more step: towns of the sealed set are not scored and draw no warheads, so the 1956 map cuts what is delivered by the share of people living in scored towns, {float(bloc_d["share_of_people_in_scored_towns"]):.2f}. That is a population share, not the share of score the sealed towns would hold: they have no score, and the population share is fixed before any model draw. In `us_1956_on_bloc`, of {count(bloc_d["delivered_median"])} delivered at the median, {count(bloc_d["on_scored_towns_median"])} fall on scored towns. Part of the spread of delivered warheads comes from cited inventories and part from the unsourced theatre shares. The theatre share alone accounts for {v.min():.0%} ({v_low["attacker"]}, `{v_low["scenario"]}`) to {v.max():.0%} ({v_high["attacker"]}, `{v_high["scenario"]}`) of the variance of an attacker's delivered warheads: a first-order Sobol index by the pick-freeze estimator on {int(variance["draws"].iloc[0]):,} draws, with standard errors up to {variance["standard_error"].max():.3f} (`runs/probmap/share_variance.csv`).

Counts of warheads and cells are whole below 100 and to the nearest ten from 100, since the theatre shares behind them have no source. In the second table each figure is the median with the 5th to 95th percentile; `on_scored_towns` is "all" where the sealed set holds nobody; `delivered_shares_at_mode` is the interval with every share held at its mode, from separate draws. Holding a share at its mode also moves the centre, so that column is not a split of the interval's width.

{markdown(scen)}

{markdown(_delivered_table(d))}

**By delivery.** Warheads available by state and delivery after the stated assumptions, and those delivered. The
shares come from SIPRI and the Natural Resources Defense Council (NRDC; `data/curated/stockpiles/delivery_mix.csv`), on bases that differ by state. For 1950
NRDC has all on bombers, {us50[0]} loaded, more than the {us50[1]} Our World in Data (OWID) gives for the whole stockpile: the sources conflict, and the
scenario's range runs between them. A share measured on strategic or deployed forces is applied to the whole inventory range, so a
Soviet row of 1965 spreads NRDC's strategic shares over a stockpile that also holds tactical weapons with no known split.
Reliability has one range for every modern delivery, because no source separates them. Each delivery draws from that
range separately, so the split leaves the expected delivered total unchanged and changes only how much the draws average
out. These are totals for a whole force. No delivery is assigned to any area. The table by state and delivery is in
`runs/classifier/TABLES.md` ("Probability map: warheads available and delivered").

**Check against the 1956 list.** A listing is not the same event as a strike: this compares what the map says of a
delivered warhead with what one study listed, so it can show agreement in order and not that the probabilities are right.
The `us_1956_on_bloc` scenario, with {count(spatial["median_warheads_on_scored_towns"])} warheads
on scored towns, against whether SAC listed a town in each 0.5-degree cell. {int(spatial["cells_listed"])} of {int(spatial["cells"])} cells hold a listed town, a
base rate of {spatial["base_rate"]:.2f}. Scored by models that never saw the cell's block: PR-AUC {spatial["pr_auc"]:.2f}, ROC-AUC {spatial["roc_auc"]:.2f},
Brier {spatial["brier"]:.2f} against {spatial["brier_of_base_rate"]:.2f} for the base rate. By models with no SAC row at all: PR-AUC {left["pr_auc"]:.2f}, ROC-AUC {left["roc_auc"]:.2f},
Brier {left["brier"]:.2f}{" (no interval was computed for its difference from the reading above, so the two cannot be told apart)" if left["pr_auc"] != spatial["pr_auc"] else ""}. That second reading looks like transfer, and it is not evidence of it: with a one-feature monotone score,
the order of towns barely depends on which rows trained it, so agreement is largely built in. Across cells the map's mean
probability is {spatial["mean_p"]:.2f} and the share listed {spatial["base_rate"]:.2f}, beside a mean interval width of {bloc_width:.2f} for this scenario. The reliability table:

{markdown(rel[["reading", "bin", "n", "mean_score", "observed"]])}

**Domain shift.** A classifier told the {int(two.iloc[0]["towns_a"]):,} training towns from the {int(two.iloc[0]["towns_b"]):,} modern towns in the countries the modern
scenarios target (of the {int(universe.iloc[-1]):,} kept worldwide) at ROC-AUC {two.iloc[0]["value"]:.2f}, where 0.5 would mean no shift. For scale, it told SAC's towns from the other training towns at
{two.iloc[1]["value"]:.2f}. {worst["value"]:.0%} of modern towns lie outside the training's 1st-99th percentile on `{worst["feature"]}`, the worst feature.
There are no modern labels, so performance on modern towns cannot be measured at all. Every modern row is an
**extrapolation**: it applies lists of 1945-1977 to towns of today, on a selective set of named places. The ROC-AUC is measured on all
{len(outside)} portable features, of which the map's score uses one, `log_pop`{_pop_outside(outside, worst)}. Feature by feature: on its own, `log_pop` separates the two sets at a folded ROC-AUC of {pop_alone:.2f}
(0.5 is no separation); the single features run from {alone.iloc[0]["value"]:.2f} (`{alone.iloc[0]["feature"]}`) to {alone.iloc[-1]["value"]:.2f} (`{alone.iloc[-1]["feature"]}`){", so the one feature the score reads is the one that separates the sets most" if alone.iloc[-1]["feature"] == "log_pop" else ""}.
With one feature left out, the classifier's ROC-AUC stays between {dropped.iloc[0]["value"]:.2f} (without `{dropped.iloc[0]["feature"]}`) and {dropped.iloc[-1]["value"]:.2f}{_carried(dropped, two.iloc[0]["value"])}

Every feature's three figures are in `runs/classifier/TABLES.md` ("Probability map: domain shift").
"""


def _unscored_note(lists: pd.DataFrame) -> str:
    """Lists with positives but no metric (fewer than 2 positives), by name and count, from lists.csv."""
    g = lists[lists["scope"] == GLOBAL_ALL].groupby("plan_id")
    small = g.agg(positives=("positives", "max"), never=("pr_auc", lambda x: x.isna().all()))
    small = small[small["never"] & (small["positives"] > 0)]
    if small.empty:
        return "no list"
    return ", ".join(f"`{plan}` with {int(r.positives)}" for plan, r in small.iterrows())


def _pop_outside(outside: pd.DataFrame, worst) -> str:
    """The share of modern towns outside the training range on log_pop, unless the sentence before gave it."""
    if worst["feature"] == "log_pop":
        return ", the worst feature named above"
    share = float(outside.loc[outside["feature"] == "log_pop", "value"].iloc[0])
    return f": {share:.0%} of modern towns lie outside the training's 1st-99th percentile on it"


def _raw_only(fits: pd.DataFrame) -> str:
    """The as-run identification fits a raw score above MAX_RAW flags and the accuracy-drop rule does not."""
    extra = fits[(fits["max_abs_raw_score"] > MAX_RAW) & ~fits["diverged"].astype(bool)]
    if extra.empty:
        return ""
    named = ", ".join(
        f'"{r.columns}" fold {int(r.fold)} (raw score {r.max_abs_raw_score:,.0f}, training accuracy steady at {_pct(r.train_accuracy_final)})'
        for r in extra.itertuples()
    )
    return f": the extra {'fit is' if len(extra) == 1 else 'fits are'} {named}"


def _pct(v: float) -> str:
    """A share as a percentage, with a decimal where whole percents would hide an order."""
    return f"{v:.1%}"


IDENT = OUT / "identification"
SETS_READ = {
    "all permitted": "on all columns",
    "no national power": "without national power",
    "no source markers": "with no source markers as well",
    "population only": "on population alone",
}


def _points(v: float) -> str:
    return f"{100 * v:+.1f}"


def _verdicts_against_largest(iv: pd.DataFrame) -> str:
    """Each set against always naming the largest document, on the place-bootstrap verdicts."""
    gaps = {
        v: [k for k in SETS_READ if iv.at[k, "over_largest_verdict"] == v]
        for v in ("above", "below", "cannot be told apart")
    }

    def names(ks: list[str]) -> str:
        return ", ".join(f'"{k}"' for k in ks)

    against = []
    if gaps["above"]:
        against.append(f"{names(gaps['above'])} name documents better than that")
    for k in gaps["below"]:
        lead = (
            "population alone does worse than that"
            if k == "population only"
            else f'"{k}" does worse than that'
        )
        against.append(
            f"{lead}, by {-100 * iv.at[k, 'over_largest']:.2f} points "
            f"[{-100 * iv.at[k, 'over_largest_hi']:.2f}, {-100 * iv.at[k, 'over_largest_lo']:.2f}]: it "
            "learns nothing usable about documents and loses a little by sometimes naming another"
        )
    if gaps["cannot be told apart"]:
        against.append(f"{names(gaps['cannot be told apart'])} cannot be told apart from it")
    return "; ".join(against)


def _accuracies(iv: pd.DataFrame) -> str:
    return ", ".join(
        f"{_pct(iv.at[k, 'accuracy'])} [{_pct(iv.at[k, 'accuracy_lo'])}, {_pct(iv.at[k, 'accuracy_hi'])}] {said}"
        for k, said in SETS_READ.items()
    )


def _identification() -> str:
    """The document identification check: the regularised reading of the fourteenth amendment, then what
    the diverged fit of the sixth and thirteenth amendments gave, and their steps still pending."""
    reg = pd.read_csv(IDENT / "regularised.csv").set_index("columns")
    div = pd.read_csv(IDENT / "divergence.csv")
    iv = pd.read_csv(IDENT / "intervals.csv").set_index("columns")
    base = reg["largest_document_share"].iloc[0]
    as_run = div[div["l2_regularization"] == 0]
    regd = div[div["l2_regularization"] > 0]
    nmc = reg.loc["no national power"]
    if nmc["over_reference_verdict"] == "below":
        suspicion = (
            "Removing national power lowers accuracy by "
            f"{-100 * nmc['over_reference']:.1f} points [{-100 * nmc['over_reference_hi']:.1f}, "
            f"{-100 * nmc['over_reference_lo']:.1f}], so those columns do help name the document."
        )
    elif nmc["over_reference_verdict"] == "above":
        suspicion = (
            "Removing national power made identification easier even with the fit regularised."
        )
    else:
        suspicion = (
            "Removing national power changes accuracy by "
            f"{_points(nmc['over_reference'])} points [{_points(nmc['over_reference_lo'])}, "
            f"{_points(nmc['over_reference_hi'])}], which cannot be told from no change: the other columns "
            "name the document as well without them."
        )
    how = (
        "almost always"
        if reg.at["all permitted", "accuracy_lo"] > 0.9
        else "far more often than by naming the largest document"
    )
    consequence = (
        f" The columns name a row's document {how}. In a pooled scope a model can learn each "
        "document's base rate from them, and a pooled gain under spatial blocks cannot be told from that. "
        "Single-document and leave-one-document-out readings do not rest on this check."
        if reg.at["all permitted", "over_largest_lo"] > 0.10
        else ""
    )
    manifest = json.loads((IDENT / "manifest.json").read_text())
    pending = manifest["pending"]
    splits_left = sum(p.startswith("split ") for p in pending)
    left = (
        ["the refit at more iterations (the capacity probe)"] if "capacity probe" in pending else []
    )
    left += [f"{splits_left} of the 10 split repeats"] if splits_left else []
    rest = (
        f" Of its steps, {' and '.join(left)} were not run; they would describe the diverged fit"
        " (`runs/classifier/identification/manifest.json`)."
        if left
        else ""
    )
    return f"""From the columns alone, with folds grouped by place, a gradient-boosted classifier with L2
regularisation 1.0 names a row's document {_accuracies(reg)}, against {_pct(base)} for always naming the largest
document. The intervals resample places, keeping a place's rows together (2,000 resamples;
`runs/classifier/identification/regularised.csv`). On those intervals {_verdicts_against_largest(reg)}.
{suspicion}{consequence}

This reading is post hoc (`configs/protocol_amendment_14.yaml`; one regularisation value was tried). The version fixed in
advance had none: {int(as_run["diverged"].sum())} of its {len(as_run)} fits (four column sets, four folds) diverged, against {int(regd["diverged"].sum())} of {len(regd)} here
(`runs/classifier/identification/divergence.csv`). By the rule fixed for this check in `configs/protocol_amendment_14.yaml`, a fit diverged if its final
training accuracy is more than {100 * DIVERGED_DROP:.0f} points below its best; this is not the raw-score and log-loss rule used
for the primary models under "Fit checks". By that rule's raw score above {MAX_RAW:.0f}, {int((as_run["max_abs_raw_score"] > MAX_RAW).sum())} of the {len(as_run)} would be called diverged{_raw_only(as_run)}. So the intervals of the version fixed in advance, {_pct(iv.at["all permitted", "accuracy_lo"])} to {_pct(iv.at["all permitted", "accuracy_hi"])} on all columns
(`runs/classifier/identification/intervals.csv`), measured a failed fit; it is withdrawn.{rest}
"""


def _subcomplex_extra(n: int) -> str:
    if n == 0:
        return "while linked subcomplex entries give exactly as many towns as entries."
    return f"and linked subcomplex entries {n} more towns than their number."


def _follows(spread: pd.DataFrame, towns_more: pd.DataFrame) -> str:
    """Which scenarios' cells follow log people more than the count of towns, from score_spread.csv."""
    if towns_more.empty:
        return (
            "In every scenario the cell probability correlates more with log people than with the count of "
            "towns: the map follows people on a log scale, far less than in proportion"
        )
    names = [f"`{n}`" for n in towns_more["scenario"]]
    named = names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"
    return (
        f"In {len(spread) - len(towns_more)} of {len(spread)} scenarios it correlates more with log people "
        f"than with the count of towns; in {named} it correlates more with the count of towns"
    )


def _width_source(s: pd.DataFrame, model_wider: pd.DataFrame) -> str:
    """Which part of the interval is wider, scenario by scenario, from scenarios.csv. No cause is claimed."""
    n, k = len(s), len(model_wider)
    if k == 0:
        return (
            f"In all {n} scenarios the mean width with the model held at its median is larger than with "
            "the stockpile held at its median: the stockpile draws, not the model, make most of the width."
        )
    named = ", ".join(f"`{x}`" for x in model_wider["scenario"])
    return (
        f"In {n - k} of {n} scenarios the mean width with the model held at its median is larger than with the "
        f"stockpile held at its median; in {named} the model's part is the larger."
    )


def _holdout_list(names: list[str]) -> str:
    """Holdout names in running text: lower case and quoted, since some hold commas."""
    quoted = [f'"{n[0].lower() + n[1:]}"' for n in names]
    if not quoted:
        return "no holdout"
    return quoted[0] if len(quoted) == 1 else ", ".join(quoted[:-1]) + " and " + quoted[-1]


def _carried(dropped: pd.DataFrame, whole: float) -> str:
    """What leaving one feature out says, in words the numbers support."""
    fall = whole - dropped["value"].min()
    if fall < 0.02:
        return (
            f", within {fall:.2f} of the {whole:.2f} on all of them, so no single feature carries the shift: "
            "the rest still tell the sets apart. That measures the shift; it does not show the score valid there."
        )
    return (
        f": leaving out `{dropped.iloc[0]['feature']}` lowers it by {fall:.2f}, the most of any feature. "
        "That measures the shift; it does not show the score valid there."
    )


def _calibration_terms(cal: pd.DataFrame, base: float) -> str:
    """What the calibration table's columns mean and what it shows, from the table."""
    raw = cal[cal["kind"] == "raw"].set_index("model")
    iso = cal[cal["kind"] == "isotonic"].set_index("model")
    change = (iso["brier"] - raw["brier"]).abs().max()
    lo, hi = cal["brier"].min(), cal["brier"].max()

    def models(v):
        return " and ".join(sorted(set(cal.loc[(cal["brier"] - v).abs() < 1e-12, "model"])))

    return (
        "The **Brier score** is the mean squared difference between a town's score and its label (1 listed, 0 not): "
        f"0 is perfect, and giving every town the list's base rate {base:.2f} scores {base * (1 - base):.2f}. The "
        "**expected calibration error** (ECE) sorts towns into bins by score and averages, weighted by bin size, the "
        "gap between a bin's mean score and its share of listed towns, so 0.03 means scores are off by about three "
        f"points on average. Brier runs from {lo:.2f} ({models(lo)}) to {hi:.2f} ({models(hi)}); every ECE is "
        f"{cal['expected_calibration_error'].max():.2f} or less, and the isotonic remapping changes no model's Brier by "
        f"more than {change:.3f}. On SAC's list, then, the raw scores already lie close to observed shares."
    )


def _targets_1965() -> list[str]:
    from nucprob.probmap.run import load_scenarios

    sc = next(s for s in load_scenarios() if s["id"] == "ussr_1965_on_west")
    return [t for a in sc["attackers"] for t in a["targets"]]


def _countries(names: list[str]) -> str:
    names = ["the FRG" if n == "FRG" else n for n in names]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _no_uk_1965() -> str:
    """REPORT's paragraph on the countries withdrawn from the 1965 map, from the scenario's targets."""
    targets = _targets_1965()
    if "Netherlands" in targets:
        return f"""**No United Kingdom in 1965.** The only UK table held, Great Britain's 1981 districts, came through a path of
`www.nomisweb.co.uk` that robots.txt disallows, and was withdrawn (`configs/protocol_amendment_10.yaml`). So the
1965 map covers {_countries(targets)}, and its unsourced theatre share falls on them
alone, so its continental cells read higher than they would if the UK were among the targets."""
    return f"""**No United Kingdom or Netherlands in 1965.** The only UK table held, Great Britain's 1981 districts, came through a
path of `www.nomisweb.co.uk` that robots.txt disallows, and was withdrawn (`configs/protocol_amendment_10.yaml`). The
Dutch census volume of 1960 came through a path of `ssh.datastations.nl` that robots.txt disallows, and was withdrawn
too (`configs/protocol_amendment_19.yaml`). So the 1965 map covers {_countries(targets)}, and its unsourced theatre
share falls on them alone, so their cells read higher than they would if the two were among the targets."""


def _readme_1965() -> str:
    if "Netherlands" in _targets_1965():
        return "The 1965 map has no United Kingdom: its only census table came\n  through a path robots.txt disallows and was withdrawn."
    return (
        "The 1965 map has no United Kingdom and no Netherlands: their census tables came\n  through paths robots.txt "
        "disallows and were withdrawn."
    )


def _not_held() -> str:
    it = f"`census_it_1961` ({len(pd.read_csv(CURATED / 'gazetteer' / 'towns_it_1961.csv'))} of the Western towns)"
    if (CURATED / "gazetteer" / "towns_nl_1960.csv").exists():
        return (
            f"- {it} and the Dutch census volume are not held: `towns_it_1961.csv` and `towns_nl_1960.csv` stand as their "
            "records (`data/sources.yaml`, `held`)."
        )
    return f"- {it} is not held: `towns_it_1961.csv` stands as its record (`data/sources.yaml`, `held`)."


def _rule_outside() -> int:
    return protocol()["state_models"]["min_positives_outside_largest"]


def _defence_summary() -> str:
    t = pd.read_csv(OUT / "defence_targets.csv").set_index("document")
    radar = t.loc[t.index.str.contains("category 284")].iloc[0]
    rows = t[t["counted"] == "designated rows"]
    pact = rows[rows.index.str.startswith("wp_")]
    return (
        f"In SAC's study {int(radar['naming_defences'])} of the {int(radar['total']):,} complex and subcomplex entries that hold a coded installation "
        "hold a radar installation (the link figures above count complex entries alone). "
        f"Across the Warsaw Pact lists {int(pact['naming_defences'].sum())} of {int(pact['total'].sum())} designated rows name "
        f"a defence, {pact['naming_defences'].gt(0).sum()} lists of {len(pact)}."
    )


EXTENDED_COLUMNS = [
    "scope",
    "comparison",
    "holdout",
    "lists",
    "positives",
    "train_positives",
    "model",
    "against",
    "difference",
    "by_blocks",
    "verdict",
]


def _extended_rows() -> pd.DataFrame | None:
    """runs/classifier/extended.csv as the report reads it, or None before it is run."""
    path = OUT / "extended.csv"
    d = pd.read_csv(path) if path.exists() else pd.DataFrame()
    if "verdict" not in d:
        return None
    # A scope with no SAC rows repeats its "all lists" row under "other than SAC".
    no_sac = d["scope"].str.startswith("Warsaw")
    d = d[~(no_sac & d["lists"].eq("other than SAC"))].reset_index(drop=True)
    return d.assign(
        difference=d.apply(interval, axis=1),
        by_blocks=d.apply(
            lambda r: f"[{signed(r['block_low'])}, {signed(r['block_high'])}]", axis=1
        ),
        model=d["a_pr_auc"],
        against=d["b_pr_auc"],
    )


def _extended_section() -> str:
    d = _extended_rows()
    if d is None:
        return "The economic and political readings have not been run.\n"
    vpk = d[d["comparison"] == "defence industry over population"].iloc[0]
    counts = d["verdict"].value_counts()
    lopo = d[(d["holdout"] == "leave one document out") & (d["verdict"] != "not a reading")]
    lopo_gains = int((lopo["verdict"] == "gain").sum())
    lopo_rest = lopo[lopo["lists"] == "other than SAC"]
    gains = lopo[lopo["verdict"] == "gain"]
    named = "; ".join(
        f"{r['comparison']} in the {r['scope']} scope on {r['lists']}, {r['a_pr_auc']:.2f} against {r['b_pr_auc']:.2f}"
        for _, r in gains.iterrows()
    )
    gain_note = (
        f'The gains: {named}. A comparison named "over primary" is against LightGBM on all permitted features, and one named '
        '"over population" against LightGBM on the population family, not against the plain population rule. '
        if len(gains)
        else ""
    )
    rest_gains = int((lopo_rest["verdict"] == "gain").sum())
    comp = pd.read_csv(OUT / "comparison.csv")
    rule = {}
    for lists, name in (("all lists", "all lists"), ("lists other than SAC", "other than SAC")):
        r = comp[
            (comp["scope"] == "global, all attacker documents")
            & (comp["holdout"] == "leave one document out")
            & (comp["against"] == "population rule")
            & (comp["lists"] == lists)
        ].iloc[0]
        rule[name] = r["b_pr_auc"]
    glob = lopo[lopo["scope"] == "global, all attacker documents"]
    best = {k: glob.loc[glob["lists"] == k, "a_pr_auc"].max() for k in rule}
    spatial = d[(d["holdout"] == "spatial blocks") & (d["verdict"] != "not a reading")]
    spatial = spatial[spatial["comparison"] != "defence industry over population"]
    shown = (d["scope"] == "global, all attacker documents") & (
        d["holdout"] == "leave one document out"
    )
    table = d.loc[shown | (d["comparison"] == "defence industry over population"), EXTENDED_COLUMNS]
    return f"""The primary model holds almost no economic or political data. `configs/protocol_amendment_5.yaml` fixed, before
any of these columns was fitted, a separate reading of the target state's regime (Regimes of the World), its defence pacts
(COW Formal Alliances) and its GDP per capita (Maddison), each as of the document's year, and of the Soviet defence-industry
counts on Soviet towns. None of them enters the primary model or the map. A gain needs both intervals to exclude zero.

Of {len(d)} rows (`runs/classifier/extended.csv` has {len(pd.read_csv(OUT / "extended.csv"))}: the Warsaw Pact scope has no SAC rows, so its "other than SAC" rows repeat its "all lists" rows and are counted once): {int(counts.get("gain", 0))} gain, {int(counts.get("loss", 0))} lose, {int(counts.get("neither", 0))} cannot be told apart, {int(counts.get("not a reading", 0))} are not readings. On a left-out document, the reading that
matters here, {lopo_gains} of {len(lopo)} rows gain, and {rest_gains} of the {len(lopo_rest)} on lists other than SAC. {gain_note}In the global scope the highest of its six models (population plus the political, economic, national-power or all three
columns; the primary model plus the political or economic columns), picked after the fact for each list set, scores {best["all lists"]:.2f} over all lists against {rule["all lists"]:.2f} for the plain population rule, and {best["other than SAC"]:.2f} on lists other than SAC
against {rule["other than SAC"]:.2f}; no paired interval against the population rule was fixed in advance, so the second gap is not a finding. The all-lists rows also rest on the fit with SAC left out, which trains on few positives. Each country-level column has one value per country and year, so within one
list it can do no more than a country term, and in a pooled list it can identify a document: a gain under spatial blocks
may be just that. "Model" and "against" are PR-AUC with and without the columns.

Counts of Soviet defence plants add {interval(vpk)} (by blocks {block_interval(vpk)}) to population on Soviet towns
of the SAC list, PR-AUC {vpk["a_pr_auc"]:.2f} against {vpk["b_pr_auc"]:.2f}: no detectable gain. The counts are later knowledge of what existed, not what SAC
knew, and they are matched to the town by name, so this does not show that SAC ignored industry.

Under spatial blocks {int((spatial["verdict"] == "gain").sum())} of {len(spatial)} rows gain. The table holds the global scope's rows on a left-out
document and the defence-industry row; all {len(d)} rows are in `runs/classifier/TABLES.md`.

{markdown(table)}

{near_zero_note(d, lambda r: f"{r['scope']}, {r['comparison']}, {r['holdout']}, {r['lists']}").lstrip()}
"""


def near_zero_note(d: pd.DataFrame, describe) -> str:
    """For a table read under seed 1956 alone: the gains whose deciding lower bound lies within NEAR_ZERO of zero."""
    g = d[d["verdict"].eq("gain") & (d[["low", "block_low"]].min(axis=1) < NEAR_ZERO)]
    if g.empty:
        return ""
    names = "; ".join(
        f"{describe(r)} ({signed(min(r['low'], r['block_low']))})" for _, r in g.iterrows()
    )
    one = len(g) == 1
    s = seed_summary()
    moved = (
        ""
        if s is None
        else (
            f", and under the 20 seeds of the primary check {int((~seed_distinct(s)['seed_stable'].astype(bool)).sum())} of {len(seed_distinct(s))} "
            "verdicts moved"
        )
    )
    return (
        f" {'One gain rests' if one else f'{len(g)} gains rest'} on a lower bound within {NEAR_ZERO} of zero: {names}. "
        f"{'It was' if one else 'They were'} not repeated under other bootstrap seeds{moved} "
        '("Bootstrap seed", under "Models against baselines").'
    )


SEALED = OUT / "sealed" / "metrics.csv"


def _sealed_status() -> str:
    return "It has been scored once; see below." if SEALED.exists() else "It has not been scored."


def _sealed_not_done() -> str:
    if SEALED.exists():
        return ""
    return "- The sealed set (`python -m nucprob.classifier.sealed`) is reserved until the models have been reviewed.\n"


NUMBER_WORDS = "zero one two three four five six seven eight nine ten".split()


@functools.cache
def _pooled_countries() -> list[str]:
    """Countries of the towns the pooled Warsaw Pact scope was fitted and scored on, read from the place ids
    of its spatial-block scores (`wp_west_1965:<country>:<n>`)."""
    path = OUT / "held_out_scores.csv.gz"
    h = pd.read_csv(path, usecols=["scope", "holdout", "place_id"])
    ids = h.loc[
        h["scope"].str.startswith("Warsaw Pact, pooled") & (h["holdout"] == "spatial blocks"),
        "place_id",
    ]
    parts = ids.str.split(":")
    assert (parts.str.len() == 3).all(), "pooled scope place ids no longer carry a country"
    return sorted(parts.str[1].unique())


def _pooled_sealed(prim: pd.DataFrame) -> str:
    r = prim[prim["scope"].str.startswith("Warsaw Pact, pooled")]
    if r.empty or not (r.iloc[0]["high"] < 0 and not r.iloc[0]["block_excludes_zero"]):
        return ""
    r = r.iloc[0]
    return (
        f"The pooled Warsaw Pact model ranks these places worse than population does ({point(r['delta'], r['low'], r['high'])}); "
        "the town interval calls that a loss and the block interval does not, so by the rule it is neither. "
        f"It was trained on towns in {_count_word(len(_sealed_fit_countries()))} Western countries "
        f"({', '.join(_sealed_fit_countries())}) and is applied here to Eastern bloc places."
    )


def _sealed_fit_countries() -> list[str]:
    """The pooled scope's countries in the fit the sealed set was scored with. The sealed set is scored once; a later
    refit on a table without the Dutch towns (the nineteenth amendment) does not change what that fit was trained on."""
    countries = _pooled_countries()
    lock = json.loads((OUT / "sealed" / "LOCK.json").read_text())
    current = json.loads((OUT / "manifest.json").read_text())["table_sha256"]
    if lock["table_sha256"] != current and "Netherlands" not in countries:
        countries = sorted([*countries, "Netherlands"])
    return countries


def _count_word(n: int) -> str:
    return NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)


def _sac_sealed_gap() -> str:
    """Connects SAC's linked positives to the positives of its scope: the difference is the sealed listed places."""
    if not SEALED.exists():
        return ""
    comp = pd.read_csv(SEALED.parent / "comparison.csv")
    sealed_pos = int(comp.loc[comp["population"].eq("all sealed"), "positives"].iloc[0])
    scope = pd.read_csv(OUT / "comparison.csv")
    scope_pos = scope.loc[scope["scope"].str.startswith("single document: SAC 1956"), "positives"]
    if scope_pos.empty:
        return ""
    return (
        f" Of SAC's, {sealed_pos} lie in the sealed blocks and are held out of every fit, which leaves the"
        f" {int(scope_pos.iloc[0])} positives of the SAC rows in the tables below."
    )


def _sealed_section() -> str:
    """The one blind reading (configs/protocol_amendment_11.yaml), from runs/classifier/sealed/."""
    if not SEALED.exists():
        return ""
    comp = pd.read_csv(SEALED.parent / "comparison.csv")
    lock = json.loads((SEALED.parent / "LOCK.json").read_text(encoding="utf-8"))
    prim = comp[comp["primary"]]
    allp = comp[comp["population"].eq("all sealed") & comp["against"].eq(PLUS)]
    p0, a0 = prim.iloc[0], allp.iloc[0]

    shown = comp.assign(
        population=comp["population"].replace({"never_scored": "not in the early check"}),
        difference=[f"{interval(r._asdict())}" for r in comp.itertuples()],
        by_blocks=[f"[{signed(r.block_low)}, {signed(r.block_high)}]" for r in comp.itertuples()],
    )[
        [
            "scope",
            "population",
            "model",
            "against",
            "a_pr_auc",
            "b_pr_auc",
            "difference",
            "by_blocks",
            "verdict",
        ]
    ]
    gains = prim[prim["verdict"].eq("gain")]["scope"].tolist()
    other = prim[~prim["verdict"].eq("gain")]
    return f"""### The sealed set, scored once

This reading is not blind: earlier runs had scored some of these places (previous section). It was made once, on {lock["scored"][:10]},
after `configs/protocol_amendment_11.yaml` fixed how it would be read; `runs/classifier/sealed/LOCK.json` records the commit and
stops a second run. Each scope's models were fitted on all its usable rows and scored SAC 1956's rows in the sealed blocks, on two sets:

- the {int(p0["rows"])} labelled places the early check had not scored (`never_scored` in the outputs, although other runs had scored
  some of them; {int(p0["positives"])} listed, base rate {p0["base_rate"]:.2f}, in {int(p0["blocks"])} blocks). The primary rows are on this set.
- all {int(a0["rows"])} sealed places with a SAC label ({int(a0["positives"])} listed). {SEALED_PLACES - pd.read_csv(OUT / "sealed" / "scores.csv.gz", usecols=["place_id"])["place_id"].nunique()} of the {SEALED_PLACES} sealed places have no SAC label,
  possibly an entry lost from the scan, and so no row.

Against population plus country the selected candidate gains in {len(gains)} of {len(prim)} scopes
({"; ".join(f"'{g}'" for g in gains) if gains else "none"}), and not in {"; ".join(f"'{r.scope}' ({r.verdict})" for r in other.itertuples())}.
{_pooled_sealed(prim)}
The gains are a few hundredths of PR-AUC on a base rate above one half. Only SAC 1956 has sealed rows, so this tests the
models on that list's places, the source of most of every global model's training positives, and says nothing about the
other documents. {_sealed_block_sentence()}{_country_rule_sentence()}

{markdown(shown)}

Every model's metrics on both populations, with a PR-AUC interval each, are in `runs/classifier/sealed/metrics.csv`.{near_zero_note(pd.read_csv(SEALED.parent / "comparison.csv"), lambda r: f"{r['scope']}, {r['population']}, against {r['against']}")}
"""


BLIND = OUT / "sealed" / "blind" / "comparison.csv"


def _blind_rows(against: str) -> pd.DataFrame:
    """The blind reading's rows against one baseline (configs/protocol_amendment_12.yaml)."""
    comp = pd.read_csv(BLIND)
    return comp[comp["population"].eq("blind") & comp["against"].eq(against)]


@functools.cache
def _country_is_rule() -> frozenset[str]:
    """Scopes whose population-plus-country model ranks every sealed place exactly as their population rule does:
    no sealed place's country has an intercept in that scope's lists, so that baseline is the population rule."""
    s = pd.read_csv(OUT / "sealed" / "scores.csv.gz")
    scopes = {c.split(" | ")[0] for c in s.columns if " | " in c}
    return frozenset(
        sc
        for sc in scopes
        if s[f"{sc} | {PLUS}"].rank(method="min").eq(s[f"{sc} | {RULE}"].rank(method="min")).all()
    )


def _country_rule_sentence() -> str:
    """Which scopes' population-plus-country rows on the sealed set are the population rule, and why."""
    same = sorted(_country_is_rule())
    if not same:
        return ""
    return (
        f" In {'; '.join(repr(x) for x in same)}, population plus country ranks every sealed place as the population "
        f"rule does, so its rows against population plus country are comparisons with the population rule: none of the "
        f"sealed places' countries (the Soviet bloc's and China's) is in that scope's lists, so none has an intercept of its own."
    )


def _rule_note(scope: str, against: str = PLUS) -> str:
    """A flag on a sealed row against population plus country that is in fact a comparison with population."""
    if against != PLUS or scope not in _country_is_rule():
        return ""
    return " (here population plus country ranks every place as the population rule does: this scope's lists hold no town of these countries)"


def _blind_line(r, auc: bool = True) -> str:
    blocks = (
        f"[{signed(r['block_low'])}, {signed(r['block_high'])}]"
        if r["block_measured"]
        else f"n/a: positives in {int(r['positive_blocks'])} blocks"
    )
    scores = f"{r['a_pr_auc']:.2f} against {r['b_pr_auc']:.2f}, " if auc else ""
    return (
        f"{r['scope']}, {r['model']}: {scores}"
        f"{interval(r)}, by blocks {blocks}: {r['verdict']}"
        f"{_rule_note(r['scope'], r['against'])}"
    )


DIVERGENCE = OUT / "divergence"


def _divergence_fits() -> pd.DataFrame | None:
    path = DIVERGENCE / "fits.csv"
    return pd.read_csv(path) if path.exists() else None


def _fit_check() -> str:
    """The Method bullet on the fifteenth amendment's divergence check, from runs/classifier/divergence/."""
    fits = _divergence_fits()
    if fits is None:
        return "- **Fit checks.** The test of the primary fits for divergence (`configs/protocol_amendment_15.yaml`) has not been run."
    n, bad = len(fits), int(fits["diverged"].sum())
    lgb = fits[fits["kind"] == "lightgbm"]
    lr = fits[fits["kind"] == "logistic"]
    rise = (lgb["loss_final"] - lgb["loss_min"]).max()
    hits = int(lr["solver_hit_max_iter"].sum())
    solver = (
        "no logistic solver stopped at its cap of 5,000 iterations"
        if hits == 0
        else f"{hits:,} logistic fits stopped at the solver's cap of 5,000 iterations"
    )
    return f"""- **Fit checks.** The document identification classifier (Results, "What the gains rest on") diverged, so
  an amendment fixed before it was run (`configs/protocol_amendment_15.yaml`) refitted the primary models to see whether they do too: every
  bag of the four models on each scope's whole rows, the five folds of the first spatial grid, each left-out
  document and both temporal directions, {n:,} bag fits in all. A test checks that the refitting code draws and fits
  bags exactly as the primary run's code does. Of the {n:,}, {bad:,} were called diverged. A LightGBM fit is called diverged if its training log
  loss ends more than {LOSS_RISE} above its lowest value or a raw score passes {MAX_RAW:.0f}; a logistic fit if its
  solver stops at its iteration cap or a decision value passes {MAX_RAW:.0f}. LightGBM's training loss {_rise_words(rise)}, and its largest raw score was {lgb["max_abs_raw"].max():.1f}; {solver}, and the
  largest decision value was {lr["max_abs_raw"].max():.1f} (`runs/classifier/divergence/summary.csv`). This shows
  whether the fits converged, not that the models are right. The grids shifted by 100 and 200 km and the fits
  that keep a left-out document's towns were not refitted."""


def _rise_words(rise: float) -> str:
    if rise <= 0:
        return "never ended above its lowest value"
    return f"ended at most {rise:.2g} above its lowest value"


def _main_divergence() -> str:
    """A main-result bullet only if some primary fit was called diverged (the fifteenth amendment's rule)."""
    fits = _divergence_fits()
    if fits is None or not fits["diverged"].any():
        return ""
    bad = fits[fits["diverged"].astype(bool)]
    where = bad.groupby(["scope", "holdout", "model"], sort=False).size()
    named = "; ".join(f"{s}, {h}, {m} ({k} bags)" for (s, h, m), k in where.items())
    return (
        f"- **Some primary fits diverged**: {len(bad):,} of {len(fits):,} bag fits, in {named}"
        " (`runs/classifier/divergence/summary.csv`). The results of those rows rest on them; the fifteenth"
        " amendment does not refit or correct them.\n"
    )


def _main_lead() -> str:
    """The report's first sentences, which follow the blind reading where one exists."""
    inside = (
        "Under cross-validation inside SAC's 1956 study, the models describe that list a little better than "
        "population and a country term do."
    )
    if not BLIND.exists():
        return inside + " That gain has not been shown to reach other documents."
    prim = _blind_rows(PLUS)
    gains = int(prim["verdict"].eq("gain").sum())
    if gains == 0:
        blind = (
            f"On the only blind test, {int(prim.iloc[0]['rows'])} places of the sealed set that no run had scored, "
            "that gain is not seen: no selected model beats population plus country there."
        )
    else:
        blind = (
            f"On the only blind test, {int(prim.iloc[0]['rows'])} places of the sealed set that no run had scored, "
            f"{gains} of {len(prim)} selected models beat population plus country."
        )
    return f"{inside} {blind} No gain has been shown to reach a document the models did not see."


def _main_blind() -> str:
    if not BLIND.exists():
        return ""
    prim, rule = _blind_rows(PLUS), _blind_rows(RULE)
    p0 = prim.iloc[0]
    gained = rule[rule["verdict"].eq("gain")]
    rule_text = (
        f"Against the population rule, {len(gained)} of {len(rule)} scopes gain by both intervals"
        + (
            ": "
            + "; ".join(f"{r.scope} {interval(r._asdict())}" for r in gained.itertuples())
            + "."
            if len(gained)
            else "."
        )
    )
    return f"""- **On the blind places** of the sealed set ({int(p0["rows"])} towns with a SAC label, {int(p0["positives"])} listed, base rate
  {p0["base_rate"]:.2f}, positives in {int(p0["positive_blocks"])} of {int(p0["blocks"])} blocks), each scope's selected model against population plus country:
{chr(10).join("  - " + _blind_line(r, auc=False) for _, r in prim.iterrows())}

  {rule_text} With positives in so few blocks the intervals are wide, and "neither" is not evidence of no
  effect. {_earlier_sealed()} The blind places were set apart after the reading of all sealed places had been seen
  (`configs/protocol_amendment_12.yaml`, which refits nothing), and the sealed scores are of the fit made before the
  corrected West European site table ("Changed by the corrected West European site table").
"""


def _earlier_sealed() -> str:
    """What the first, not blind, sealed reading said, so the main result cannot quote it alone."""
    prim = pd.read_csv(SEALED.parent / "comparison.csv")
    prim = prim[prim["primary"]]
    gains = prim.loc[prim["verdict"].eq("gain"), "scope"].tolist()
    if not gains:
        return ""
    return (
        f"On the {int(prim.iloc[0]['rows'])} sealed places the early check (the two test models run before this classifier) had not scored, a larger set that includes places "
        f"other runs had scored, {len(gains)} of {len(prim)} models ({'; '.join(gains)}) did gain over population plus "
        'country; that reading is not blind ("The sealed set, scored once").'
    )


def _blind_section() -> str:
    """The twelfth amendment's reading of the committed sealed scores on places no run scored."""
    if not BLIND.exists():
        return ""
    comp = pd.read_csv(BLIND)
    prim = comp[comp["primary"]]
    p0 = prim.iloc[0]
    ns = comp[comp["population"].eq("never_scored") & comp["against"].eq(PLUS)].iloc[0]
    lost = int(ns["rows"]) - int(p0["rows"])

    rule = comp[comp["population"].eq("blind") & comp["against"].eq(RULE)].set_index("scope")
    rows = pd.DataFrame(
        [
            {
                "scope": r["scope"],
                "model": r["model"],
                "a_pr_auc": r["a_pr_auc"],
                "against population + country": _blind_cell(r),
                "against population rule": _blind_cell(rule.loc[r["scope"]]),
            }
            for _, r in prim.iterrows()
        ]
    )
    same = sorted(_country_is_rule() & set(prim["scope"]))
    same_text = (
        f" In {'; '.join(repr(x) for x in same)} the two baselines rank every place alike, so its two columns are one"
        ' comparison ("The sealed set, scored once").'
        if same
        else ""
    )
    return f"""### The sealed set on blind places

These are the blind places' results: {int(p0["rows"])} places of the sealed set with a SAC label that no committed run had
scored ({int(p0["positives"])} listed, base rate {p0["base_rate"]:.2f}, in {int(p0["blocks"])} blocks, positives in {int(p0["positive_blocks"])}). `a_pr_auc` is the selected
candidate's PR-AUC; each other cell is its difference from that baseline, the block interval and the verdict.{same_text}

{markdown(rows)}

With {int(p0["rows"])} places, and positives in {int(p0["positive_blocks"])} blocks, the intervals are wide. The
blind places' neighbours, and same-named towns elsewhere, were scored in earlier runs, so this is a reading of places no
run scored, not of a region none had seen. All rows, with every model's metrics: `runs/classifier/sealed/blind/`.

How the blind places were found. "The early check" is two test models run before this classifier and outside its
protocol: the M1 slice (USSR towns only, population and administrative features, `runs/m1-slice/`) and the M2 check (every
bloc country and feature family on the 1956 list, `runs/m2-check/`), as read when the sealed blocks
were drawn (`data/curated/splits/scored_before_freeze.csv`): {EARLY_SCORED} of the {SEALED_PLACES} sealed places had a score there. The sealed
scoring (next section) took the other {AMENDMENT_11_SET} as unscored; {int(ns["rows"])} of those have a SAC label. Earlier versions of
the M2 check had scored places that the version read then no longer scored, so a walk over every commit before the sealed
scoring (`scripts/scored_history.py`, output `data/curated/splits/scored_in_history.csv`) looked for any committed
score. It found one for {lost} of the {int(ns["rows"])}; the other {int(ns["rows"]) - lost} are the blind places.
`configs/protocol_amendment_12.yaml` made that restriction after the next section's reading had been seen; it refits
and rescores nothing. `python -m nucprob.classifier.sealed_reread` reads the committed sealed scores, checking their hash.
"""


def _blind_cell(r) -> str:
    blocks = (
        f"[{signed(r['block_low'])}, {signed(r['block_high'])}]"
        if r["block_measured"]
        else f"n/a: positives in {int(r['positive_blocks'])} blocks"
    )
    return f"{interval(r)}, by blocks {blocks}: {r['verdict']}"


def _undated_sites() -> int:
    """Rows of the West European site table with no from_year that it holds as in role in 1965: they count for
    every document, including those of 1961 and 1964 (nucprob.classifier.features.sites_as_of)."""
    s = pd.read_csv(CURATED / "features" / "weurope_military_sites_1965.csv")
    undated = pd.to_numeric(s["from_year"], errors="coerce").isna()
    in_role = s["in_role_1965"].astype(str).str.lower().isin(["true", "1", "yes"])
    return int((undated & in_role & s["lat"].notna() & s["lon"].notna()).sum())


def _audit() -> dict:
    """The SAC transcription audit (data/curated/sac1956/audit.csv): lines read again, lines where the final
    reading was wrong, and the upper end of the 95% Wilson interval of that error rate."""
    a = pd.read_csv(CURATED / "sac1956" / "audit.csv")
    n, wrong, z = len(a), int((~a["outcome"].isin(["agree", "curated right"])).sum()), 1.959964
    p = wrong / n
    centre, half = p + z * z / (2 * n), z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return {"lines": n, "wrong": wrong, "upper": (centre + half) / (1 + z * z / n)}


def _stockpile_1950_us() -> tuple[int, int]:
    """NRDC's US bomber loading of 1950 and OWID's US stockpile of that year (data/curated/stockpiles/)."""
    s = pd.read_csv(CURATED / "stockpiles" / "stockpiles.csv")
    s = s[(s["scenario_year"] == 1950) & (s["state"] == "US")]
    nrdc = s[s["source_id"] == "nrdc_table_us"]["central"].iloc[0]
    owid = s[s["source_id"] == "owid_warhead_stockpiles"]["central"].iloc[0]
    return int(nrdc), int(owid)


FITTED_RUN = OUT / "sealed" / "fitted_run"


BEFORE_17 = OUT / "before_amendment_17"
BEFORE_19 = OUT / "before_amendment_19"


def _moved(was_dir, now_dir) -> tuple[str, str]:
    """Which primary verdicts and selections differ between two runs' comparison.csv and selection.csv."""
    now_sel = pd.read_csv(now_dir / "selection.csv")
    was_sel = pd.read_csv(was_dir / "selection.csv")
    now = primary_table(pd.read_csv(now_dir / "comparison.csv"), now_sel)
    was = primary_table(pd.read_csv(was_dir / "comparison.csv"), was_sel)
    key = ["Scope", "Holdout", "Lists"]
    both = now.merge(was, on=key, suffixes=("", "_was"))
    moved = both[both["Verdict"] != both["Verdict_was"]]
    pick = lambda s: s[s["selected"]].set_index("scope")["model"]  # noqa: E731
    sel_now, sel_was = pick(now_sel), pick(was_sel)
    changed = [s for s in sel_now.index if sel_was.get(s) != sel_now[s]]
    if moved.empty:
        verdicts_text = (
            f"None of the {len(both)} primary rows (each scope's selected candidate against population plus "
            "country, by holdout and list set) changes verdict."
        )
    else:
        verdicts_text = (
            f"{len(moved)} of the {len(both)} primary rows (each scope's selected candidate against population "
            "plus country, by holdout and list set) change verdict; each difference is followed by its interval "
            "by blocks:\n\n"
            + "\n".join(
                f"- {r['Scope']}, {r['Holdout'][0].lower() + r['Holdout'][1:]}, {r['Lists']}: "
                f"{r['Verdict_was']} before ({r['Difference, country_was']}, by blocks {r['By blocks_was']}), "
                f"{r['Verdict']} now ({r['Difference, country']}, by blocks {r['By blocks']})"
                for _, r in moved.iterrows()
            )
            + "\n\n"
        )
    if changed:
        sel_text = (
            " The refit selects a different model than the earlier run for "
            + "; ".join(f"'{s}' ({sel_was.get(s)} before, {sel_now[s]} now)" for s in changed)
            + ": the sealed and blind rows of those scopes are of the earlier selection."
        )
    else:
        sel_text = (
            " Every scope selects the same model as before, so the sealed and blind rows are of the models this "
            "refit selects, fitted on the earlier table."
        )
    if not moved.empty:
        sel_text = sel_text.lstrip()  # a new paragraph after the list
    return verdicts_text, sel_text


def _table_of(run_dir) -> str:
    return json.loads((run_dir / "manifest.json").read_text())["table_sha256"]


def _amendment_16() -> str:
    """The sixteenth amendment's paragraph: every primary verdict that moved between the run the sealed set was
    scored with (sealed/fitted_run/) and the refit on the corrected West European site table. Once a later
    amendment refits again, the sixteenth's refit is the run kept in before_amendment_17/."""
    if not (FITTED_RUN / "comparison.csv").exists():
        return ""
    after_16 = BEFORE_17 if (BEFORE_17 / "comparison.csv").exists() else OUT
    if _table_of(FITTED_RUN) == _table_of(after_16):
        return ""
    verdicts_text, sel_text = _moved(FITTED_RUN, after_16)
    return f"""### Changed by the corrected West European site table

`configs/protocol_amendment_16.yaml` corrected 29 West European site rows that had no cited text (Data, "Military and
defence sites of 1965") and refitted every classifier step on the corrected table. Four columns change, on rows of
three documents, two Warsaw Pact and one a Soviet lesson list: distance to a naval base, distance to an air defence site and air defence sites within
50 km on rows of Lato-67 and the 1977 staff-academy lessons, and distance to a long-range aviation base on rows of
the 1965 Hungarian war game (the amendment's `table` field). The sealed set was not scored again: its scores, and the blind reading of them, are of
the fit on the earlier table (`runs/classifier/sealed/fitted_run/`). {verdicts_text}{sel_text}
"""


def _amendment_19() -> str:
    """The nineteenth amendment's paragraph: every primary verdict that moved between the run kept in
    before_amendment_19/ and the refit without the Dutch towns and with sites at cell centres. Empty until then."""
    if not (BEFORE_19 / "comparison.csv").exists() or _table_of(BEFORE_19) == _table_of(OUT):
        return ""
    verdicts_text, sel_text = _moved(BEFORE_19, OUT)
    sel_text = sel_text.replace(
        "Every scope selects the same model as before, so the sealed and blind rows are of the models this "
        "refit selects, fitted on the earlier table.",
        "Again every scope selects the same model as before.",
    )
    return f"""
### Changed by the nineteenth amendment

`configs/protocol_amendment_19.yaml` withdrew the Netherlands' 1960 towns, whose census volume came through a path
robots.txt disallows, so the Dutch rows of Lato-67, the 1977 staff-academy lessons and Soyuz-75 link to no town and
Soyuz-75, all of whose rows are Dutch, is no longer scored. It held every site with no recorded end year, and every
SAC base, at the centre of its 0.5-degree cell, which moves those sites by up to about 39 km and with them the
distance and count features, and it dropped two Czechoslovak headquarters rows whose only source refuses this project's agents. Every
classifier step and the map were run again; the run before it is kept in `runs/classifier/before_amendment_19/`. The
sealed set was not scored again. {verdicts_text}{sel_text}
"""


def _amendment_17() -> str:
    """The seventeenth amendment's paragraph: every primary verdict that moved between the run kept in
    before_amendment_17/ and the refit on the corrected links. Empty until that refit is committed."""
    after_17 = BEFORE_19 if (BEFORE_19 / "comparison.csv").exists() else OUT
    if not (BEFORE_17 / "comparison.csv").exists() or _table_of(BEFORE_17) == _table_of(after_17):
        return ""
    verdicts_text, sel_text = _moved(BEFORE_17, after_17)
    if sel_text.strip().startswith("Every scope selects the same model as before"):
        sel_text = sel_text.replace(
            "Every scope selects the same model as before, so the sealed and blind rows are of the models this "
            "refit selects, fitted on the earlier table.",
            "Again every scope selects the same model as before.",
        )
    return f"""
### Changed by the corrected Warsaw Pact links

`configs/protocol_amendment_17.yaml` corrected the links of two Polish exercise lists, Lato-67 (the Coastal Front
directive of exercise Lato, 1967) and Burza (the Maritime Front exercise of 1961). It placed Lato-67's five German offset
rows (51-55) at their printed offsets, which credits four towns: Walsrode (rows 51 and 52), Münster, Kevelaer and
Lobberich. It unlinked Burza's "south of Schleswig" and "north of Hamburg", which print a direction with no distance,
so Hamburg and Schleswig are no longer Burza positives. And it gave a reason for two Lato-67 rows that had been left
unlinked without one: row 17 (КЕЛЬ, read by the row's note as probably Kiel) and row 57 ("west of Lingen"), so Kiel
is not credited. Every classifier step and the map were run again on the corrected table; the run before it
is kept in `runs/classifier/before_amendment_17/`. The sealed set was not scored again. Before the amendment was
written, the committed held-out scores had been rescored (no model refitted) with five Lato-67 towns made positive,
one more than the links it adopted credit, and Lato-67's PR-AUC had been seen to rise, so a verdict it moves is not of
a reading fixed before its result was seen. {verdicts_text}{sel_text}
"""


def _cannot_blind() -> str:
    if not BLIND.exists():
        return ""
    prim = _blind_rows(PLUS)
    if prim["verdict"].eq("gain").any():
        return ""
    return (
        "- **A blind gain over population plus country.** On the only blind places, "
        f"{int(prim.iloc[0]['rows'])} towns of SAC's list, no selected model beat it by both intervals (Results, "
        '"The sealed set on blind places").'
    )


def _cannot_pooled() -> str:
    """A limit from the regularised identification check, if the columns name documents."""
    reg = pd.read_csv(IDENT / "regularised.csv").set_index("columns")
    if reg.at["all permitted", "over_largest_lo"] <= 0.10:
        return ""
    return (
        "- **A pooled gain as more than each document's base rate.** The columns name a row's document "
        f"{_pct(reg.at['all permitted', 'accuracy'])} of the time against {_pct(reg.at['all permitted', 'largest_document_share'])} "
        "for naming the largest, so a model fitted on pooled lists can learn which document a row belongs to "
        '(Results, "What the gains rest on").'
    )


# The classifier table every run used before the seventeenth amendment's link corrections.
TABLE_BEFORE_17 = "2aaafd623c1668e3464067d24346ea766e7a375033eb658fd1a31e5b5e152c41"


def _pending_17() -> str:
    """While the outputs are of the links before `configs/protocol_amendment_17.yaml`, say which links were wrong."""
    if json.loads((OUT / "manifest.json").read_text())["table_sha256"] != TABLE_BEFORE_17:
        return ""
    return """
**Known link errors in these results.** Every result here is of links that broke the rule stated for the smaller
lists. Lato-67's German offset rows ("5 km NW of Münster" and four more) were not placed and linked to no town,
while its Danish ones were; placed, they credit Walsrode, Münster, Kevelaer and Lobberich. Two Burza rows that print a
direction with no distance ("south of Schleswig", "north of Hamburg") were linked to those towns, though the same rule
left "south of Utrecht" unlinked. So Lato-67 lacks four positives and Burza has two it should not.
`configs/protocol_amendment_17.yaml`, committed before any refit, corrects them and fixes how the refit is read; the
refit is not yet committed."""


# The classifier table of every run before the nineteenth amendment (Dutch towns withdrawn, site coordinates of
# sites possibly in use today held at their 0.5-degree cell centres).
TABLE_BEFORE_19 = "2376ae4cda66262f164010ba12cf06e4ce578fdb205b313022f71d25c23fd2b3"


def _pending_19() -> str:
    """While the outputs are of the table before `configs/protocol_amendment_19.yaml`, say what it changes."""
    if json.loads((OUT / "manifest.json").read_text())["table_sha256"] != TABLE_BEFORE_19:
        return ""
    return """
**These results are of the table before the nineteenth amendment.** Its Dutch towns came from a census volume fetched
through a path the host's robots.txt disallows, and its site distances were computed from cited coordinates of sites
that may be in use today. `configs/protocol_amendment_19.yaml`, committed before any refit, withdraws the Dutch towns
(and the Netherlands from the 1965 map), holds every site with no recorded end year at the centre of its 0.5-degree
cell, drops two site rows whose only source refuses this project's agents, and fixes how the refit is read. The refit
is not yet committed."""


def _last_amendment() -> int:
    return max(
        int(p.stem.rsplit("_", 1)[1]) for p in (ROOT / "configs").glob("protocol_amendment_*.yaml")
    )


def _seal_sentence() -> str:
    """How many sealed places are blind: the card's sizes and the counts of the committed reading."""
    card = f"the {SEALED_PLACES} places of the sealed blocks, held out of every fit. An early check (two test models run before this classifier) had scored {EARLY_SCORED} of them before the blocks were drawn (`data/curated/splits/README.md`)."
    if not BLIND.exists():
        return card
    comp = pd.read_csv(BLIND)
    ns = comp[comp["population"].eq("never_scored") & comp["against"].eq(PLUS)].iloc[0]
    p0 = _blind_rows(PLUS).iloc[0]
    lost = int(ns["rows"]) - int(p0["rows"])
    return (
        f"{card} Of the other {AMENDMENT_11_SET}, committed outputs of earlier runs held scores for {lost} more, which the drawing of "
        f"the set missed (`data/curated/splits/scored_in_history.csv`). Of the remaining {AMENDMENT_11_SET - lost}, the "
        f"{int(p0['rows'])} with a SAC label are the **blind places**."
    )


def _msites() -> int:
    return sum(1 for _ in open(CURATED / "sac1956" / "msites.csv", encoding="utf-8")) - 1


def _further(n: int) -> str:
    return "One further document" if n == 1 else f"A further {n} documents"


def report() -> str:
    """REPORT.md, each paragraph and bullet filled to README's width, with one blank line between blocks."""
    return re.sub(r"\n{3,}", "\n\n", _wrap(_report_text()))


def _report_text() -> str:
    comp = pd.read_csv(OUT / "comparison.csv")
    selection = pd.read_csv(OUT / "selection.csv")
    lists = pd.read_csv(OUT / "lists.csv")
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    scopes = pd.read_csv(OUT / "scopes.csv").set_index("scope")
    fam = pd.read_csv(OUT / "family_gain.csv")
    defence = pd.read_csv(OUT / "defence.csv")
    cal = pd.read_csv(OUT / "calibration.csv")
    sens = pd.read_csv(OUT / "sensitivity.csv")
    su_pop = pd.read_csv(OUT / "ussr_population.csv")
    evidence = pd.read_csv(RUNS / "evidence" / "evidence_by_attacker.csv")
    primary = primary_table(comp, selection)
    v = verdicts(primary)
    pooled = "Warsaw Pact, pooled, exercise-based"

    def best(scope):
        return _best(selection, scope)

    def row(scope, holdout, model, against, which="all lists"):
        return _row(comp, scope, holdout, model, against, which)

    def pr(scope, holdout, plan, model):
        g = lists[
            (lists["scope"] == scope)
            & lists["holdout"].str.startswith(holdout)
            & (lists["plan_id"] == plan)
            & (lists["model"] == model)
        ]
        return f"{g['pr_auc'].iloc[0]:.2f}"

    def variant(scope, name):
        return sens[(sens["scope"] == scope) & (sens["variant"] == name)].iloc[0]

    def both(r):
        return f"{interval(r)}, by blocks {block_interval(r)}"

    sac_best = best(SAC_SCOPE)
    sac_sp = row(SAC_SCOPE, "spatial blocks", sac_best, PLUS)
    sac_strict = variant(SAC_SCOPE, "strict as-of")
    sac_flag = variant(SAC_SCOPE, "none flagged")
    g_best = best(GLOBAL_ALL)
    g_lopo = row(GLOBAL_ALL, "leave one document out", g_best, RULE)
    g_lopo_rest = row(GLOBAL_ALL, "leave one document out", g_best, RULE, "lists other than SAC")
    g_sp_rest = row(GLOBAL_ALL, "spatial blocks", g_best, PLUS, "lists other than SAC")
    g_rev = row(GLOBAL_ALL, "temporal reversed: fit after 1956, score earlier", g_best, RULE)
    wp_best = best(pooled)
    wp_lopo = row(pooled, "leave one document out", wp_best, PLUS)
    wp_kept = row(pooled, "leave one document out, towns kept in training", wp_best, PLUS)
    usr, us_gate, pl, cz = (gate.loc[k] for k in ("USSR", "US", "Poland", "Czechoslovakia"))
    pool = gate.loc[pooled]
    su_rows = int(evidence.loc[evidence["attacker"] == "USSR", "rows"].sum())
    su_train = evidence[(evidence["attacker"] == "USSR") & (evidence["role"] == "train")]
    plan_docs = evidence[evidence["doc_type"] == "war_plan"]
    disputed = evidence[evidence["doc_type"] == "disputed_plan_or_exercise"]
    su_pos = lists[
        (lists["scope"] == GLOBAL_ALL)
        & (lists["holdout"] == "spatial blocks")
        & lists["plan_id"].isin(["wp_1977_gsa_lessons", "wp_1977_gsa_front_lesson"])
        & (lists["model"] == RULE)
    ]["positives"].sum()
    sac_rate = float(sac_sp["base_rate"])
    coverage = pd.read_csv(OUT / "link_audit_coverage.csv").set_index("country_1956")
    dgz = pd.read_csv(OUT / "link_audit_dgz.csv").set_index("model")
    temporal_mix = pd.read_csv(OUT / "link_audit_temporal.csv")
    later = temporal_mix[temporal_mix["holdout"] == "scored by a fit before the cut"]
    later_pact = int(later.loc[later["side"] != "US", "positives"].sum())
    floor_table = pd.read_csv(OUT / "link_audit_floors.csv").set_index("country")
    floors, towns_of = floor_table["smallest_town"], floor_table["towns"]
    sub = (
        pd.read_csv(OUT / "link_audit_coverage_subcomplex.csv").set_index("country_1956").loc["all"]
    )
    every = coverage.loc["all"]
    war_docs = (
        lists[(lists["scope"] == GLOBAL_ALL) & (lists["doc_type"] == "war_plan")]
        .drop_duplicates("plan_id")
        .set_index("plan_id")
    )
    war_positives = int(war_docs["positives"].sum())
    verdict_gains = sorted(set(primary.loc[primary["Verdict"] == "gain", "Holdout"]))
    verdict_losses = sorted(set(primary.loc[primary["Verdict"] == "loss", "Holdout"]))
    same_sens = interval(sac_flag) == interval(sac_strict) and block_interval(
        sac_flag
    ) == block_interval(sac_strict)
    flagged_text = (
        f"Without the features flagged as today's data, and equally without the defence tables as well, the difference is {both(sac_flag)}: {claim(sac_flag)}."
        if same_sens
        else f"Without the features flagged as today's data the difference is {both(sac_flag)}: {claim(sac_flag)}. Also without the defence tables, {both(sac_strict)}: {claim(sac_strict)}."
    )
    rest_rate = float(g_sp_rest["base_rate"])

    def fam_row(rows, family):
        return fam[(fam["rows"] == rows) & (fam["family"] == family)].iloc[0]

    def odds(desc, feature):
        d = defence[
            defence["rows_described"].str.startswith(desc) & (defence["feature"] == feature)
        ].iloc[0]
        return f"{d['odds_ratio_per_tenfold']:.2f} [{d['low']:.2f}, {d['high']:.2f}]"

    cal_table = cal.groupby(["model", "kind"], as_index=False)[
        ["brier", "expected_calibration_error"]
    ].first()
    expected = lists[
        (lists["scope"] == GLOBAL_ALL) & lists["holdout"].str.startswith("expectation")
    ]
    apart = expected.pivot_table(
        index=["plan_id", "doc_type", "towns", "positives", "base_rate"],
        columns="model",
        values="pr_auc",
    ).reset_index()[["plan_id", "doc_type", "towns", "positives", "base_rate", RULE, g_best]]
    nearby = pd.read_csv(OUT / "block_neighbours.csv")
    air = pd.read_csv(OUT / "airfield_negatives.csv").set_index("towns")
    air_all, air_less = air.loc["all towns"], air.loc["negatives within 10 km left out"]
    fam_table = verdict_grid(fam, "family", "rows")
    sens_table = verdict_grid(sens, "scope", "variant")
    su_table = su_pop.assign(
        difference=su_pop.apply(interval, axis=1), by_blocks=su_pop.apply(block_interval, axis=1)
    )[
        [
            "model",
            "towns",
            "positives",
            "towns_without_1939",
            "pr_auc_1939",
            "pr_auc_1959",
            "difference",
            "by_blocks",
        ]
    ]

    aud = _audit()
    return f"""# What made a place a nuclear target? Report

Generated by `python -m nucprob.classifier.report` from `runs/classifier/` and `runs/probmap/`. Results
come from files there. Some figures describing the data come instead from the files that record it, each named where
it appears: the sizes of the sealed set (`data/curated/splits/README.md`), the transcription audit
(`data/curated/sac1956/README.md`), the West European site table (`data/curated/features/weurope_military_sites_1965.md`),
the second read of the Soviet search (`data/notes/second_read_2026-11b.md`) and the source register
(`data/sources.yaml`). List by list: `runs/classifier/TABLES.md`.

**How to read the numbers.** The main measure is PR-AUC, the area under the precision-recall curve: rank the
towns by score and ask how many of those near the top are on the list. A model with no information scores
the list's share of positives, its **base rate**, so a PR-AUC means nothing without it: SAC's list has a
base rate of {sac_rate:.2f}, the others together {rest_rate:.2f}. On a list that does not claim to be complete, a town off the
list is unlabeled, not a negative, so PR-AUC there understates true precision: read such figures against each other and
the base rate, not as how often a model is right. The classifier's intervals are 95% paired bootstrap intervals;
the map's (section "Probability map") are the 5th to 95th percentiles of its draws, so 90%. "By blocks" resamples whole
300 km squares of towns; the other interval resamples single towns. Verdicts use the unrounded bounds.

**How numbers are rounded.** Scores (PR-AUC, probabilities, shares) have two decimals; one that is not zero but would print as 0.00 takes a third (0.003), so that 0.00 means zero. A difference between two
scores and its interval bounds have three, so that a gain and its bounds print at the same precision in README,
here and in `runs/classifier/TABLES.md`. A difference within 0.0005 of zero prints as +0.000 or -0.000: the sign gives
the side of zero on which the unrounded value lies, and verdicts use the unrounded bounds. An exact zero prints as
0.000. Where an estimate would print equal to a bound it differs from, all three take a fourth decimal.

A comparison whose two scores never differ on its rows is shown as "constant". Where the positives lie in fewer than {MIN_POSITIVE_BLOCKS} blocks, resampling blocks measures nothing, and the block interval is shown as "n/a" with the count. In the tables, `a_pr_auc` is the PR-AUC of the model named in the row and `b_pr_auc` that of the score it is compared against; `by_blocks` is the block interval; `towns_without_1939` counts towns with no 1939 census figure; `cell_deg` is a map cell's side in degrees.

**Terms.** "Document" is the general word here: most of the lists are studies, exercises, lessons and a war
game, and few are war plans (see "How much evidence there is, by side"). "Leave one document out" is the holdout `configs/protocol.yaml` calls leave one plan out.
A **scope** is the set of documents a model is fitted on: all attacker documents, plan documents only, the pooled Warsaw Pact
documents, or SAC's 1956 study alone. SAC is the US Strategic Air Command, whose 1956 study supplies the largest list. The study
groups its targets into **complexes**, mostly a town and its surroundings, some of which hold named **subcomplexes** with their own
aim points and installations (`data/curated/sac1956/README.md`). COW is the Correlates of War project. In the `doc_type` column, `training` is a staff-academy lesson, `wargame` a war game and `mirror` one side's guess at the other's targets. "All permitted"
means every feature the protocol allows a model to read as of a document's date: population, administration, geography, the one
industry column, transport, military sites, defences and national power (`data/FEATURES_CLASSIFIER.md`). The **population rule** is a baseline: a
logistic regression on log population. The **state gate** is the rule deciding whether a state gets its own model. The **selection rule** decides which model is chosen. A
**sector box** (`data/curated/labels/SECTORS.yaml`) is the area a list covers: a town outside it is not a negative of that list.
The **sealed set** is the towns of the 300 km blocks in `data/curated/splits/sealed_blocks.csv`, kept out of every fit
and scored once at the end; its **blind places** are those no committed run had scored before then (Method).
**Burza** is the Polish front exercise of 1961 whose list is `wp_1961_burza`. A **theatre share** is the stated share of an attacker's
inventory assumed to be aimed at a scenario's countries. A **folded** ROC-AUC is the larger of the ROC-AUC and one minus it, so that
0.5 means no separation whichever way a feature points. **Pick-freeze** is the estimator of a first-order Sobol index: the share of a
quantity's variance that one input explains alone, from pairs of draws sharing that input. "Plan" alone means a document of a type the protocol counts as a plan (war plan, target selection,
requirements or policy study); "war plan" means that type only.

## Main result

{_main_lead()}

{_main_blind()}
- **Inside SAC's 1956 study**, under spatial cross-validation, {sac_best} scores {sac_sp["a_pr_auc"]:.2f} against {sac_sp["b_pr_auc"]:.2f}
  for population plus a country term: {both(sac_sp)}. {flagged_text}
  These repeats remove flagged columns, not every late input: see "Inputs later than the document" under Data.
- **On a document the model has not seen**, fitted on the other documents with that document's towns removed,
  {g_best} against the rule that ranks towns by population: {both(g_lopo)} over all lists, which SAC dominates, and
  {both(g_lopo_rest)} on lists other than SAC: {claim(g_lopo_rest)}.
- **Fitted on documents after 1956 and scoring earlier ones**: {both(g_rev)} against the population rule.
- **Verdicts in the primary table, against population plus country:** {v.get("gain", 0)} {WORDS["gain"]}, {v.get("loss", 0)} {WORDS["loss"]}, {v.get("neither", 0)} {WORDS["neither"]}, {v.get("not a reading", 0)} {WORDS["not a reading"]}. A gain or a
  loss needs both intervals to exclude zero. Gains appear under {_holdout_list(verdict_gains)}; losses under {_holdout_list(verdict_losses)}. A row with under {MIN_TRAIN_POSITIVES} positives in training, or a
  constant score, is not a reading.
{_main_divergence()}- **No state has its own model.** The US has {int(us_gate["linked_positives"])} linked positives, but only {int(us_gate["positives_outside_largest"])} outside the SAC study, and the state gate asks {_rule_outside()}.

## Question

Which traits of a place, as of a document's date, predict that the document designates it as a nuclear
target? And given that, what is the probability that an area is struck under a stated stockpile?

## Data

**Places.** Towns of the target country from censuses and yearbooks near the document. The floor differs
by source: 10,000 for most. China's universe is the cities (*shi*) of its 1953 census, {int(towns_of["China"])} towns from {int(floors["China"]):,} people.
North Korea, North Vietnam and Mongolia have only the UN's 1956 model estimates for cities of 300,000 or more today
(`data/curated/gazetteer/README.md`), so their universes are {int(towns_of["North Korea"])}, {int(towns_of["North Vietnam"])} and {int(towns_of["Mongolia"])} towns, the smallest of
{int(floors["North Korea"]):,}, {int(floors["North Vietnam"]):,} and {int(floors["Mongolia"]):,} people. These are the smallest towns held, not a published floor
(`runs/classifier/link_audit_floors.csv`, which counts the unsealed and sealed towns of the study). Soviet towns use the 1959 census for a June 1956 document, because no
town census exists between 1939 and 1959 (below). Western European towns use 1961 populations for documents up to
1977: stale, not later.

**Military and defence sites of 1965.** The West European site table (`data/curated/features/weurope_military_sites_1965.md`)
had 29 rows whose fact rested on general knowledge. Each was cited from a Wikipedia page fetched through a path robots.txt
allows, corrected to what that page states, or dropped (15 cited, 6 corrected, 8 dropped; 323 rows remain). Six fed
features: the NATO air-defence Control and Reporting Centre (CRC) at Glons is dated 1972 by its source and leaves 1965, CRC Semmerzake and the Belgian naval base at Ostend are
dropped, and Aviano is an air base, not a strike base, because no page found dates a strike role there in 1965.

**Inputs later than the document.** Removing the flagged columns does not remove all of these. The 1959 Soviet census is
in every population column. For the June 1956 document Hungary's towns are interpolated from the 1949 and 1960 censuses and
the Czech lands' from 1950 and 1961 (`data/curated/gazetteer/README.md`), and Kurchatov carries a 1990 figure
(`data/curated/gazetteer/closed_cities_1956.csv`). East Germany's and Poland's towns are interpolated with end-1956
figures, half a year after the document, which also set their 10,000 floor; Slovakia's with figures of 1 January 1958;
and North Korea's, North Vietnam's and Mongolia's towns are those the UN's 2018 estimates give 300,000 or more today,
so which towns enter there is chosen by later size. The Western European site table runs to 1966, and {_undated_sites()} undated sites it
holds as in role in 1965 also count for the documents of 1961 and 1964.

**Labels.** A positive is a town linked to a row the document designates (`selected = 1` in
`data/curated/labels/SCHEMA.md`). A rejected town, such as Tokyo in the Target Committee's list, is a negative. A town
named only in rows that neither designate nor reject it, such as areas "appropriate for study" or a
facility in the 1963 Joint Chiefs of Staff (JCS) vulnerability table, is left out of that list. SAC targets link to the nearest
town within 10 km, or up to 75 km if the name matches closely; other lists link within 15 km. A list that
concerns one sector keeps only that sector's towns (`data/curated/labels/SECTORS.yaml`). Some boxes follow a boundary a document states; the
others are derived from the list's own linked targets plus a fixed margin, because no boundary was read, and they say nothing about the plan's real scope. That file says which is which and gives a reason for each list
read over its whole universe. Corrected link errors are listed in
`configs/protocol_amendment_6.yaml`, `configs/protocol_amendment_7.yaml` and `configs/protocol_amendment_8.yaml`.

**Transcription.** SAC's lists, about nine positives in ten of what is trained on, were transcribed from the scan by two
independent passes of vision-language models (Claude agents), with disagreements resolved against the page
(`data/curated/sac1956/README.md`). A blind audit of a random 5% of rows, {aud["lines"]} lines, found {aud["wrong"]} errors in the final reading (95% interval 0 to {100 * aud["upper"]:.2f}%),
by auditors whose own error rate was 1.3%, so the audit's reading is itself uncertain. Of the 270 airfield rows that can be compared with a second printing, 216 lie on the low-resolution (about 200 dpi)
Part II pages, and on those the confirmed misread rate was 3 in 216, well above that bound.

**Links** lose entries too: {int(every["unlinked"])} of SAC's {int(every["entries"]):,} complex entries link to no town of the universe ({int(sub["unlinked"])} of its {int(sub["entries"])} subcomplex entries; `runs/classifier/link_audit_coverage_subcomplex.csv`), and the share varies by country: China {int(coverage.loc["China", "unlinked"])} of {int(coverage.loc["China", "entries"])}, North Korea {int(coverage.loc["North Korea", "unlinked"])} of {int(coverage.loc["North Korea", "entries"])}, North Vietnam {int(coverage.loc["North Vietnam", "unlinked"])} of {int(coverage.loc["North Vietnam", "entries"])}, Albania {int(coverage.loc["Albania", "unlinked"])} of {int(coverage.loc["Albania", "entries"])} (`runs/classifier/link_audit_coverage.csv`). These count entries, not towns. An entry whose cover name stands for a town and its closed city (Kapustin Yar and Znamensk, for example) links to both, so linked complex entries give {int(every["towns_linked"] - every["linked"])} more towns than their number, {_subcomplex_extra(int(sub["towns_linked"] - sub["linked"]))}
{_pending_17()}{_pending_19()}

**Documents.** `data/curated/labels/PLANS.yaml` records each list's attacker, author, date, type and evidence
grade. The grades: A, a primary document or its published translation read here; B, a primary document read here that names only part of the
targets it counts, or a later classified history quoting one; C, a scholar's table or paraphrase of an archive file not read here; D, journalism or an
encyclopedia; U, a text of unrecorded origin. D and U give no labels. The Canadian list of 1956 is U: its only source is an extract with no origin, date, page or hash, so it is not scored.
"Plan documents" below means war plans, target selections, requirements studies and policy studies at
grade C or better. Only `war_plan` documents are called war plans. SAC's 1956 list, the largest, is a
requirements study, not a war plan. Exercises, war games and lessons may enter models marked as such. Civil-defence
lists and mirrors record what a defender expected, never train a model, and are scored apart.

**How much evidence there is, by side.** The US has {int(us_gate["linked_positives"])} linked positives, of which
{int(us_gate["linked_positives"] - us_gate["positives_outside_largest"])} come from one document, and no document of type war plan.{_sac_sealed_gap()} For the USSR the registry holds **no war-plan document**: {su_rows}
rows, {int(su_train["rows"].sum())} of them from General Staff Academy lessons on one fictional scenario, giving {int(su_pos)} linked town-list pairs, and one
news report. Czechoslovakia has {int(cz["linked_positives"])} linked positives and Poland {int(pl["linked_positives"])}. The registry holds {int(plan_docs["documents"].sum())} war-plan documents with {int(plan_docs["rows"].sum())} rows between
them, all Warsaw Pact, with {war_positives} linked positives. **Only one was read at source**, the Czechoslovak plan of 1964 (grade A), and it has {int(war_docs.loc["wp_1964_csla_plan", "positives"])} linked positives: its rows that state nuclear weapons name units and
give no place, and the sentences that name places state no weapon. The two Polish Coastal Front plans for the Danish island of Zealand, of 1965 and 1977, are grade C, known here from a scholar's table and paraphrase of files not read. They share one author and one universe of towns, so "independent" here means separate
documents, not separate minds. {_further(int(disputed["documents"].sum()))} with {int(disputed["rows"].sum())} rows (Coastal Front map, 1970) {"has" if int(disputed["documents"].sum()) == 1 else "have"} a disputed status,
plan or exercise, and {"is" if int(disputed["documents"].sum()) == 1 else "are"} counted as neither. The searches recorded in `data/notes/` found no declassified Soviet strategic
target list; that does not show none exists.

**Features** (`data/FEATURES_CLASSIFIER.md`): population, administration, geography, industry (one column:
today's power plants by commissioning year), transport (rail, ports and rivers, and also airfield counts),
military sites, air and missile defences, and the target state's COW National Material Capabilities v7.0.
Several are today's data standing in for the past and are flagged. Sources, licences, dates and hashes are in
`data/sources.yaml`. The pages cited row by row in the site tables are registered apart, in `data/curated/features/cited_pages.csv`.

## Method

The analysis is fixed in `configs/protocol.yaml` and changed since only by dated amendments: four inside that file and
`configs/protocol_amendment_5.yaml` to `configs/protocol_amendment_{_last_amendment()}.yaml`. Each says what had already been read when it
was written; `configs/HISTORY.md` gives one line per amendment. **It is not blind.** Scores on SAC's spatial folds and
on the small lists, and later the full results, had been read before amendments corrected labels, links and sector
boxes. Burza's sector box was drawn after its effect on Burza's scores had been seen. The rule that a block interval needs
positives in {MIN_POSITIVE_BLOCKS} blocks was set after the row it changes had been seen (7 positives in 2 blocks, verdict "neither"
before and after; `configs/protocol_amendment_9.yaml`).

The one blind test uses the **sealed set**: {_seal_sentence()} Their labels are in the committed label files, so the
seal is a procedure and not a secret. {_sealed_status()}

- **Models.** Baselines: logistic regression on log population, and the same plus one intercept per
  country. Candidates: L2-penalised (ridge) logistic regression and LightGBM (gradient-boosted trees) with fixed settings. Nothing was tuned.
- **Positive-unlabeled.** On a list that does not claim to be complete, a town off it is unlabeled, not a
  negative. Each of 50 fits (**bags**) keeps all positives and draws as many unlabeled towns as the list has positives.
- **Holdouts.** Leave one document out (a document's lists and towns leave together); spatial blocks of 300 km in
  5 folds on three shifted grids; temporal, in both directions around 1956, splitting documents by date only, so a town
  listed in both periods is in both the fit and the scored rows (`configs/protocol.yaml`, holdouts). Spatial folds have no buffer: on the first grid
  {nearby.iloc[0]["within_25km"]:.0%} of held-out rows have a training town within 25 km and {nearby.iloc[0]["within_50km"]:.0%} within 50 km (`runs/classifier/block_neighbours.csv`).
- **Reading.** Mean per-list PR-AUC, weighted by positives, on lists with 2 or more. Neither interval includes
  the variance of refitting a model.
{_fit_check()}
- **Which model.** Each scope's candidate was chosen on spatial blocks alone, and the spatial differences below are read on the same rows, so
  they are optimistic by the choice between two candidates. The left-out and temporal rows are not read where the model was chosen. The protocol's "nothing is chosen on a held-out set" concerns model settings.

## Results

### Models against baselines

The selected candidate of each scope. "Trained on" is the smallest number of positives in any fit behind the row, over every grid and fold.
"Difference, country" is the model against population plus country; "Difference, rule" against the population rule. Rows marked "not a reading" are shown and not counted. "Seeds 1-20" gives the verdicts against population plus country under twenty other bootstrap seeds (below).
**The temporal rows also change attacker:** {later_pact} of the {int(later["positives"].sum())} positives dated after 1956 are on Warsaw Pact or Soviet-lesson lists, and the rest on lists too small to score ({_unscored_note(lists)}), so "fit to 1956, score later" tests a US study against the other side's lists, and era and attacker cannot be told apart (`runs/classifier/link_audit_temporal.csv`).

{markdown(with_seeds(primary))}

{seed_section()}

- **The pooled Warsaw Pact model** has {int(pool["linked_positives"])} positives across {int(scopes.loc[pooled, "lists"])} lists, mostly exercises and lessons; it is never a war-plan model.
- **Keeping a left-out document's towns in training**, as the earlier run did, lets a town bring its label from another document
  into the fit. For the pooled Warsaw Pact model it gives {both(wp_kept)}, against the {both(wp_lopo)} in the table with them removed.
- **SAC itself**, left out of the global model: {pr(GLOBAL_ALL, "leave", SAC, g_best)} under {g_best}, {pr(GLOBAL_ALL, "leave", SAC, RULE)} for the population rule, on a base rate of {sac_rate:.2f}.
- **Target Committee of 1945**, its designated cities, left out: {pr(GLOBAL_ALL, "leave", "us_1945_target_committee", g_best)} under {g_best}, {pr(GLOBAL_ALL, "leave", "us_1945_target_committee", RULE)} for the population rule.

{_blind_section()}
{_sealed_section()}
{_amendment_16()}{_amendment_17()}{_amendment_19()}
### What the gains rest on

Each scope's selected candidate against population plus country under spatial blocks, with columns removed.
"None flagged" removes today's data standing in for the past. "Strict as-of" also removes the defence tables, mostly
post-Soviet knowledge. "No national power" removes COW's values, which take one value per country and year and so
were suspected of marking a document. "No source markers" also removes the defence and military columns, which are
blank or filled according to the table a row came from. {_identification()}

Each cell is the difference in PR-AUC and its verdict: a gain or a loss needs both intervals, spatial and by blocks, to
exclude zero. The intervals are in `runs/classifier/TABLES.md` ("What the gains rest on, every row").

{markdown(sens_table)}

**SAC's negatives beside its own airfields.** SAC's town list is complete, but it lists airfields apart, so a town off it may lie beside a
listed airfield. {int(air_all["negatives_within_5km"])} of its {int(air_all["negatives"])} negatives lie within 5 km of one and {int(air_all["negatives_within_10km"])} within 10 km. Without those within 10 km the SAC gain above is {both(air_less)}, against {both(air_all)} with them.

**SAC's negatives holding an aim point.** {int(dgz.loc["logistic, all permitted", "negatives_with_a_dgz_point"])} unsealed negatives have a designated ground zero point, a printed aim point of the study, as their nearest entry, so "complete" overstates how cleanly the town list marks what SAC would strike. Counting them as positive changes PR-AUC, without refitting, by {signed(dgz.loc["logistic, all permitted", "pr_auc_counted_positive"] - dgz.loc["logistic, all permitted", "pr_auc_as_labelled"])} for the logistic ({dgz.loc["logistic, all permitted", "pr_auc_as_labelled"]:.2f} as labelled) and by {signed(dgz.loc["population + country", "pr_auc_counted_positive"] - dgz.loc["population + country", "pr_auc_as_labelled"])} for population plus country ({dgz.loc["population + country", "pr_auc_as_labelled"]:.2f}) (`runs/classifier/link_audit_dgz.csv`). They stay negatives: the document lists them under no town entry.

**Soviet population.** The USSR's rows use the 1959 census, later than the June 1956 document, in every baseline too. Repeating
Soviet towns on the 1939 census, earlier than the document and missing for towns founded after it, gives:

{markdown(su_table)}

### Which families add anything (US 1956 complexes)

Each family with population and country, LightGBM, spatial blocks, one bag per fit rather than 50. A gain needs both intervals to exclude zero, as everywhere. Airfield counts are in transport, not
military, and industry is the single power-plant column, so a zero there says little about industry. Over a country term national
power can add nothing within one list; over population alone it does the country term's work. Transport here is
largely today's data. Each cell is the gain over the base (population and country, or population alone where the
row says so) and its verdict; the intervals are in `runs/classifier/TABLES.md` ("Feature families, US 1956 complexes").

{markdown(fam_table)}

### Economic and political data

{_extended_section()}
### Defences

These are associations in the lists, not findings about intent. Odds ratios are per tenfold increase in the
feature, controlling log population and an intercept per list and country; intervals bootstrap places.

- **Soviet towns on the SAC list.** Adding the defence family gives {interval(fam_row("USSR", "defence"))}, by blocks {block_interval(fam_row("USSR", "defence"))}: {fam_row("USSR", "defence")["verdict"]}. Sites within 50 km: {odds("US 1956", "log_air_defence_sites_50km")}.
  Distance to an S-25 Moscow-ring missile site: {odds("US 1956", "log_km_to_sam")}. Distance to any defence site: {odds("US 1956", "log_km_to_air_defence")}, and
  without the S-25 points {odds("US 1956", "log_km_to_air_defence_no_s25")}.
- **This does not show that SAC avoided defended places.** The S-25 ring surrounds Moscow, so nearby small towns
  may be absorbed into its complex entry rather than listed by name, and air-defence sites may follow large cities.
  The table is not what SAC knew: the S-25 points, from Michael Holm's web pages on Soviet units, carry US designations, while the rest is post-Soviet knowledge.
- **Warsaw Pact documents, NATO Europe.** Sites within 50 km {odds("Warsaw Pact", "log_air_defence_sites_50km")}, distance to a US surface-to-air missile site (Nike, HAWK) {odds("Warsaw Pact", "log_km_to_sam")}.
- **Defences as targets in themselves.** Some documents name them. Counts of rows or complexes, from the documents' own
  words (`runs/classifier/defence_targets.csv`); the plans' order of strikes is not read here. The Warsaw Pact documents' shares are a finding about
  those few lists. {_defence_summary()} In SAC's Moscow region {_msites()} rows are numbered "M-n"; the study does not say what M means, so they are not counted.

{markdown(pd.read_csv(OUT / "defence_targets.csv").drop(columns=["counted"]))}

### Calibration

On the SAC list under spatial blocks, with isotonic calibration (a monotone remapping of scores to observed shares) fitted on other folds.
SAC's selected model is {sac_best}, and the map uses the population rule. Calibration cannot be measured on incomplete lists, and
no calibration measured on SAC carries to another document's base rate. {_calibration_terms(cal_table, float(sac_sp["base_rate"]))}

{markdown(cal_table.rename(columns={"expected_calibration_error": "ECE"}))}

### Lists scored apart

Civil-defence lists and mirrors record what a defender expected, so they never train a model. Each is scored here by the global model's fit on all attacker
documents. The two NATO mirrors are Warsaw Pact exercise documents' pictures of NATO's targets. A high score says only that defenders expected
large towns to be hit too.

{markdown(apart)}

### Other metrics

The protocol's secondary metrics (Brier; log-loss, the mean of minus the log of the score given to each town's true
label; precision at k, the share of listed towns among the k highest scored) for every scope and holdout are in
`runs/classifier/TABLES.md`. Brier and log-loss there are on raw scores, which are not probabilities where a list
is incomplete.

## Probability map

{_map_section()}
## What the evidence cannot support

- **Any statement about Soviet war plans.** The USSR is refused its own model: {usr["reason"]}. The Soviet rows that are used come from General Staff Academy lessons and Warsaw Pact exercises, and say what those taught or rehearsed.
- **That SAC's list is free of error.** See how it was transcribed, under Data, and `data/ISSUES.md` for what has been corrected.
- **A state's own model.** Each state is refused. A model of Warsaw Pact war plans in particular has no basis: {war_positives} linked positives, none from a plan read at source. The pooled model is exercise-based.
- **Prediction for a plan not in the data.** See the main result. The map's score carries this limit into every cell.
{_cannot_blind()}
{_cannot_pooled()}
- **Causes.** These are associations between a town's traits and its presence on a list. No design here separates one trait's effect from another's or from the planners' reasons.
- **What planners knew.** Features record what existed according to later sources.
- **Any statement about a present-day plan.** Modern map rows extrapolate from lists of 1945 to 1977.

## State models refused or allowed

The state rows follow the state gate in `configs/protocol.yaml`. The last row is not a state: the pooled Warsaw Pact model has its own rule, which needs no independent plan because
it is labelled exercise-based and never read as a war-plan model, so it can show 0 independent plans and still meet its rule.

{markdown(gate.reset_index().drop(columns=["documents_any_type"]))}

"Independent plans" counts separate documents of a plan type at grade C or better with at
least one linked positive: the US's come to policy and requirements studies and a target selection, none a war plan.
`linked_positives` and `positives_outside_largest` count positives in those plan-type documents only, which is why
the USSR shows 0: its town-list pairs come from staff-academy lessons, which the gate does not count as plans.

## Not done

{_sealed_not_done()}{_not_held()}
- Rows of the 1970 Coastal Front map beyond the four kept (`data/notes/soviet_search_2026-11.md`), and 69 mirror candidates
  from a 1963 Polish exercise and one lesson, 65 of them map symbols with no text to quote, are not labels
  (`data/notes/second_read_2026-11b.md`). Of the 27 lesson candidates in the same search, which found no new war plan
  naming places, 25 passed a second read of the scan and are labels.
"""


README_START = "<!-- results: generated by python -m nucprob.classifier.report -->"
README_END = "<!-- end of results -->"

# How a feature family reads in README's answer to its first question, in the order README gives them: families
# measured as of the document first, then the two that rest on today's data (data/FEATURES_CLASSIFIER.md).
FAMILY_WORDS = {
    "military": "military sites of the document's date",
    "geography": "geography (elevation, relief, distance to the coast)",
    "defence": "air and missile defence sites of the document's date",
    "administration": "administrative status (capital, regional centre, distance to the capital)",
    "national_power over population": "national power (the Correlates of War project's (COW) National Material Capabilities) over population alone",
    "national_power": "national power over population and country",
    "transport": "transport (railways, ports, airfields; largely today's data)",
    "industry": "industry (one column, today's power plants)",
}
TODAYS_FAMILIES = ("transport", "industry")
README_WIDTH = 118


def _wrap(text: str, width: int = README_WIDTH) -> str:
    """Reflow generated markdown: each paragraph or bullet is joined and filled to `width`, keeping its indent
    (and a bullet's hanging indent). Table rows, headings and blank lines are kept as they are. A line indented
    past a bullet's text, or starting a new bullet, starts a new block."""
    out: list[str] = []
    block: list[str] = []
    lead = hang = ""

    def flush() -> None:
        if block:
            out.append(
                textwrap.fill(
                    " ".join(block),
                    width=width,
                    initial_indent=lead,
                    subsequent_indent=hang,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
            block.clear()

    for line in text.split("\n"):
        body = line.lstrip(" ")
        indent = line[: len(line) - len(body)]
        if not body or body.startswith(("|", "#")):
            flush()
            out.append(line)
            continue
        if block and not body.startswith("- ") and indent == hang:
            block.append(body)
            continue
        flush()
        lead = indent
        hang = indent + ("  " if body.startswith("- ") else "")
        block.append(body)
    flush()
    return "\n".join(out)


def _odds_50km() -> str:
    d = pd.read_csv(OUT / "defence.csv")
    d = d[
        d["rows_described"].str.startswith("US 1956")
        & (d["feature"] == "log_air_defence_sites_50km")
    ].iloc[0]
    return f"{d['odds_ratio_per_tenfold']:.2f} [{d['low']:.2f}, {d['high']:.2f}]"


def _sac_base_rate() -> float:
    comp = pd.read_csv(OUT / "comparison.csv")
    return float(
        _row(
            comp,
            SAC_SCOPE,
            "spatial blocks",
            _best(pd.read_csv(OUT / "selection.csv"), SAC_SCOPE),
            PLUS,
        )["base_rate"]
    )


def _families() -> pd.DataFrame:
    fam = pd.read_csv(OUT / "family_gain.csv")
    fam["verdict"] = fam.apply(lambda r: "constant" if constant(r) else r["verdict"], axis=1)
    return fam


def family_cell(r) -> str:
    """One cell of README's family table: estimate, both intervals and verdict."""
    if constant(r):
        return "constant on these towns"
    return f"{interval(r)}, by blocks {block_interval(r)}: {r['verdict']}"


def _readme_families() -> str:
    """README's answer to "what made a place a target": the feature-family reading of SAC's list, as a table."""
    fam = _families()
    base = fam[(fam["rows"] == "all countries") & (fam["base"] == "base")].iloc[0]
    su = fam[(fam["rows"] == "USSR") & (fam["base"] == "base")].iloc[0]
    pop = fam[(fam["rows"] == "all countries") & (fam["base"] == "population only")].iloc[0]
    gains = fam[fam["verdict"] == "gain"]
    near = gains[gains["block_low"] < NEAR_ZERO]
    near_text = ", ".join(
        f"{r.family} ({r.rows}, {signed(r.block_low)})" for r in near.itertuples()
    )
    cell = {(r["rows"], r["family"]): family_cell(r) for _, r in fam.iterrows()}
    rows = "\n".join(
        f"| {words} | {cell[('all countries', f)]} | {cell[('USSR', f)]} |"
        for f, words in FAMILY_WORDS.items()
    )
    return f"""- **What the lists favour beyond population, on SAC's 1956 study alone.** The table adds each family of
  features, one at a time, to a LightGBM fit on log population and a country term (spatial blocks, one bag per fit),
  which scores {base["base_pr_auc"]:.2f} on all countries ({su["base_pr_auc"]:.2f} on Soviet towns alone). That fit is not the population rule: it is a fitted model
  that may bend population's effect, and the population rule, a plain ranking by population, scores {_sac_rule()["b_pr_auc"]:.2f} on the
  same rows. Families measured as of the document come first. "National power over population alone" is added to a
  fit on log population with no country term ({pop["base_pr_auc"]:.2f}), so it can only do what the country term does.

| Family added | All countries | Soviet towns only |
|---|---|---|
{rows}

  Each gain is at most {gains["delta"].max():.3f} of PR-AUC. These are associations within one requirements study,
  not causes and not a reading on any other document. A family that gains helps rank towns; it does not say in
  which direction. For defences: listed Soviet towns had fewer defence sites within 50 km than log population and
  country predict (odds ratio per tenfold {_odds_50km()}); REPORT ("Defences") gives why this does not show that SAC
  avoided defended places. {len(near)} of the {len(gains)} gains have a block lower bound under {NEAR_ZERO} ({near_text}),
  and none of these readings was repeated under other bootstrap seeds, since the family fits' scores are not kept.
  Intervals: `runs/classifier/family_gain.csv`.
"""


def _sac_rule(against: str = RULE):
    """The selected SAC model against a baseline under spatial blocks: its b_pr_auc is the baseline's PR-AUC."""
    return _row(
        pd.read_csv(OUT / "comparison.csv"),
        SAC_SCOPE,
        "spatial blocks",
        _best(pd.read_csv(OUT / "selection.csv"), SAC_SCOPE),
        against,
    )


def _readme_short() -> str:
    """README's plain answers to its two questions, from the committed outputs."""
    fam = _families()
    rule, plus = _sac_rule(RULE), _sac_rule(PLUS)
    gains = fam[fam["verdict"] == "gain"]
    dated = gains[~gains["family"].isin(TODAYS_FAMILIES) & gains["base"].eq("base")]
    dated_names = [f for f in FAMILY_WORDS if f in set(dated["family"])]
    words = {
        "military": "military sites",
        "geography": "geography",
        "defence": "air and missile defence sites",
        "administration": "administrative status",
    }
    named = [words.get(f, f) for f in dated_names]
    named_text = ", ".join(named[:-1]) + " and " + named[-1] if len(named) > 1 else "".join(named)
    sens = pd.read_csv(OUT / "sensitivity.csv")
    clean = sens[(sens["scope"] == SAC_SCOPE) & (sens["variant"] == "none flagged")].iloc[0]
    strict = sens[(sens["scope"] == SAC_SCOPE) & (sens["variant"] == "strict as-of")].iloc[0]
    blind = _blind_rows(PLUS) if BLIND.exists() else None
    blind_text = (
        " On the one blind test, places no run had scored, no model beat population plus country."
        if blind is not None and not blind["verdict"].eq("gain").any()
        else ""
    )
    scen = pd.read_csv(MAP / "scenarios.csv").set_index("scenario")
    val = pd.read_csv(MAP / "validation.csv").set_index("reading").loc["spatial blocks held out"]

    def over(name: str) -> str:
        r = scen.loc[name]
        return (
            f"{count(r['cells_over_half_median'])} [{count(r['cells_over_half_low'])}, "
            f"{count(r['cells_over_half_high'])}] of {count(r['cells'])}"
        )

    return f"""### Short answers

**What made a place a target?** The lists show what listed towns had in common, not why they were chosen. On the
one large list, SAC's 1956 study of the Soviet bloc, a listed town stood out mostly by its size. Under spatial
cross-validation, ranking towns by population alone (the population rule) gives a PR-AUC of {rule["b_pr_auc"]:.2f} where a
ranking with no information gives {_sac_base_rate():.2f}; population plus a term for each country gives {plus["b_pr_auc"]:.2f}, and the selected
model with every permitted feature {plus["a_pr_auc"]:.2f} ({interval(plus)} over population plus country, by blocks
{block_interval(plus)}).{seed_note(plus)} Added one at a time to a fit on population and country, no family of town traits adds
more than {gains["delta"].max():.3f}. Of the families that describe the towns as of 1956, {named_text} add {dated["delta"].min():.3f} to
{dated["delta"].max():.3f} each where they gain. The defence sites are known mostly from post-Soviet sources: they record what
existed in 1956, not what SAC knew. Transport adds the most but rests largely on today's data. {_short_repeats(clean, strict)} Those repeats still use the 1959 Soviet census and other late inputs (REPORT, "Inputs later than the
document"), and the analysis is not blind: earlier results had been read (REPORT, Method). None of this has been
shown to carry over to a document the models did not see.{blind_text}

**How likely is an area to be struck?** Only under stated assumptions, and only as a historical illustration. If the
cited US stockpile of 1956 were sent against the Soviet bloc and each delivered warhead fell on a town in proportion
to the map's score, {over("us_1956_on_bloc")} half-degree cells would have a probability over one half of
receiving at least one warhead; with the 1950 stockpile, {over("us_1950_stock_on_bloc")}. The brackets are the 5th to
95th percentiles of {N_DRAWS} draws, so 90% intervals. Most of their width comes from the stockpile and from the share of each force
assumed sent to the theatre, which has no source. Against SAC's own list, with spatial blocks held out, the 1956 map
ranks the cells that hold a listed town at PR-AUC {val["pr_auc"]:.2f} where {val["base_rate"]:.0%} of cells hold one, and its mean cell
probability is {val["mean_p"]:.2f}. The score was fitted on these lists, so this is agreement with the training list, not a
test. Present-day scenarios apply lists of 1945-1977 to today's towns:
they are extrapolation, with no label to test them.

### Results in brief

"""


def _readme_pending_19() -> str:
    if not _pending_19():
        return ""
    return (
        "**Pending refit.** Every figure below is of the table before `configs/protocol_amendment_19.yaml`, which "
        "withdraws the Dutch towns (their census volume came through a path robots.txt disallows) and holds sites "
        "possibly in use today at their 0.5-degree cell centres. REPORT, Data, says more.\n\n"
    )


def readme_results() -> str:
    """What README.md says of the results, so that a figure there cannot drift from the outputs."""
    comp = pd.read_csv(OUT / "comparison.csv")
    selection = pd.read_csv(OUT / "selection.csv")
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    sac_best, g_best = _best(selection, SAC_SCOPE), _best(selection, GLOBAL_ALL)
    sac = _row(comp, SAC_SCOPE, "spatial blocks", sac_best, PLUS)
    lopo = _row(comp, GLOBAL_ALL, "leave one document out", g_best, RULE)
    rest = _row(comp, GLOBAL_ALL, "leave one document out", g_best, RULE, "lists other than SAC")
    us = gate.loc["US"]
    lists = pd.read_csv(OUT / "lists.csv")
    su_pos = lists[
        (lists["scope"] == GLOBAL_ALL)
        & (lists["holdout"] == "spatial blocks")
        & lists["plan_id"].isin(["wp_1977_gsa_lessons", "wp_1977_gsa_front_lesson"])
        & (lists["model"] == RULE)
    ]["positives"].sum()
    ext = pd.read_csv(OUT / "extended.csv")
    ext = ext[~(ext["scope"].str.startswith("Warsaw") & ext["lists"].eq("other than SAC"))]
    held = ext[(ext["holdout"] == "leave one document out") & (ext["verdict"] != "not a reading")]
    rest_ext = held[held["lists"] == "other than SAC"]
    glob = held[(held["scope"] == GLOBAL_ALL) & (held["lists"] == "all lists")]
    vpk = ext[ext["comparison"] == "defence industry over population"].iloc[0]
    spread = pd.read_csv(MAP / "score_spread.csv").set_index("scenario").loc["us_1956_on_bloc"]
    shift = pd.read_csv(MAP / "domain_shift.csv")
    log_pop = shift[shift["comparison"].str.endswith(": log_pop")].iloc[0]
    other = _row(comp, GLOBAL_ALL, "spatial blocks", g_best, PLUS, "lists other than SAC")
    scen = pd.read_csv(MAP / "scenarios.csv")
    terms = f"""**Terms.** Spatial cross-validation cuts the map into 300 km squares, deals them into 5 folds, and scores each
fold's towns with a model fitted on the other four; it is done on three shifted grids and a town's score is the mean. PR-AUC, the area under the precision-recall curve, measures how many of a model's top-ranked towns are on a
list. A list's base rate is what no information scores: {float(sac["base_rate"]):.2f} for SAC, {float(other["base_rate"]):.2f} for the other lists.
Where a list is incomplete a town off it is unlabeled, so PR-AUC understates precision there. The classifier's
intervals are 95%, the first resampling towns and "by blocks" resampling 300 km squares; a difference counts only if
both exclude zero. Differences have three decimals; one printed +0.000 or -0.000 lies within 0.0005 of zero on that
side. A **scope** is the set of lists a model is fitted on: two global scopes (every attacker's documents, or plan
documents only), a pooled Warsaw Pact scope, and SAC's 1956 study alone. A **linked positive** is a listed place
matched to a town of the place universe. The **population rule** ranks towns by population alone; **population plus
country** adds a term for each target country."""
    short = _readme_short()
    short_head, short_rest = short.split("\n", 1)
    text = f"""{_readme_pending_19()}{short_head}\n\n{terms}\n{short_rest}{_readme_blind()}{_readme_families()}- **On lists other than SAC's**, under the same spatial cross-validation, the global model on all attacker documents
  (exercises included) against population plus country is {interval(other)}, by blocks {block_interval(other)}: {claim(other)}.{seed_note(other)}
  {_other_lists_basis(lists, other, g_best)} The held-out blocks' documents are also in training, so this is not a
  reading on an unseen document (next point).
- **On a document the model has not seen**, the richer model against ranking towns by population is {interval(lopo)},
  by blocks {block_interval(lopo)} over all lists, which SAC dominates.{seed_note(lopo)} On lists other than SAC it is {interval(rest)},
  by blocks {block_interval(rest)}: {claim(rest)}.{seed_note(rest)} So no model has been shown to do better than population on
  an unseen document.
{_readme_seeds()}- **No state gets its own model.** The US has {int(us["linked_positives"])} linked positives, but only {int(us["positives_outside_largest"])} outside one document and
  the pre-committed gate asks for {_rule_outside()}. The USSR has 0 positives in a document registered as a war plan, and
  {int(su_pos)} town-list pairs from staff-academy lessons. A pooled Warsaw Pact model is allowed and is always labelled
  exercise-based. Refusals: `runs/classifier/state_gate.csv`.
- **Economic and political data** (regime, defence pacts, GDP per capita, Soviet defence plants), read apart under
  an amendment committed before fitting: on a left-out document {int((rest_ext["verdict"] == "gain").sum())} of the {len(rest_ext)} rows on lists other than SAC
  gain. The highest of these models over all lists, picked after the fact and with no paired interval fixed in
  advance, scores {glob["a_pr_auc"].max():.2f} against {lopo["b_pr_auc"]:.2f} for the population rule. Plant counts add {interval(vpk)} on
  Soviet towns.
- **The map's score.** Because of the transfer result above, the pre-committed selection rule (highest PR-AUC on a
  left-out document) chose population as the score. On the 1956 towns the score moves only
  {spread["score_ratio"]:.1f}-fold over a {spread["population_ratio"]:.0f}-fold range of population, so a cell's probability also depends on how
  many towns it holds. {_readme_width(scen)} {_readme_1965()} Modern scenarios use Natural Earth's map-label towns. A
  classifier told them from the training towns at ROC-AUC {shift.iloc[0]["value"]:.2f} (ROC-AUC: the chance that it ranks a random
  modern town above a random training town; 0.5 would mean no shift) on {_shift_features(shift)} features both sets have
  (population, its rank, population within 25-100 km, distances to a town of 100,000, the capital and the coast,
  capital and regional-centre status), with {log_pop["value"]:.0%} outside the training's 1st-99th percentile on the
  one feature the score reads."""
    return _wrap(text)


def _readme_seeds() -> str:
    """README's line on the repeat of the primary comparisons under other bootstrap seeds."""
    s = seed_summary()
    if s is None:
        return "- **Bootstrap seed.** The repeat of the primary comparisons under other seeds has not been run.\n"
    s = seed_distinct(s)
    moved = s[~s["seed_stable"].astype(bool)]
    tail = (
        f' The {len(moved)} that do not are listed in REPORT ("Bootstrap seed") and are not read as findings '
        "either way; a reading above that is one of them says so."
        if len(moved)
        else ""
    )
    return f"""- **Bootstrap seed.** The bootstrap resamples are drawn with one fixed seed, the number 1956 (not the document year). Every primary
  comparison was repeated under seeds 1 to 20 with nothing refitted: {len(s) - len(moved)} of {len(s)} keep their verdict under all 20.{tail}
"""


# How the doc_type values of PLANS.yaml read in prose, for the README's account of what a reading rests on.
NOT_PLAN_TYPES = {
    "exercise": "exercises",
    "training": "staff-academy lessons",
    "wargame": "a war game",
    "disputed_plan_or_exercise": "the disputed 1970 map",
}


def _other_lists_basis(lists: pd.DataFrame, other, model: str) -> str:
    """What the global reading on lists other than SAC's rests on: its positives by document type, from
    lists.csv, and its verdict before the corrected Warsaw Pact links, which were adopted after one exercise
    list had been rescored with them."""
    rows = lists[
        (lists["scope"] == GLOBAL_ALL)
        & (lists["holdout"] == "spatial blocks")
        & (lists["model"] == RULE)
        & (lists["plan_id"] != "us_1956_sac_complexes")
    ]
    by_type = rows.groupby("doc_type")["positives"].sum()
    total = int(by_type.sum())
    not_plan = {t: int(by_type.get(t, 0)) for t in NOT_PLAN_TYPES}
    named = [f"{NOT_PLAN_TYPES[t]} ({n})" for t, n in not_plan.items() if n]
    parts = ", ".join(named[:-1]) + " and " + named[-1] if len(named) > 1 else "".join(named)
    war = int(by_type.get("war_plan", 0))
    rest = total - sum(not_plan.values()) - war
    text = (
        f"Of its {total} positives, {sum(not_plan.values())} come from Warsaw Pact {parts}; {war} come from documents "
        f"registered as war plans and {rest} from US target-selection and policy studies. It is mostly a reading "
        "on exercises and lessons, not on war plans."
    )
    if (BEFORE_17 / "comparison.csv").exists():
        was = _row(
            pd.read_csv(BEFORE_17 / "comparison.csv"),
            GLOBAL_ALL,
            "spatial blocks",
            model,
            PLUS,
            "lists other than SAC",
        )
        if verdict(was) != verdict(other):
            text += (
                f" Without the corrected links of two Polish exercise lists it is {verdict(was)} "
                f"({interval(was)}, by blocks {block_interval(was)}), and those corrections were adopted after one "
                "of the two lists had been rescored with them, so this verdict was not fixed before its result was "
                'seen (REPORT, "Changed by the corrected Warsaw Pact links").'
            )
    return text


def _shift_features(shift: pd.DataFrame) -> int:
    """The features the domain-shift classifier reads: those domain_shift.csv gives a percentile share for."""
    prefix = "modern towns outside the 1st-99th percentile of training: "
    rows = shift["comparison"][shift["comparison"].str.startswith(prefix)]
    return rows.str.removeprefix(prefix).nunique()


def _readme_blind() -> str:
    """The blind reading of the sealed set, the one test of places no run had scored, from its outputs."""
    if not BLIND.exists():
        return ""
    prim, rule = _blind_rows(PLUS), _blind_rows(RULE)
    p0 = prim.iloc[0]
    gains = prim[prim["verdict"].eq("gain")]
    rule_gains = rule[rule["verdict"].eq("gain")]
    first = (
        "no model beats population plus country"
        if gains.empty
        else f"{len(gains)} of {len(prim)} models beat population plus country by both intervals"
    )
    earlier = pd.read_csv(SEALED.parent / "comparison.csv")
    earlier = earlier[earlier["primary"]]
    lines = "".join(
        f"  - {r.scope}: {interval(r._asdict())}, by blocks [{signed(r.block_low)}, {signed(r.block_high)}]: "
        f"{r.verdict}{_rule_note(r.scope)}\n"
        for r in prim.itertuples()
    )
    rule_text = (
        ": "
        + "; ".join(
            f"{r.scope} {interval(r._asdict())}, by blocks [{signed(r.block_low)}, {signed(r.block_high)}]"
            for r in rule_gains.itertuples()
        )
        if len(rule_gains)
        else ""
    )
    return f"""- **On the only blind test**, {first}. The **sealed set** is the {SEALED_PLACES} towns of 300 km blocks kept out
  of every fit and scored once at the end; {int(pd.read_csv(BLIND)["rows"].max())} of them have a SAC label and are scored against SAC's list,
  and {int(p0["rows"])} of those had been scored by no earlier run ({int(p0["positives"])} listed). Against population plus country there:
{lines}  Against the population rule, {len(rule_gains)} of {len(rule)} gain by both intervals{rule_text}. Positives lie in only
  {int(p0["positive_blocks"])} of {int(p0["blocks"])} blocks, so these intervals are wide and "neither" is not evidence of no effect.
- **The whole sealed set is not a blind test.** On {int(earlier.iloc[0]["rows"])} sealed places, including ones earlier runs had scored,
  {int(earlier["verdict"].eq("gain").sum())} of {len(earlier)} models gained over population plus country. Which sealed places count as blind was decided
  after that reading had been seen, and the set may be read once, so only the protocol's bootstrap seed was used
  (`runs/classifier/sealed/blind/comparison.csv`; REPORT, "The sealed set").
"""


def _readme_width(s: pd.DataFrame) -> str:
    """Which part of the map's intervals is wider, from scenarios.csv."""
    stock = (s["mean_width_stockpile_only"] > s["mean_width_model_only"]).sum()
    if stock == len(s):
        return (
            "In every scenario the stockpile draws, more than the model's, make the width of its intervals, and those rest on "
            "cited inventories and on theatre shares (the assumed part of each force sent to this theatre) with no source."
        )
    return (
        f"In {stock} of {len(s)} scenarios the stockpile draws, more than the model's, make the width of its intervals; "
        "the stockpile rests on cited inventories and on theatre shares (the assumed part of each force sent to this "
        "theatre) with no source."
    )


def _short_repeats(clean, strict) -> str:
    """The SAC gain without today's data, and also without the defence tables, once if they print the same."""
    lead = "Without the columns flagged as today's data, the selected model's gain over population and country is"
    first = f"{interval(clean)}, by blocks {block_interval(clean)}"
    second = f"{interval(strict)}, by blocks {block_interval(strict)}"
    if first == second:
        return f"{lead}, with or without the defence tables, {first}: {claim(clean)}."
    if claim(clean) == claim(strict):
        return f"{lead} {first}, and also without the defence tables {second}. In both, {claim(clean)}."
    return f"{lead} {first}: {claim(clean)}. Also without the defence tables it is {second}: {claim(strict)}."


def with_readme_results(text: str) -> str:
    head, rest = text.split(README_START)
    _, tail = rest.split(README_END)
    return f"{head}{README_START}\n{readme_results()}\n{README_END}{tail}"


def main() -> None:
    (OUT / "TABLES.md").write_text(tables(), encoding="utf-8")
    (ROOT / "REPORT.md").write_text(report(), encoding="utf-8")
    readme = ROOT / "README.md"
    readme.write_text(with_readme_results(readme.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
