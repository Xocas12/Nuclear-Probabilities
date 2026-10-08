"""Find places of the place table by a name written in Latin letters, as other sources write
them: SAC's list (GORKIY), Dexter and Rodionov's guide (Gor'kii), GeoNames (Gorky).

`latin_names` gives every name a place has, in the SAC/BGN transliteration; `loose` folds
the transliteration conventions together (Й/Ы/ИЙ as y, i or ii; Е as e or ye; Я as ya or ia),
so that keys from different sources meet.
"""

import re
import unicodedata
from collections import defaultdict

import pandas as pd
from rapidfuzz import fuzz, process

from nucprob.gazetteer.names import variants
from nucprob.gazetteer.translit import simple, to_latin

SCRIPTS = re.compile(r"[A-Za-zÀ-žЀ-ӿ\s\-’'.]+")  # Latin or Cyrillic names only
LOOSE = [("YE", "E"), ("YO", "E"), ("YU", "U"), ("YA", "A"), ("IY", "I"), ("II", "I"), ("Y", "I")]
LOOSE += [("IA", "A"), ("IU", "U"), ("J", "I"), ("EE", "E")]


def text(value) -> str:
    return value if isinstance(value, str) else ""


def latin_names(place) -> list[str]:
    """Every name of a settlement in the SAC style of Latin letters: its 1956 and current
    names, the names in its parentheses and notes, and GeoNames' Latin and Cyrillic alternate
    names."""
    names = [place["name_1956"], *variants(place["name_ru"], text(place.get("notes")))]
    names += [text(place.get("gn_name"))]
    names += [
        n for n in str(place.get("gn_alternatenames") or "").split(",") if SCRIPTS.fullmatch(n)
    ]
    return sorted({simple(to_latin(n)) for n in names if n})


def loose(name: str) -> str:
    """A matching key that ignores transliteration conventions and diacritics."""
    folded = unicodedata.normalize("NFKD", to_latin(name)).encode("ascii", "ignore").decode()
    out = simple(folded)
    for a, b in LOOSE:
        out = out.replace(a, b)
    return out


class PlaceIndex:
    """Loose name keys of every place of a table (row positions of `places`)."""

    def __init__(self, places: pd.DataFrame):
        self.places = places.reset_index(drop=True)
        index: dict[str, set[int]] = defaultdict(set)
        for pos in range(len(self.places)):
            for n in latin_names(self.places.iloc[pos]):
                index[loose(n)].add(pos)
        self.index = {k: sorted(v) for k, v in index.items() if k}

    def find(self, name: str) -> list[int]:
        return self.index.get(loose(name), [])

    def fuzzy(self, name: str, allowed: set[int] | None = None, cutoff: int = 92) -> list[int]:
        """Places whose closest loose key scores at least `cutoff` (0-100), best first."""
        target = loose(name)
        if len(target) < 6:
            return []
        keys = [k for k, v in self.index.items() if allowed is None or set(v) & allowed]
        hits = process.extract(target, keys, scorer=fuzz.ratio, score_cutoff=cutoff, limit=3)
        out = []
        for k, _, _ in hits:
            out += [p for p in self.index[k] if allowed is None or p in allowed]
        return list(dict.fromkeys(out))
