"""README answers both of its questions in plain words before the details, its
generated text is wrapped and grouped rather than run on, no reader-facing text leans on the build's review history,
the corrected Warsaw Pact links are described whole, estimates never print as "-0.00" or equal to a bound, constant
comparisons are called constant, and the viewer shows the share it says it shows."""

import json
import re

import pandas as pd

from nucprob.classifier import report
from nucprob.paths import CURATED, ROOT
from nucprob.probmap import viewer
from nucprob.probmap.counts import count

MAP = ROOT / "runs" / "probmap"


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _results() -> str:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    return text[text.index(report.README_START) : text.index(report.README_END)]


def test_readme_answers_both_questions_before_the_details():
    results = _results()
    flat = " ".join(results.split())
    assert results.index("### Short answers") < results.index("### Results in brief")
    short = flat[: flat.index("### Results in brief")]
    assert (
        "**What made a place a target?**" in short
        and "**How likely is an area to be struck?**" in short
    )
    # The population rule's own PR-AUC, from comparison.csv, not a fitted model on population (family_gain.csv)
    rule, plus = report._sac_rule(report.RULE), report._sac_rule(report.PLUS)
    assert f"(the population rule) gives a PR-AUC of {rule['b_pr_auc']:.2f}" in short
    assert f"population plus a term for each country gives {plus['b_pr_auc']:.2f}" in short
    assert "The brackets are the 5th to 95th percentiles" in short
    assert "so it cannot be told from no difference" in short
    scen = pd.read_csv(MAP / "scenarios.csv").set_index("scenario")
    for name in ("us_1956_on_bloc", "us_1950_stock_on_bloc"):
        r = scen.loc[name]
        assert (
            f"{count(r['cells_over_half_median'])} [{count(r['cells_over_half_low'])}, "
            f"{count(r['cells_over_half_high'])}] of {count(r['cells'])}"
        ) in short, name
    val = pd.read_csv(MAP / "validation.csv").set_index("reading").loc["spatial blocks held out"]
    assert f"mean cell probability is {val['mean_p']:.2f}" in short
    assert "extrapolation" in short


def test_short_answer_names_only_dated_families_and_says_the_defence_tables_are_later_knowledge():
    short = " ".join(_results().split())
    short = short[: short.index("### Results in brief")]
    sentence = short[short.index("Of the families that describe the towns as of 1956") :].split(
        ". "
    )[0]
    assert "transport" not in sentence and "industry" not in sentence
    assert "Transport adds the most but rests largely on today's data" in short
    if "defence" in sentence:
        assert "The defence sites are known mostly from post-Soviet sources" in short
    # The repeat without the defence tables is quoted, from sensitivity.csv
    sens = pd.read_csv(report.OUT / "sensitivity.csv")
    strict = sens[(sens["scope"] == report.SAC_SCOPE) & (sens["variant"] == "strict as-of")].iloc[0]
    assert report.interval(strict) in short


def test_family_table_puts_dated_families_before_todays_data():
    order = list(report.FAMILY_WORDS)
    assert order[-len(report.TODAYS_FAMILIES) :] == list(report.TODAYS_FAMILIES)
    results = _results()
    rows = [
        line
        for line in results.splitlines()
        if line.startswith("| ") and "Family added" not in line
    ]
    assert [r.split(" | ")[0][2:] for r in rows] == list(report.FAMILY_WORDS.values())


def test_generated_and_written_prose_is_wrapped():
    """README.md:62 was one 1,362-character line of seven near-identical clauses."""
    for name, limit in (("README.md", report.README_WIDTH), ("REPORT.md", 1000)):
        for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
            if not line.lstrip().startswith("|"):
                assert len(line) <= limit, (name, line[:80])
    seeds = _results()[_results().index("**Bootstrap seed.**") :]
    seeds = " ".join(seeds[: seeds.index("**No state gets its own model.**")].split())
    s = report.seed_summary()
    moved = _moved()
    assert f"{len(s) - len(moved)} of {len(s)} keep their verdict under all 20" in seeds
    assert f'The {len(moved)} that do not are listed in REPORT ("Bootstrap seed")' in seeds
    assert "the number 1956 (not the document year)" in seeds
    # REPORT lists every seed-dependent comparison, one table row each
    rep = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    section = rep[rep.index("**Bootstrap seed.**") :]
    assert f"These {len(moved)} are seed-dependent" in " ".join(section.split())


def _moved() -> pd.DataFrame:
    s = report.seed_summary()
    return s[~s["seed_stable"].astype(bool)]


def test_the_wrapper_keeps_tables_and_bullets():
    text = "- " + "word " * 40 + "\n  - " + "sub " * 40 + "\n| a | b |\n\nplain"
    out = report._wrap(text, width=60)
    lines = out.splitlines()
    assert all(len(x) <= 60 for x in lines if not x.startswith("|"))
    assert "| a | b |" in lines and lines[-1] == "plain"
    assert any(x.startswith("    sub") for x in lines)  # the sub-bullet's hanging indent
    assert " ".join(out.split()) == " ".join(text.split())


def test_no_reader_facing_text_leans_on_the_review_history():
    for name in ("README.md", "REPORT.md"):
        text = _flat(ROOT / name)
        for phrase in ("a review had", "a review found", "after a review", "A review found"):
            assert phrase not in text, (name, phrase)
    readme = _flat(ROOT / "README.md").lower()
    for word in ("seventeenth", "eighteenth"):
        assert f"{word} amendment" not in readme


