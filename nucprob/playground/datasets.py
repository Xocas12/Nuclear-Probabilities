"""Every modelling table of the project as one uniform `Data` object.

| name | rows | target |
|---|---|---|
| `sac1956` | the bloc's towns of 10,000+ near 1956 | named in the SAC 1956 study (`listed`) |
| `sac1956:has_dgz` | same | has a designated ground zero |
| `sac1956:part2` | same, where known | keeps an aim point in the Part II allocation |
| `ussr1959` | the USSR's towns at the 1959 census (the M1 slice) | `listed` |
| `napb90:very_high` | US counties, 1985 | NAPB-90 blast risk >= 10 psi |
| `napb90:medium_plus` | US counties, 1985 | NAPB-90 blast risk >= 2 psi |
| `napb90:fallout` | US counties, 1985 | NAPB-90 fallout high or very high (a consequence, not a target label) |
| `transfer:<plan_id>` | the towns of one smaller list's countries at its date | named in that list |
| `pooled` | every town of the bloc and of the transfer regions, common features only | named in its own list |

Build the processed tables first (`make check`, `python -m nucprob.us1985.dataset`, and the
four `nucprob.transfer` steps); a dataset whose table is missing says which command builds it.
"""

import warnings
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from nucprob.features.registry import FEATURES as BLOC_FEATURES
from nucprob.model.splits import assign_blocks
from nucprob.paths import CURATED, PROCESSED
from nucprob.us1985.features import FEATURES as US_FEATURES

META = ["id", "name", "country", "lat", "lon", "year", "block", "sealed", "y"]


@dataclass
class Data:
    """One modelling table: `frame` holds META columns plus the features."""

    name: str
    description: str
    frame: pd.DataFrame
    features: list[str]
    families: dict[str, list[str]] = field(default_factory=dict)
    note: str = ""

    @property
    def X(self) -> pd.DataFrame:
        return self.frame[self.features]

    @property
    def y(self) -> pd.Series:
        return self.frame["y"]

    def select(self, spec: str | list[str] | None = None, drop: str | list[str] | None = None):
        """A copy restricted to some families or columns ("population,military" or a list of
        feature names), optionally without others."""

        def resolve(s):
            names = [x.strip() for x in s.split(",")] if isinstance(s, str) else list(s)
            out = []
            for n in names:
                out += self.families.get(n, [n] if n in self.features else [])
            return out

        keep = resolve(spec) if spec else list(self.features)
        if drop:
            gone = set(resolve(drop))
            keep = [c for c in keep if c not in gone]
        if not keep:
            raise ValueError(f"no features selected; families: {sorted(self.families)}")
        fams = {f: [c for c in cols if c in keep] for f, cols in self.families.items()}
        return Data(
            self.name,
            self.description,
            self.frame,
            keep,
            {f: c for f, c in fams.items() if c},
            self.note,
        )

    def summary(self) -> str:
        n, pos = len(self.frame), int(self.frame["y"].sum())
        fams = ", ".join(f"{f} ({len(c)})" for f, c in self.families.items())
        return (
            f"{self.name}: {n} rows, {pos} positive ({pos / n:.1%}), "
            f"{len(self.features)} features: {fams}"
        )


def family_of(col: str) -> str:
    for reg in (BLOC_FEATURES, US_FEATURES):
        if col in reg:
            return reg[col].family
    if "pop" in col or "growth" in col:
        return "population"
    if col.startswith("log_km_to_") or col.endswith("_hq"):
        return "military"
    if col in ("regional_seat", "republic_capital", "national_capital", "district_seat"):
        return "administrative"
    return "other"


