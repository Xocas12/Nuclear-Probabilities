"""Cyrillic to Latin in the style of the 1956 SAC list (close to BGN/PCGN: Ж ZH, Х KH, Ц TS,
Ч CH, Ш SH, Щ SHCH, Ю YU, Я YA, Й and Ы Y, initial Е YE), used only to compare names."""

import re

RU = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    # Ukrainian and Belarusian letters, written as a Russian-trained transliterator would
    "і": "i",
    "ї": "yi",
    "є": "ye",
    "ґ": "g",
    "ў": "u",
    # Kazakh, Kyrgyz, Tajik, Azerbaijani-Cyrillic letters folded to the nearest Russian sound
    "ә": "a",
    "ғ": "g",
    "қ": "k",
    "ң": "n",
    "ө": "o",
    "ұ": "u",
    "ү": "u",
    "һ": "kh",
    "ҷ": "ch",
    "ӣ": "i",
    "ӯ": "u",
    "ҳ": "kh",
}


def to_latin(name: str) -> str:
    text = name.lower()
    text = re.sub(r"(^|[\s\-])е", lambda m: m.group(1) + "ye", text)  # initial Е -> YE
    return "".join(RU.get(ch, ch) for ch in text).upper()


def simple(name: str) -> str:
    """Letters only, upper case, for comparing transliterations ("MOLOTOV", "KAMENSK-URALSKIY")."""
    return re.sub(r"[^A-Z]", "", name.upper())