def test_lato67_and_burza_are_defined_where_readme_first_names_them():
    readme = _flat(ROOT / "README.md")
    first = readme.index("Lato-67")
    assert readme[first : first + 60].startswith(
        ("Lato-67, a Polish exercise of 1967", "Lato-67 (the Coastal Front directive")
    )
    first = readme.index("Burza")
    assert readme[first : first + 50].startswith("Burza (the Maritime Front exercise of 1961)")


def test_the_corrected_links_are_described_whole():
    """Amendment 17 also gave reasons for Lato-67 rows 17 (Kiel) and 57 (west of Lingen); five towns were made
    positive in the rescoring seen before it, four in the links it adopted."""
    amendment = (ROOT / "configs" / "protocol_amendment_17.yaml").read_text(encoding="utf-8")
    assert "Kiel is not credited" in amendment and "gains four linked towns" in amendment
    text = _flat(ROOT / "REPORT.md")
    assert "row 17" in text and "row 57" in text and "Kiel" in text
    assert "four towns" in text
    # README gives the rule and sends the reader to REPORT for the rows
    assert 'REPORT ("Changed by the corrected Warsaw Pact links") gives the rows' in _flat(
        ROOT / "README.md"
    )
    rep = _flat(ROOT / "REPORT.md")
    assert "five Lato-67 towns made positive, one more than the links it adopted credit" in rep


def _estimates(text: str) -> list[tuple[str, str, str]]:
    return re.findall(r"([+-]\d\.\d+) \[([+-]?\d\.\d+), ([+-]?\d\.\d+)\]", text)


def test_a_negative_bound_rounded_to_zero_in_the_csv_keeps_its_sign():
    assert report.signed(-0.0) == "-0.000"
    assert report.signed(0.0) == "0.000"


def test_no_estimate_prints_as_minus_zero_or_equal_to_a_bound():
    for name in ("README.md", "REPORT.md", "runs/classifier/TABLES.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        # a signed zero has exactly three decimals (a value within 0.0005 of zero, on the sign's side)
        signed_zeros = set(re.findall(r"(?<![\d.])[+-]0\.0+(?![0-9])", text))
        assert signed_zeros <= {"+0.000", "-0.000"}, (name, signed_zeros)
        # no estimate itself prints as a signed zero unless it lies within 0.0005 of zero
        for est, _, _ in _estimates(text):
            assert est not in ("+0.00", "-0.00"), (name, est)
        found = _estimates(text)
        assert found, name
        for est, lo, hi in found:
            assert est not in (lo, hi), (name, est, lo, hi)


def test_a_constant_comparison_is_called_constant():
    fam = report._families()
    const = fam[fam.apply(report.constant, axis=1)]
    assert len(const)  # USSR national power: one country, so no variation
    rep = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    grid = rep[rep.index("| family | all countries | USSR |") :].split("\n\n")[0]
    assert "constant" in grid and "not a reading" not in grid
    assert "constant on these towns" in _results()


def test_near_zero_gains_read_under_one_seed_are_flagged():
    rep = _flat(ROOT / "REPORT.md")
    sealed = pd.read_csv(report.SEALED.parent / "comparison.csv")
    near = sealed[
        sealed["verdict"].eq("gain") & (sealed[["low", "block_low"]].min(axis=1) < report.NEAR_ZERO)
    ]
    if len(near):
        assert "on a lower bound within 0.005 of zero" in rep
    assert (
        "So a verdict there whose bound lies within 0.005 of zero may not survive another seed."
        in rep
    )


def test_report_header_names_every_non_run_source_it_draws_figures_from():
    head = _flat(ROOT / "REPORT.md")[:1200]
    for path in (
        "data/curated/splits/README.md",
        "data/curated/sac1956/README.md",
        "data/curated/features/weurope_military_sites_1965.md",
        "data/notes/second_read_2026-11b.md",
        "data/sources.yaml",
    ):
        assert path in head, path


def test_readme_opening_does_not_claim_every_input_is_of_the_document_date():
    readme = _flat(ROOT / "README.md")
    opening = readme[: readme.index("## What was found")]
    assert "as far as the sources allow" in opening and "several inputs are later" in opening


def test_agent_built_town_tables_are_said_to_be_so():
    card = _flat(CURATED / "gazetteer" / "TOWNS_INSTRUCTIONS.md")
    assert card.startswith("# Building a town table") and "*What this file is.*" in card[:300]
    assert "language-model agents" in card
    assert "transcribed by language-model agents" in _flat(ROOT / "README.md")


def test_the_viewer_shows_the_share_of_people_in_scored_towns():
    delivered = pd.read_csv(MAP / "delivered.csv")
    data = viewer.payload()
    for sc in data["scenarios"]:
        d = delivered[delivered["scenario"] == sc["id"]].set_index("attacker")
        for row in sc["delivered"]:
            want = round(float(d.loc[row["attacker"], "share_of_people_in_scored_towns"]), 2)
            assert row["share_of_people_in_scored_towns"] == want
    assert len(data["shift"]) == 1
    page = (MAP / "viewer" / "index.html").read_text(encoding="utf-8")
    assert "share of people in scored towns" in page
    assert json.dumps(data["shift"]) in page or '"shift"' in page


def test_state_gate_says_what_its_positives_count():
    rep = _flat(ROOT / "REPORT.md")
    assert "count positives in those plan-type documents only, which is why the USSR shows 0" in rep
