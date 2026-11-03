"""The classifier report is what its outputs say, its outputs are what the scores say, and the run
is of the committed inputs."""

import json

import numpy as np
import pandas as pd
import pytest
import yaml

from nucprob.classifier import evaluate as ev
from nucprob.classifier import report
from nucprob.classifier.run import input_hashes
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier"
needs_run = pytest.mark.skipif(not (OUT / "comparison.csv").exists(), reason="no classifier run")
# A clean clone has the committed outputs but not the tables built from data/raw.
needs_table = pytest.mark.skipif(
    not (PROCESSED / "classifier_table.parquet").exists(), reason="classifier table not built here"
)


@needs_run
def test_report_is_a_regeneration_of_the_committed_outputs():
    assert (ROOT / "REPORT.md").read_text(encoding="utf-8") == report.report()
    assert (OUT / "TABLES.md").read_text(encoding="utf-8") == report.tables()


@needs_run
def test_the_run_used_the_protocol_settings_and_the_full_analysis():
    m = json.loads((OUT / "manifest.json").read_text())
    proto = yaml.safe_load((ROOT / "configs" / "protocol.yaml").read_text(encoding="utf-8"))
    assert m["bags"] == 50
    assert m["bootstrap"] == proto["evaluation"]["bootstrap"]["resamples"]
    assert not m["quick"]
    assert m["sealed_rows_excluded"] > 0


@needs_run
def test_the_run_is_of_the_committed_protocol_and_labels():
    """Changing the protocol, a label file, the registry or sources.yaml after a run fails here."""
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["protocol_sha256"] == sha256(ROOT / "configs" / "protocol.yaml")
    assert m["inputs_sha256"] == input_hashes()


@needs_run
@pytest.mark.skipif(
    not (PROCESSED / "classifier_table.parquet").exists(), reason="table not built here"
)
def test_the_run_is_of_this_table():
    """A permuted label in the table fails here, where the table exists."""
    m = json.loads((OUT / "manifest.json").read_text())
    assert m["table_sha256"] == sha256(PROCESSED / "classifier_table.parquet")


@needs_run
def test_every_comparison_row_recomputes_from_the_held_out_scores():
    """A changed number in comparison.csv fails here, without any table or raw data."""
    comp = pd.read_csv(OUT / "comparison.csv")
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz")
    assert len(comp) > 0
    for (scope, holdout), part in comp.groupby(["scope", "holdout"]):
        s = scores[(scores["scope"] == scope) & (scores["holdout"] == holdout)]
        assert len(s), (scope, holdout)
        for _, r in part.iterrows():
            k = s if r["lists"] == "all lists" else s[s["plan_id"] != report.SAC]
            y, doc = k["listed"].to_numpy(int), k["plan_id"].to_numpy()
            a = ev.weighted_pr_auc(y, k[r["model"]].to_numpy(), doc)
            b = ev.weighted_pr_auc(y, k[r["against"]].to_numpy(), doc)
            assert a == pytest.approx(r["a_pr_auc"], abs=2e-3), (scope, holdout)
            assert b == pytest.approx(r["b_pr_auc"], abs=2e-3), (scope, holdout)
            assert int(y.sum()) == r["positives"]
            assert a - b == pytest.approx(r["delta"], abs=2e-3)


def test_numbers_keep_two_decimals_and_a_constant_is_not_shown_as_a_measurement():
    assert report.signed(0.0234) == "+0.02" and report.signed(-0.0004) == "-0.000"
    assert report.signed(0.0) == "0.00"
    flat = {"delta": 0.0, "low": 0.0, "high": 0.0, "block_low": 0.0, "block_high": 0.0}
    assert report.constant(flat) and "constant" in report.interval(flat)
    assert not report.constant(flat | {"high": 0.001})


@needs_run
def test_verdicts_come_from_unrounded_bounds_and_need_both_intervals():
    row = {
        "low": -0.18,
        "high": -0.0004,
        "block_low": -0.2,
        "block_high": -0.001,
        "train_positives_min": 100,
        "constant_score": False,
    }
    assert report.verdict(row) == "loss"
    assert report.verdict(row | {"block_high": 0.01}) == "neither"
    assert report.verdict(row | {"train_positives_min": 8}) == "not a reading"
    assert report.verdict(row | {"constant_score": True}) == "not a reading"
    assert report.verdict(
        row | {"low": 0.01, "high": 0.2, "block_low": 0.0, "block_high": 0.2}
    ) == ("neither")


