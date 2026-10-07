"""Name normalisation and historical names.

Cyrillic names are compared in a normal form: lower case, ё → е, hyphens and dashes as spaces,
punctuation dropped, spaces collapsed. pop-stat's notes record renamings ("до 1940 Пермь,
1940-1957 Молотов"); `name_on` reads the name a place carried in a given year from them.
"""

import re
import unicodedata

DASHES = re.compile(r"[\-‐‑‒–—]")
NON_WORD = re.compile(r"[^\w\s]")
SPACES = re.compile(r"\s+")
# "до 1961 Сталино", "1940-1957 Молотов", "1924-1929 Сталин"; names may hold spaces and
# hyphens ("Ойрот-Тура", "Нижний Тагил") and end at a comma, a semicolon or the end.
SEGMENT = re.compile(
    r"(?:(?P<start>\d{4})\s*[\-–]\s*(?P<end>\d{4})|до\s+(?P<until>\d{4}))\s+(?P<name>[^,;()*]+)"
)


def normalise(name: str) -> str:
    text = name.lower().replace("ё", "е")
    text = DASHES.sub(" ", text)
    text = NON_WORD.sub("", text)
    return SPACES.sub(" ", text).strip()


# Letters of the other Cyrillic alphabets of the USSR folded to their nearest Russian letter,
# so "Леңгір" (Kazakh) meets "Ленгир" and "Калінкавічы" (Belarusian) meets "Калинкавичы".
FOLD = str.maketrans(
    {
        "і": "и",
        "ї": "и",
        "є": "е",
        "ґ": "г",
        "ў": "у",  # Ukrainian, Belarusian
        "ә": "а",
        "ғ": "г",
        "қ": "к",
        "ң": "н",
        "ө": "о",
        "ұ": "у",
        "ү": "у",
        "һ": "х",  # Kazakh, Kyrgyz
        "ҷ": "ч",
        "ӣ": "и",
        "ӯ": "у",
        "ҳ": "х",  # Tajik
        "ҟ": "к",
        "ҭ": "т",
        "ҧ": "п",
        "ҵ": "ц",
        "ҽ": "ч",
        "ҩ": "о",
        "ӡ": "з",
        "ҕ": "г",
        "ə": "а",  # Abkhaz
        "ь": "",
        "ъ": "",
        "'": "",
        "’": "",
    }
)


def key(name: str) -> str:
    """Matching key: the normal form, other Cyrillic alphabets folded to Russian letters,
    without spaces ("Янги-Юль" and "Янгиюль" agree)."""
    return normalise(name).translate(FOLD).replace(" ", "")


def latin_key(name: str) -> str:
    """A rough Latin key: diacritics stripped, lower case, letters only ("Kalinkavičy" ->
    "kalinkavicy"), for the transliterated names of pop-stat and the ASCII names of GeoNames."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z]", "", text)


def variants(name: str, notes: str = "") -> list[str]:
    """Names to try, best first: the name itself, the names in its parentheses ("Дніпро
    (Дніпропетровськ)", "Bender (Tighina)"), then former names from the notes."""
    main = re.sub(r"\(.*?\)", "", name).strip()
    inner = [
        p.strip() for group in re.findall(r"\((.*?)\)", name) for p in re.split(r"[,;]", group)
    ]
    former = [n for _, _, n in former_names(notes)]
    out = []
    for n in [main, *inner, *former]:
        if n and n not in out:
            out.append(n)
    return out


def former_names(notes: str) -> list[tuple[int | None, int, str]]:
    """(start year or None, end year, name) for every dated former name in a pop-stat note."""
    out = []
    for m in SEGMENT.finditer(notes or ""):
        name = m["name"].strip()
        if not name or name[0].isdigit() or name.startswith(("город", "пгт", "посёлок", "посел")):
            continue
        if m["until"]:
            out.append((None, int(m["until"]), name))
        else:
            out.append((int(m["start"]), int(m["end"]), name))
    return out


def name_on(current: str, notes: str, year: int) -> str:
    """The name in use during `year`: a former name whose span covers the year, else the
    current name. "1940-1957 X" covers 1940 to 1956; "до 1961 X" covers the years before 1961,
    and of several such names the one that ends first after `year` applies."""
    until = []
    for start, end, name in former_names(notes):
        if start is not None and start <= year < end:
            return name
        if start is None and year < end:
            until.append((end, name))
    return min(until)[1] if until else current
