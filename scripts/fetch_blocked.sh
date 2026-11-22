#!/usr/bin/env bash
# Fetch the raw files the cloud container cannot reach (data/BLOCKED.md, first table).
# Run from the repository root on an ordinary machine, then copy data/raw/ across (or commit
# nothing: data/raw/ is git-ignored) and run `make data` to check the hashes.
set -euo pipefail
UA="Mozilla/5.0 (research; nuclear-probabilities)"
get() { mkdir -p "$(dirname "$2")"; curl -fL --retry 4 -A "$UA" -o "$2" "$1" && echo "ok  $2"; }
get https://www.demoscope.ru/weekly/ssp/ussr59_reg2.php data/raw/demoscope/ussr59_reg2.html
for p in 0041 0042 0043; do
  get "https://digi.bib.uni-mannheim.de/fileadmin/statjahrb/514402644_1956/pdf/514402644_${p}.pdf" \
      "data/raw/ddr/514402644_${p}.pdf"
done