@needs_run
def test_failures_are_in_the_report_and_gains_are_not_claimed_where_an_interval_holds_zero():
    comp = pd.read_csv(OUT / "comparison.csv")
    assert ((comp["low"] <= comp["delta"]) & (comp["delta"] <= comp["high"])).all()
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    counts = primary["Verdict"].value_counts().to_dict()
    assert sum(counts.values()) == len(primary)
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    for name in ("gain", "loss", "neither", "not a reading"):
        assert f"{counts.get(name, 0)} {report.WORDS[name]}" in text
    for _, r in comp.iterrows():
        if report.verdict(r) == "gain":
            assert r["low"] > 0 and r["block_low"] > 0


@needs_run
def test_no_constant_model_is_read_as_a_finding():
    comp = pd.read_csv(OUT / "comparison.csv")
    primary = report.primary_table(comp, pd.read_csv(OUT / "selection.csv"))
    constant = comp[comp["constant_score"].astype(bool)]
    for _, r in constant.iterrows():
        assert report.verdict(r) == "not a reading"
    assert "not a reading" in set(primary["Verdict"]) or constant.empty


@needs_run
def test_no_exercise_based_scope_is_called_a_war_plan_model_and_the_ussr_is_refused():
    scopes = pd.read_csv(OUT / "scopes.csv").set_index("scope")
    pooled = "Warsaw Pact, pooled, exercise-based"
    assert scopes.loc[pooled, "exercise_based"]
    assert not scopes.loc["global, plan documents only", "exercise_based"]
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    assert not gate.loc["USSR", "allowed"]
    assert "not a war-plan model" in report.SCOPES[pooled]


@needs_run
def test_no_sealed_place_is_in_any_committed_score():
    """A sealed place is in a sealed block and unread by earlier runs. Eleven towns of those blocks were
    read by the M2 check before the seal and stay scored, so the block check allows only those."""
    sealed = set(pd.read_csv(ROOT / "data" / "curated" / "splits" / "sealed_blocks.csv")["block"])
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz", usecols=["plan_id", "place_id", "block"])
    sac = scores[scores["plan_id"] == report.SAC]
    assert len(sac) > 0
    assert sac.loc[sac["block"].isin(sealed), "place_id"].nunique() <= 11
    table = PROCESSED / "classifier_table.parquet"
    if table.exists():
        t = pd.read_parquet(table, columns=["place_id", "sealed"])
        assert not set(t.loc[t["sealed"].astype(bool), "place_id"]) & set(scores["place_id"])
    assert not (OUT / "sealed" / "metrics.csv").exists() or (OUT / "sealed" / "LOCK.json").exists()


def headline_quotes() -> list[str]:
    """Figures the README must repeat from the report."""
    comp = pd.read_csv(OUT / "comparison.csv")
    selection = pd.read_csv(OUT / "selection.csv")
    sens = pd.read_csv(OUT / "sensitivity.csv")
    sac = report._row(
        comp,
        report.SAC_SCOPE,
        "spatial blocks",
        report._best(selection, report.SAC_SCOPE),
        report.PLUS,
    )
    strict = sens[(sens["scope"] == report.SAC_SCOPE) & (sens["variant"] == "strict as-of")].iloc[0]
    g = report._row(
        comp,
        report.GLOBAL_ALL,
        "leave one document out",
        report._best(selection, report.GLOBAL_ALL),
        report.RULE,
    )
    return [report.interval(sac), report.interval(strict), report.interval(g)]


@needs_run
def test_the_readme_quotes_the_report_and_the_gate():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    for quoted in headline_quotes():
        assert quoted in readme and quoted in text, quoted
    gate = pd.read_csv(OUT / "state_gate.csv").set_index("attacker")
    us = gate.loc["US"]
    assert f"{int(us['positives_outside_largest'])} outside" in readme


@needs_run
@needs_table
def test_each_scope_lists_only_documents_of_that_scope():
    lists = pd.read_csv(OUT / "lists.csv")
    table = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    expected = lists["holdout"].str.startswith("expectation")
    pact = lists[lists["scope"].str.startswith("Warsaw Pact")]
    # Rows the pooled model is fitted and held out on are Warsaw Pact documents; the other side's
    # expectations of a Soviet strike are scored only as expectation lists, never as plans.
    assert pact.loc[~expected, "plan_id"].str.startswith("wp_").all()
    roles = table.groupby("plan_id")["role"].first()
    assert (roles.reindex(lists.loc[expected, "plan_id"]) == "test-expectation").all()
    assert not lists.loc[expected, "plan_id"].str.startswith("wp_").any()
    train = set(table.loc[table["role"] == "train", "plan_id"])
    assert set(lists.loc[~expected, "plan_id"]) <= train
    assert not np.isnan(pd.read_csv(OUT / "comparison.csv")["delta"]).any()


