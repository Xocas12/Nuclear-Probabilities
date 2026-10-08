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
# Russian notes: "до 1961 Сталино", "1940-1957 Молотов". English notes on the other pages:
# "Kirov until 1999", "Staliniri in 1934-1961", "Serebrovski 1964-1992", "earlier Frunze",
# "Soviet name: Panfilov"; a name may be given in two scripts, "სტალინირი / Staliniri".
SEGMENT = re.compile(
    r"(?:(?P<start>\d{4})\s*[\-–]\s*(?P<end>\d{4})|до\s+(?P<until>\d{4}))\s+(?P<name>[^,;()*]+)"
)
EN_UNTIL = re.compile(r"(?P<name>[^,;()]+?)\s+until\s+(?P<until>\d{4})")
EN_SPAN = re.compile(r"(?P<name>[^,;()]+?)\s+(?:in\s+)?(?P<start>\d{4})\s*[\-–]\s*(?P<end>\d{4})")
EN_UNDATED = re.compile(r"(?:earlier|Soviet name:)\s+(?P<names>[^;()]+)")
NOT_A_NAME = re.compile(
    r"^(?:merged|now|became|partly|destroyed|in\s|город|пгт|посёлок|посел|\d)", re.I
)


def normalise(name: str) -> str:
    text = name.lower().replace("ё", "е")
    text = DASHES.sub(" ", text)
    text = NON_WORD.sub("", text)
    return SPACES.sub(" ", text).strip()


# Letters of the other Cyrillic alphabets of the USSR folded to their nearest Russian letter,
# so "Леңгір" (Kazakh) meets "Ленгир" and "Калінкавічы" (Belarusian) meets "Калинкавичы"; and
# the two spellings of Romanian ș and ț folded together.
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
        # Romanian and Moldovan s and t with a comma below (pop-stat) or a cedilla (GeoNames)
        "ș": "s",
        "ş": "s",
        "ț": "t",
        "ţ": "t",
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


def split_scripts(name: str) -> list[str]:
    """'სტალინირი / Staliniri' -> both; 'Nor Bayazet, Kamo' stays one segment per call."""
    return [p.strip() for p in name.split("/") if p.strip()]


def former_names(notes: str) -> list[tuple[int | None, int | None, str]]:
    """(start year, end year, name) for every former name in a pop-stat note; years are None
    when the note gives none ("earlier Frunze")."""
    notes = notes or ""
    out: list[tuple[int | None, int | None, str]] = []

    def add(start, end, name):
        for n in split_scripts(name):
            if n and not NOT_A_NAME.match(n):
                out.append((start, end, n))

    for m in SEGMENT.finditer(notes):
        if m["until"]:
            add(None, int(m["until"]), m["name"])
        else:
            add(int(m["start"]), int(m["end"]), m["name"])
    for part in re.split(r",\s*", notes):
        if m := EN_UNTIL.fullmatch(part.strip()):
            add(None, int(m["until"]), m["name"])
        elif m := EN_SPAN.fullmatch(part.strip()):
            add(int(m["start"]), int(m["end"]), m["name"])
    for m in EN_UNDATED.finditer(notes):
        for n in re.split(r",\s*", m["names"]):
            add(None, None, n)
    return out


def name_on(current: str, notes: str, year: int) -> str:
    """The name in use during `year`: a former name whose span covers the year, else the
    current name. "1940-1957 X" covers 1940 to 1956; "до 1961 X" / "X until 1961" cover the
    years before 1961, and of several such names the one that ends first after `year` applies.
    Undated former names ("earlier X") are not used here."""
    until = []
    for start, end, name in former_names(notes):
        if end is None:
            continue
        if start is not None and start <= year < end:
            return name
        if start is None and year < end:
            until.append((end, name))
    return min(until)[1] if until else current