def families(cols: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c in cols:
        out.setdefault(family_of(c), []).append(c)
    return out


def _read(name: str, how: str) -> pd.DataFrame:
    path = PROCESSED / name
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; build it with: {how}")
    return pd.read_parquet(path)


def _numeric(df: pd.DataFrame, exclude: set[str]) -> list[str]:
    return [
        c
        for c in df.columns
        if c not in exclude and pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().any()
    ]


# --- loaders -------------------------------------------------------------------------------


def _sac1956(target: str) -> Callable[[], tuple[pd.DataFrame, list[str]]]:
    def load():
        d = _read("dataset_sac1956.parquet", "make check")
        feats = [c for c in BLOC_FEATURES if c in d.columns]
        frame = pd.DataFrame(
            {
                "id": d["place_id"],
                "name": d["name_1956"],
                "country": d["country_1956"],
                "lat": d["lat"],
                "lon": d["lon"],
                "year": 1956,
                "block": d["block"],
                "sealed": d["sealed"].astype(bool),
                "y": d[target],
            }
        )
        frame = pd.concat([frame, d[feats]], axis=1)
        return frame[frame["y"].notna()].reset_index(drop=True), feats

    return load


def _ussr1959():
    d = _read("dataset_ussr1959.parquet", "make check (the M1 slice is built by nucprob.model)")
    labels = {
        "listed",
        "has_dgz",
        "n_dgz",
        "n_dgz_points_near",
        "n_complexes",
        "n_subcomplexes",
        "n_installations",
        "best_priority",
        "best_tier",
        "parent_priority",
        "pop_1959",
        "lat",
        "lon",
    }
    feats = _numeric(d, labels)
    frame = pd.DataFrame(
        {
            "id": d["place_id"],
            "name": d["name_1956"],
            "country": d["republic"],
            "nation": "USSR",
            "lat": d["lat"],
            "lon": d["lon"],
            "year": 1959,
            "block": d["block"],
            "sealed": d["sealed"].astype(bool),
            "y": d["listed"].fillna(0).astype(int),
        }
    )
    return pd.concat([frame, d[feats]], axis=1), feats


def _napb90(target: str):
    def load():
        d = _read("dataset_napb90.parquet", "python -m nucprob.us1985.dataset")
        feats = [c for c in US_FEATURES if c in d.columns]
        if target == "fallout":
            f = pd.read_csv(CURATED / "napb90" / "fallout_counties.csv", dtype={"fips": str})
            rank = f.drop_duplicates("fips").set_index("fips")["fallout_rank"]
            y = d["fips"].map(rank).ge(2).where(d["fips"].isin(rank.index))
        else:
            y = d[target]
        frame = pd.DataFrame(
            {
                "id": d["fips"],
                "nation": "USA",
                "name": d["census_name"] + ", " + d["state"],
                "country": d["state"],
                "lat": d["lat"],
                "lon": d["lon"],
                "year": 1985,
                "block": d["block"],
                "sealed": d["sealed"].astype(bool),
                "y": y,
            }
        )
        frame = pd.concat([frame, d[feats]], axis=1)
        return frame[frame["y"].notna()].reset_index(drop=True), feats

    return load


def _transfer_tables():
    from nucprob.transfer.features import COMMON, MILITARY_GROUPS
    from nucprob.transfer.labels import BLOC
    from nucprob.transfer.regions import REGIONS

    how = "python -m nucprob.transfer.places / .features / .labels"
    labels = _read("labels_transfer.parquet", how)
    feats = _read("features_transfer.parquet", how)
    places = _read("transfer_places.parquet", how)[["place_id", "name", "lat", "lon"]]
    cols = [*COMMON, *MILITARY_GROUPS]
    bloc = _read("dataset_sac1956.parquet", "make check")
    bloc_feats = bloc[["place_id", "country_1956", "name_1956", "lat", "lon", *cols]].rename(
        columns={"country_1956": "country", "name_1956": "name"}
    )
    bloc_feats = bloc_feats.assign(region=BLOC)
    t = feats.merge(places, on="place_id", how="left")
    all_feats = pd.concat([t, bloc_feats], ignore_index=True)
    years = {k: r.year for k, r in REGIONS.items()} | {BLOC: 1956}
    return labels, all_feats, cols, years


def _transfer(plan: str):
    def load():
        labels, feats, cols, years = _transfer_tables()
        lab = labels[labels["plan_id"] == plan]
        if lab.empty:
            raise KeyError(f"no transfer labels for {plan}")
        d = lab.merge(feats, on=["place_id", "region"], how="left")
        frame = pd.DataFrame(
            {
                "id": d["place_id"],
                "name": d["name"],
                "country": d["country"],
                "lat": d["lat"],
                "lon": d["lon"],
                "year": d["region"].map(years),
                "block": assign_blocks(d["lat"].to_numpy(), d["lon"].to_numpy()),
                "sealed": False,
                "y": d["listed"],
            }
        )
        return pd.concat([frame, d[cols]], axis=1), cols

    return load


def _pooled():
    labels, feats, cols, years = _transfer_tables()
    d = labels.merge(feats, on=["place_id", "region"], how="left")
    # One row per place and list; the bloc's own SAC labels are added as the list "sac1956".
    bloc = _read("dataset_sac1956.parquet", "make check")
    b = bloc[~bloc["sealed"]]
    sac = pd.DataFrame(
        {
            "place_id": b["place_id"],
            "region": "bloc_1956",
            "plan_id": "us_1956_sac",
            "listed": b["listed"],
        }
    ).merge(feats, on=["place_id", "region"], how="left")
    d = pd.concat([d, sac], ignore_index=True)
    frame = pd.DataFrame(
        {
            "id": d["place_id"] + "|" + d["plan_id"],
            "name": d["name"],
            "country": d["country"],
            "lat": d["lat"],
            "lon": d["lon"],
            "year": d["region"].map(years),
            "block": assign_blocks(d["lat"].to_numpy(), d["lon"].to_numpy()),
            "sealed": False,
            "y": d["listed"],
            "plan_id": d["plan_id"],
        }
    )
    return pd.concat([frame, d[cols]], axis=1), cols


DATASETS: dict[str, tuple[str, Callable]] = {
    "sac1956": ("Soviet bloc towns 1956, named in the SAC 1956 study", _sac1956("listed")),
    "sac1956:has_dgz": (
        "Soviet bloc towns 1956, with a designated ground zero",
        _sac1956("has_dgz"),
    ),
    "sac1956:part2": (
        "Soviet bloc towns 1956, keeping an aim point in the SAC Part II allocation",
        _sac1956("part2_has_dgz"),
    ),
    "ussr1959": ("USSR towns at the 1959 census, named in the SAC study (M1 slice)", _ussr1959),
    "napb90:very_high": ("US counties 1985, NAPB-90 blast risk >= 10 psi", _napb90("very_high")),
    "napb90:medium_plus": ("US counties 1985, NAPB-90 blast risk >= 2 psi", _napb90("medium_plus")),
    "napb90:fallout": (
        "US counties 1985, NAPB-90 fallout risk high or very high (not a target label)",
        _napb90("fallout"),
    ),
    "pooled": (
        "every town of the bloc and the transfer regions, named in its own list (common features)",
        _pooled,
    ),
}


def transfer_lists() -> list[str]:
    path = PROCESSED / "labels_transfer.parquet"
    if not path.exists():
        return []
    return sorted(pd.read_parquet(path, columns=["plan_id"])["plan_id"].unique())


def names() -> list[str]:
    return [*DATASETS, *(f"transfer:{p}" for p in transfer_lists())]


def load(name: str, include_sealed: bool = False) -> Data:
    """A dataset by name. The sealed test blocks are dropped unless include_sealed is True."""
    if name.startswith("transfer:"):
        plan = name.split(":", 1)[1]
        description, loader = f"towns of the countries of {plan}, named in it", _transfer(plan)
    elif name in DATASETS:
        description, loader = DATASETS[name]
    else:
        raise KeyError(f"unknown dataset {name}; known: {names()}")
    frame, feats = loader()
    frame["y"] = frame["y"].astype(int)
    if "nation" not in frame:
        frame["nation"] = frame["country"]
    if not include_sealed:
        frame = frame[~frame["sealed"]].reset_index(drop=True)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").fillna(-1).astype(int)
    feats = [c for c in feats if frame[c].notna().any() and frame[c].nunique() > 1]
    frame[feats] = frame[feats].astype(float).replace([np.inf, -np.inf], np.nan)
    note = ""
    flag = PROCESSED / "INCOMPLETE_BUILD.txt"
    if flag.exists() and not name.startswith("napb90"):
        note = flag.read_text().strip()
        warnings.warn(f"incomplete build: {note}", stacklevel=2)
    return Data(name, description, frame, feats, families(feats), note)