@needs_run
def test_the_report_states_what_earlier_reviews_found_it_withholding():
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    assert "no measured error rate" not in text
    assert "743 lines, found 0 errors" in text and "3 in 216" in text
    # Terms a newcomer needs, and the grades.
    for term in (
        "Strategic Air Command",
        "Correlates of War",
        '"All permitted"',
        "C, a scholar's table",
    ):
        assert term in text, term
    # War plans: what was read at source, in numbers from the outputs.
    assert "Only one was read at source" in text
    assert "A further 1 document" not in text
    # The map's unsourced shares and its scaling are printed, not left to the config.
    assert "The theatre shares have no source" in text
    assert "share of people living in scored towns" in text
    # Great Britain was withdrawn (tenth amendment): the report says so and cites no withdrawn reading.
    assert "No United Kingdom in 1965" in text and "unit_sensitivity.csv" not in text
    assert "The temporal rows also change attacker" in text
    # A gain named in prose is one in the table, whatever the data say.
    assert "Those gains are over LightGBM" not in text


@needs_run
def test_the_transcription_figures_in_the_report_are_those_of_the_card():
    card = (ROOT / "data" / "curated" / "sac1956" / "README.md").read_text(encoding="utf-8")
    card = " ".join(card.split())
    assert "(743 lines, seed 1956)" in card and "0 of 743, 95% interval 0 to 0.51%" in card
    assert "error rate was 1.3%" in card and "is 3 in 216" in card
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    assert "743 lines, found 0 errors in the final reading (95% interval 0 to 0.51%)" in text
    assert "own error rate was 1.3%" in text and "rate was 3 in 216" in text


@needs_run
def test_a_row_under_the_training_floor_is_counted_over_every_grid():
    """The primary table's training count is the fewest positives of any fit, not an estimate."""
    table = PROCESSED / "classifier_table.parquet"
    if not table.exists():
        pytest.skip("no built tables")
    t = pd.read_parquet(table)
    t = t[~t["sealed"].astype(bool) & (t["role"] == "train") & t["plan_id"].str.startswith("wp_")]
    comp = pd.read_csv(OUT / "comparison.csv")
    row = comp[
        (comp["scope"] == "Warsaw Pact, pooled, exercise-based")
        & (comp["holdout"] == "spatial blocks")
    ].iloc[0]
    assert row["train_positives_min"] == ev.spatial_train_positives(t.reset_index(drop=True))


@needs_run
def test_what_the_map_follows_is_stated_scenario_by_scenario():
    """A scenario whose cells follow the count of towns more than log people is named, not covered by
    a sentence about every scenario (the review of 46021d7)."""
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    spread = pd.read_csv(RUNS / "probmap" / "score_spread.csv")
    towns_more = spread[
        spread["p_correlation_with_towns_in_cell"] > spread["p_correlation_with_log_people_in_cell"]
    ]
    for scenario in towns_more["scenario"]:
        assert f"`{scenario}`" in text[text.index("**What that score does.**") :][:1500], scenario
    if len(towns_more):
        assert "In every scenario the cell probability correlates more with log people" not in text


@needs_run
def test_the_identification_sentences_follow_the_regularised_reading():
    reg = pd.read_csv(OUT / "identification" / "regularised.csv").set_index("columns")
    text = " ".join((ROOT / "REPORT.md").read_text(encoding="utf-8").split())
    nmc = reg.loc["no national power", "over_reference_verdict"]
    assert ("those columns do help name the document" in text) == (nmc == "below")
    assert ("made identification easier" in text) == (nmc == "above")
    assert "did not confirm either suspicion" not in text
    pop = reg.loc["population only", "over_largest_verdict"]
    assert ("population alone does worse than that" in text) == (pop == "below")
    if reg.at["all permitted", "over_largest_lo"] > 0.10:
        assert "a pooled gain under spatial blocks cannot be told from that" in text
        assert "A pooled gain as more than each document's base rate" in text
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    if reg.at["all permitted", "accuracy_lo"] > 0.9:
        assert "The columns name a row's document almost every time" in readme
    else:
        assert "almost every time" not in readme


