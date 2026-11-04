"""Download the sources listed in data/sources*.yaml into data/raw/ and record what was
retrieved and when.

    python -m nucprob.sources.fetch [ID ...] [--refresh]

A file that is already present is checked against its recorded sha256 and kept; a
different hash is reported (the source changed since it was recorded), not overwritten, and
the same goes for a fresh download of a source with a recorded hash. A source that cannot be
reached is reported and the rest continue; `mirror` names an archived copy to try instead.
`volatile: <why>` marks a source whose bytes change with no change in what is used (a live
database, a landing page): a difference is still reported, but is not a problem.
Nothing is downloaded that the host's robots.txt does not allow (nucprob.sources.robots): such a
source is reported as not obtained, and its mirror is not tried. Some entries give `obtained_from`
(with `obtained`, the date, and `obtained_note`): the URL the held bytes were actually fetched from when that is not
the publisher's `url` (a licensed mirror or an archived capture, used where the publisher's robots.txt
refuses or cannot be read). It is downloaded in place of `url`, under the same robots check and the
same sha256 check. `--refresh` downloads again and records the new hash. Entries with `fetch: false` are
downloaded by hand and only checked; entries with `fetch: <module>` (tile sets) are fetched by
that module.
"""

import argparse
import datetime as dt
import hashlib
import sys
import time
from pathlib import Path

import requests
import yaml

from nucprob.paths import RAW, REGISTRIES
from nucprob.sources import robots

HEADER_LINES = 4  # the comment block at the top of sources.yaml, kept on rewrite
USER_AGENT = robots.USER_AGENT


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["sources"]


def obtained() -> dict[str, dict]:
    """The registered sources that give `obtained_from`, by id."""
    return {s["id"]: s for s in load_manifest()["sources"] if s.get("obtained_from")}


def load_manifest() -> dict:
    """Every registered source, from every registry."""
    return {"sources": [dict(s) for path in REGISTRIES for s in _read(path)]}


def save_manifest(manifest: dict) -> None:
    """Rewrite only a registry with a changed entry: the primary run records one file's hash."""
    by_id = {s["id"]: s for s in manifest["sources"]}
    for path in REGISTRIES:
        old = _read(path)
        new = [by_id[s["id"]] for s in old]
        if new == old:
            continue
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        body = yaml.safe_dump({"sources": new}, sort_keys=False, allow_unicode=True, width=100)
        path.write_text("".join(lines[:HEADER_LINES]) + body, encoding="utf-8")


def download(url: str, dest: Path, tries: int = 4) -> None:
    """Stream to a temporary file and move it into place, retrying with backoff. Raises
    robots.RobotsRefused, with nothing requested, if robots.txt does not allow the URL."""
    robots.require(url)
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
        if src.get("withdrawn"):
            print(f"{src['id']}: withdrawn, not fetched ({src['withdrawn'].split('.')[0]})")
            continue
        if isinstance(src.get("fetch"), str):
            print(f"{src['id']}: fetched by {src['fetch']}")
            continue
        if dest.exists() and not args.refresh:
            digest = sha256(dest)
            if src.get("sha256") and src["sha256"] != digest:
                print(f"{src['id']}: present, but its sha256 differs from the recorded one")
                problems += not src.get("volatile")
            elif not src.get("sha256"):
                src["sha256"] = digest
                changed += 1
            continue
        if src.get("fetch") is False:
            print(f"{src['id']}: missing; download it by hand to data/raw/{src['path']}")
            problems += 1
            continue
        url = src.get("obtained_from") or src["url"]
        print(f"{src['id']}: downloading {url}", flush=True)
        try:
            download(url, dest)
        except robots.RobotsRefused as err:
            print(f"{src['id']}: not obtained; {err}")
            problems += 1
            continue
        except requests.RequestException as err:
            if not src.get("mirror"):
                print(f"{src['id']}: FAILED ({type(err).__name__}); not obtained")
                problems += 1
                continue
            # An archived copy counts only if its bytes are the recorded ones (checked below).
            print(f"{src['id']}: {type(err).__name__}; trying its mirror {src['mirror']}")
            try:
                download(src["mirror"], dest)
            except robots.RobotsRefused as refused:
                print(f"{src['id']}: not obtained; {refused}")
                problems += 1
                continue
        digest = sha256(dest)
        if src.get("sha256") and src["sha256"] != digest and not args.refresh:
            # The record stays: it says what the committed tables were built from.
            print(f"{src['id']}: downloaded, but its sha256 differs from the recorded one")
            problems += not src.get("volatile")
            continue
        if src.get("sha256") == digest:
            continue
        src["retrieved"] = dt.datetime.now(dt.UTC).date().isoformat()
        src["sha256"] = digest
        changed += 1
    if changed:
        save_manifest(manifest)
    print(f"{changed} entries recorded; {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
