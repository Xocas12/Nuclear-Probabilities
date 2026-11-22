"""Command line for the playground (see nucprob/playground/__init__.py)."""

import argparse

import pandas as pd

from nucprob.playground.algos import ALGORITHMS, SLOW
from nucprob.playground.datasets import DATASETS, load, names
from nucprob.playground.evaluate import evaluate, explain, run_dir, transfer


def _data(args, name=None):
    d = load(name or args.dataset, include_sealed=getattr(args, "include_sealed", False))
    if args.features or args.drop:
        d = d.select(args.features, args.drop)
    return d


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m nucprob.playground")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="datasets and algorithms")

    def common(sp):
        sp.add_argument("-a", "--algos", default="fast", help="'all', 'fast' or a,b,c")
        sp.add_argument(
            "-f", "--features", help="families or columns to keep, e.g. population,military"
        )
        sp.add_argument("--drop", help="families or columns to leave out")

    r = sub.add_parser("run", help="cross-validate algorithms on a dataset")
    r.add_argument("-d", "--dataset", required=True)
    common(r)
    r.add_argument("--cv", default="spatial", choices=["spatial", "random", "country"])
    r.add_argument("-k", type=int, default=5)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument(
        "--include-sealed",
        action="store_true",
        help="use the sealed test blocks too (they are kept for the final scoring, M8)",
    )

    t = sub.add_parser("transfer", help="fit on one dataset, score another")
    t.add_argument("--train", required=True)
    t.add_argument("--test", required=True)
    common(t)

    e = sub.add_parser("explain", help="feature importance of one algorithm")
    e.add_argument("-d", "--dataset", required=True)
    e.add_argument("-a", "--algo", default="lgbm")
    e.add_argument("-f", "--features")
    e.add_argument("--drop")

    args = p.parse_args(argv)
    pd.set_option("display.width", 200)
    if args.cmd == "list":
        print("Datasets:")
        for n in names():
            print(f"  {n:45s} {DATASETS[n][0] if n in DATASETS else ''}")
        print(
            "\nAlgorithms ('all' and 'fast' leave out the slow ones: "
            + ", ".join(sorted(SLOW))
            + "):"
        )
        for n, a in ALGORITHMS.items():
            print(f"  {n:13s} {a.family:13s} {a.note}")
        return
    if args.cmd == "run":
        d = _data(args)
        print(d.summary())
        out = run_dir(f"{d.name}-{args.cv}")
        board = evaluate(d, args.algos, args.cv, args.k, args.seed, out=out)
        cols = ["algorithm", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "brier_mean", "base_rate"]
        print(board[cols].round(3).to_string(index=False))
        print(f"written to {out}")
    elif args.cmd == "transfer":
        tr, te = _data(args, args.train), _data(args, args.test)
        print(tr.summary())
        print(te.summary())
        board = transfer(tr, te, args.algos)
        print(
            f"shared features ({len(board.attrs['features'])}): {', '.join(board.attrs['features'])}"
        )
        print(board.round(3).to_string(index=False))
    elif args.cmd == "explain":
        d = _data(args)
        print(d.summary())
        print(explain(d, args.algo).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
