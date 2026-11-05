"""Where these scripts read and write. They first ran with WORK = /tmp/pvo_fetch and the repository at a fixed
path; set PVO_WORK to a directory holding the saved pages (html/site/, from fetch.py) to run them elsewhere."""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..")) + os.sep
WORK = os.environ.get("PVO_WORK", "/tmp/pvo_fetch")
SITE = os.path.join(WORK, "html", "site")


def work(name: str) -> str:
    return os.path.join(WORK, name)
