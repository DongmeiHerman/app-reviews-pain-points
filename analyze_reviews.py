"""Turn an exported reviews dataset into a pain-point report.

Works on the JSON written by scrape_reviews.py or on a JSON export downloaded
from the Actor's output tab.

Usage:
    python analyze_reviews.py --data data/reviews.json --outdir data
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

STOP = set(
    """a an the and or but if to of in on for with is it this that was are be i me my we
    you your they them have has had not no just so very app extension""".split()
)

# Starter themes. Edit these after reading the top phrases for your own apps.
THEMES = {
    "crash / freeze": ["crash", "freez", "stuck", "not responding"],
    "login / account": ["login", "log in", "sign in", "account", "password"],
    "performance": ["slow", "lag", "battery", "memory"],
    "ads / paywall": ["ads", "subscription", "paywall", "premium"],
    "update broke it": ["update", "latest version", "new version"],
}


def phrases(text: str, n: int) -> list[str]:
    words = [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP]
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def tag(text: str) -> list[str]:
    t = text.lower()
    return [name for name, kws in THEMES.items() if any(k in t for k in kws)] or ["other"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/reviews.json")
    parser.add_argument("--outdir", default="data")
    parser.add_argument("--max-rating", type=int, default=2, help="Ratings at or below this count as negative")
    args = parser.parse_args()

    df = pd.read_json(args.data)
    if df.empty:
        print("No reviews in the dataset.")
        return
    df["text"] = df["text"].fillna("")
    df["thumbsUp"] = df["thumbsUp"].fillna(0)

    summary = (
        df.groupby(["store", "appId"])
        .agg(
            reviews=("reviewId", "count"),
            avg_rating=("rating", "mean"),
            share_negative=("rating", lambda s: (s <= args.max_rating).mean()),
            share_replied=("developerReply", lambda s: s.notna().mean()),
        )
        .round(2)
    )
    print("\n== Overview by store and app ==\n", summary)

    by_version = (
        df.dropna(subset=["appVersion"])
        .groupby(["appId", "appVersion"])
        .agg(n=("reviewId", "count"), avg_rating=("rating", "mean"))
        .query("n >= 5")
        .round(2)
        .sort_values(["appId", "avg_rating"])
    )
    print("\n== Lowest-rated versions (>= 5 reviews) ==\n", by_version.head(15))

    neg = df[(df["rating"] <= args.max_rating) & (df["text"].str.len() > 0)].copy()
    counts: Counter[str] = Counter()
    for t in neg["text"]:
        counts.update(phrases(t, 2))
        counts.update(phrases(t, 3))
    print("\n== Top complaint phrases ==")
    for phrase, c in counts.most_common(25):
        print(f"{c:4d}  {phrase}")

    neg["theme"] = neg["text"].map(tag)
    themed = neg.explode("theme")
    ranking = (
        themed.groupby(["store", "theme"])
        .agg(reviews=("reviewId", "count"), agreed=("thumbsUp", "sum"))
        .sort_values(["store", "reviews"], ascending=[True, False])
    )
    print("\n== Themes ==\n", ranking)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(outdir / "overview.csv")
    ranking.to_csv(outdir / "pain_points_by_store.csv")
    neg.sort_values("thumbsUp", ascending=False)[
        ["store", "appId", "appVersion", "rating", "thumbsUp", "text"]
    ].head(50).to_csv(outdir / "top_negative_reviews.csv", index=False)
    print(f"\nWrote overview.csv, pain_points_by_store.csv, top_negative_reviews.csv to {outdir}/")


if __name__ == "__main__":
    main()