def test_the_readme_names_every_committed_amendment():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    numbers = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in (ROOT / "configs").glob("protocol_amendment_*.yaml")
    )
    assert (
        f"`configs/protocol_amendment_{numbers[0]}.yaml` to `configs/protocol_amendment_{numbers[-1]}.yaml`"
        in readme
    )
    assert numbers == list(range(numbers[0], numbers[-1] + 1))


@needs_run
def test_the_readme_count_of_war_plan_positives_is_the_runs():
    lists = pd.read_csv(OUT / "lists.csv")
    war = lists[(lists["scope"] == report.GLOBAL_ALL) & (lists["doc_type"] == "war_plan")]
    n = int(war.drop_duplicates("plan_id")["positives"].sum())
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert f"war plans give {n} linked positives" in readme


@pytest.mark.skipif(not (OUT / "sealed" / "LOCK.json").exists(), reason="sealed set not scored")
def test_the_sealed_reading_is_of_the_committed_amendment_models_and_table():
    """The sealed set was scored once, after the eleventh amendment was committed, on the table the
    committed classifier run used, with the selected candidates of that run."""
    import subprocess

    lock = json.loads((OUT / "sealed" / "LOCK.json").read_text())
    amendment = ROOT / "configs" / "protocol_amendment_11.yaml"
    assert lock["amendment_11_sha256"] == sha256(amendment)
    assert lock["protocol_sha256"] == sha256(ROOT / "configs" / "protocol.yaml")
    committed = subprocess.run(
        ["git", "show", f"{lock['git_commit']}:configs/protocol_amendment_11.yaml"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    assert (
        committed == amendment.read_bytes()
    )  # the reading was fixed in a commit before the scores
    assert lock["table_sha256"] == json.loads((OUT / "manifest.json").read_text())["table_sha256"]
    comp = pd.read_csv(OUT / "sealed" / "comparison.csv")
    sel = pd.read_csv(OUT / "selection.csv")
    chosen = dict(sel.loc[sel["selected"], ["scope", "model"]].to_numpy())
    assert dict(comp[["scope", "model"]].drop_duplicates().to_numpy()) == chosen
    prim = comp[comp["primary"]]
    assert set(prim["scope"]) == set(chosen) and len(prim) == len(chosen)
    assert set(prim["population"]) == {"never_scored"} and set(prim["against"]) == {
        "population + country"
    }
    both = prim["excludes_zero"] & prim["block_excludes_zero"]
    assert ((prim["verdict"] != "neither") == both).all()
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    assert "### The sealed set, scored once" in text and "It has not been scored" not in text


@pytest.mark.skipif(
    not (OUT / "sealed" / "blind" / "comparison.csv").exists(), reason="blind reading not run"
)
def test_the_readme_says_what_the_blind_reading_found():
    """Twelfth amendment: the blind rows are of the 150 never_scored places no committed run scored,
    the primary row is blind against population + country, and README states its verdicts."""
    comp = pd.read_csv(OUT / "sealed" / "blind" / "comparison.csv")
    prim = comp[comp["primary"]]
    assert set(prim["population"]) == {"blind"} and set(prim["against"]) == {"population + country"}
    hist = pd.read_csv(ROOT / "data" / "curated" / "splits" / "scored_in_history.csv")
    scores = pd.read_csv(OUT / "sealed" / "scores.csv.gz", usecols=["place_id", "never_scored"])
    blind = scores["never_scored"] & ~scores["place_id"].isin(set(hist["place_id"]))
    assert (prim["rows"] == int(blind.sum())).all()
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert "**That reading is not blind.**" in readme
    if prim["verdict"].eq("neither").all():
        assert "no model beats population plus country" in readme
    else:
        assert "no model beats population plus country" not in readme


@pytest.mark.skipif(not report.BLIND.exists(), reason="blind reading not run")
def test_the_main_result_and_the_limits_quote_the_blind_reading():
    """The review of dcb3c75: the headline led with a gain the blind reading does not show. The main result
    states every primary blind row, and both documents list the missing blind gain as a limit."""
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    main = text[text.index("## Main result") : text.index("## Question")]
    prim = report._blind_rows(report.PLUS)
    for _, r in prim.iterrows():
        assert f"[{report.signed(r['low'])}, {report.signed(r['high'])}]" in main, r["scope"]
    cannot = text[text.index("## What the evidence cannot support") :]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    results = readme[readme.index(report.README_START) : readme.index(report.README_END)]
    if not prim["verdict"].eq("gain").any():
        assert "no selected model beats population plus country there" in main
        assert "A blind gain over population plus country" in cannot
        assert "A blind gain over population plus country" in readme
        assert results.index("On the only blind test") < results.index("Inside SAC's list")


def test_the_splits_card_does_not_call_never_scored_places_blind():
    card = " ".join(
        (ROOT / "data" / "curated" / "splits" / "README.md").read_text(encoding="utf-8").split()
    )
    assert "Only the 273 `never_scored` places are blind" not in card
    # The sizes the report takes from the card.
    for figure in ("of the 467 sealed places, 194", "273 `never_scored`", "123 of them"):
        assert figure in card, figure


def test_reader_facing_text_has_no_commit_names_or_run_on_lines():
    """Process history lives in configs/HISTORY.md, the amendments and the git log (review of dcb3c75)."""
    import re

    for name in ("README.md", "REPORT.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert not re.findall(r"(?<![\w/.-])[0-9a-f]{7}(?![\w/.-])", text), name
        assert max(len(line) for line in text.splitlines()) < 1500, name
    assert (ROOT / "configs" / "HISTORY.md").exists()


def test_a_nonzero_value_never_prints_as_an_exact_zero():
    assert report._cell(0.003) == "0.003"
    assert report._cell(-0.002) == "-0.002"
    assert report._cell(0.0) == "0.00"
    assert report._cell(0.00002) not in ("0.00", "0.000")
    assert report._cell(0.4438) == "0.44"


@needs_run
def test_tables_headings_are_not_truncated_holdout_labels():
    tables = (OUT / "TABLES.md").read_text(encoding="utf-8")
    assert "### PR-AUC by list: temporal: fit up\n" not in tables
    assert "### PR-AUC by list: fit up to 1956, score later" in tables


def test_no_committed_us_check_output_holds_county_coordinates():
    """Section E: no output finer than admin-1 beyond historical labels. The US check's county scores
    are written to data/interim/, not committed."""
    for f in (RUNS / "m4-us-check").glob("*.csv"):
        cols = set(pd.read_csv(f, nrows=0).columns)
        assert not {"lat", "lon", "fips"} & cols, f.name


@needs_run
def test_the_condensed_map_and_extended_tables_keep_every_figure():
    """REPORT folds each interval into one column and the theatre shares into one row per range; no
    figure of the map's outputs is lost, and TABLES.md keeps every economic and political row."""
    text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    m = report.MAP
    d = pd.read_csv(m / "delivered.csv")
    for _, r in d.iterrows():
        cell = f"{r['delivered_median']:.0f} [{r['delivered_low']:.0f}, {r['delivered_high']:.0f}]"
        fixed = f"[{r['delivered_low_share_fixed']:.0f}, {r['delivered_high_share_fixed']:.0f}]"
        assert f"| {r['scenario']} | {r['attacker']} | {cell} |" in text, cell
        assert fixed in text, fixed
        if r["share_of_people_in_scored_towns"] < 1:
            scored = f"{r['on_scored_towns_median']:.0f} [{r['on_scored_towns_low']:.0f}, "
            assert scored + f"{r['on_scored_towns_high']:.0f}]" in text
    for _, r in pd.read_csv(m / "by_delivery.csv").iterrows():
        avail = f"{r['available_median']:.0f} [{r['available_low']:.0f}, {r['available_high']:.0f}]"
        sent = f"{r['delivered_median']:.0f} [{r['delivered_low']:.0f}, {r['delivered_high']:.0f}]"
        row = f"| {r['scenario']} | {r['attacker']} | {r['stock_year']} | {r['delivery']} | {avail} | {sent} |"
        assert row in text, row
    theatre = report._theatre_table()
    stated = sum(len(a.split(", ")) for a in theatre["attackers"])
    assert stated == sum(len(sc["attackers"]) for sc in report.load_scenarios())
    shift = pd.read_csv(m / "domain_shift.csv")
    shift["feature"] = shift["comparison"].str.split(": ").str[-1]
    per = shift[shift["measure"].isin(report.SHIFT_COLUMNS)]
    for feature, g in per.groupby("feature", sort=False):
        values = g.set_index("measure")["value"].reindex(list(report.SHIFT_COLUMNS))
        row = "| " + " | ".join([feature, *(report._cell(float(v)) for v in values)]) + " |"
        assert row in text, row
    rows = report._extended_rows()
    tables = (OUT / "TABLES.md").read_text(encoding="utf-8")
    assert report.markdown(rows[report.EXTENDED_COLUMNS]) in tables
