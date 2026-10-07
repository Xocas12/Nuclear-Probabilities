"""Download the sources listed in data/sources.yaml into data/raw/ and record what was
retrieved and when.

    python -m nucprob.sources.fetch [ID ...] [--refresh]

A file that is already present is checked against its recorded sha256 and kept; a
different hash is reported (the source changed since it was recorded), not overwritten.
`--refresh` downloads again and records the new hash. Entries with `fetch: false` are
downloaded by hand and only checked.
"""

import argparse
import datetime as dt
import hashlib
import sys
import time
from pathlib import Path

import requests
import yaml

from nucprob.paths import RAW, SOURCES

HEADER_LINES = 4  # the comment block at the top of sources.yaml, kept on rewrite
USER_AGENT = "nuclear-probabilities research project (historical data; contact via GitHub)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest() -> dict:
    return yaml.safe_load(SOURCES.read_text(encoding="utf-8"))


def save_manifest(manifest: dict) -> None:
    header = "".join(SOURCES.read_text(encoding="utf-8").splitlines(keepends=True)[:HEADER_LINES])
    body = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=100)
    SOURCES.write_text(header + body, encoding="utf-8")


def download(url: str, dest: Path, tries: int = 4) -> None:
    """Stream to a temporary file and move it into place, retrying with backoff."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(tries):
        try:
            with requests.get(
                url, stream=True, timeout=120, headers={"User-Agent": USER_AGENT}
            ) as r:
                r.raise_for_status()
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            tmp.replace(dest)
            return
        except requests.RequestException as err:
            if attempt == tries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  {err}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="*", help="source ids (default: all)")
    parser.add_argument(
        "--refresh", action="store_true", help="download again and record the new hash"
    )
    args = parser.parse_args(argv)
    manifest = load_manifest()
    wanted = set(args.ids)
    changed = problems = 0
    for src in manifest["sources"]:
        if wanted and src["id"] not in wanted:
            continue
        dest = RAW / src["path"]
        if dest.exists() and not args.refresh:
            digest = sha256(dest)
            if src.get("sha256") and src["sha256"] != digest:
                print(f"{src['id']}: present, but its sha256 differs from the recorded one")
                problems += 1
            elif not src.get("sha256"):
                src["sha256"] = digest
                changed += 1
            continue
        if src.get("fetch") is False:
            print(f"{src['id']}: missing; download it by hand to data/raw/{src['path']}")
            problems += 1
            continue
        print(f"{src['id']}: downloading {src['url']}")
        download(src["url"], dest)
        src["retrieved"] = dt.datetime.now(dt.UTC).date().isoformat()
        src["sha256"] = sha256(dest)
        changed += 1
    if changed:
        save_manifest(manifest)
    print(f"{changed} entries recorded; {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
