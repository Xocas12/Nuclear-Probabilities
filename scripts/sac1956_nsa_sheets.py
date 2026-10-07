"""Extract the National Security Archive's city spreadsheets for the 1956 SAC study.

    python scripts/sac1956_nsa_sheets.py

EBB 538 posts four one-page sheets (Moscow, Leningrad, Beijing, Warsaw) that count the
installation lines of each city and its suburbs by category. They are an independent count of
the same list, made by the Archive's staff, so they check our transcription. They carry their own
slips (e.g. Mishutkino "Population 375"), so a difference is a lead to inspect, not a verdict.

Reads data/raw/sac1956/city_<City>.pdf (text layer) and writes
data/curated/validation_sac1956_nsa_city_sheets.csv: sheet, location, block (the name as printed
in the list), category_name (as on the sheet), category_code, count.
"""

import csv
import re
from pathlib import Path

import pdfplumber

RAW = Path("data/raw/sac1956")
OUT = Path("data/curated/validation_sac1956_nsa_city_sheets.csv")
# Locations on the sheets, and the block of the list each one counts (complex or sub-complex
# name as printed, without the country suffix).
LOCATIONS = {
    "Moscow/Suburbs": "MOSCOW", "Kuchino": "KUCHINO", "Shchylkovo": "SHCHELKOVO", "Tomilino": "TOMILINO",
    "Mishutkino": "MISHUTKINO",
    "Leningrad/Suburbs": "LENINGRAD", "Beloostrov": "BELOOSTROV", "Kolpino": "KOLPINO", "Sablino": "SABLINO",
    "Sestroretsk": "SESTRORETSK",
    "Beijing/Suburbs": "PEI PING", "Fengtai": "FENG TAI",
    "Warsaw": "WARSAW",
}
ROW = re.compile(r"^(?P<category>.+?) (?P<code>\d{1,3}) (?P<count>\d+)$")


def main() -> None:
    rows = []
    for sheet in ("Moscow", "Leningrad", "Beijing", "Warsaw"):
        with pdfplumber.open(RAW / f"city_{sheet}.pdf") as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        location = None
        for line in text.splitlines():
            line = line.replace("‐", "-").strip()
            for name in LOCATIONS:
                if line.startswith(name + " "):
                    location, line = name, line[len(name) + 1 :]
            m = ROW.match(line)
            if location and m:
                rows.append({
                    "sheet": sheet, "location": location, "block": LOCATIONS[location],
                    "category_name": m["category"], "category_code": m["code"].zfill(3), "count": int(m["count"]),
                })
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    totals = {}
    for r in rows:
        totals[r["location"]] = totals.get(r["location"], 0) + r["count"]
    print(f"{len(rows)} rows; lines per location: {totals}")


if __name__ == "__main__":
    main()
