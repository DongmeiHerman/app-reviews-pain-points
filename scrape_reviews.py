"""Run the App Store, Google Play & Chrome Web Store Reviews Scraper and save the reviews.

Usage:
    export APIFY_TOKEN=...            # never hard-code it
    python scrape_reviews.py                          # uses input.example.json
    python scrape_reviews.py --input my_input.json --out data/reviews.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

ACTOR_ID = "tiandu-tech/apify-002-app-reviews"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default="input.example.json", help="Actor input JSON file")
    parser.add_argument("--out", default="data/reviews.json", help="Where to write the reviews")
    args = parser.parse_args()

    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN is not set. Export it in your shell (see .env.example).", file=sys.stderr)
        return 2

    run_input = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not run_input.get("apps"):
        print("Input must contain a non-empty 'apps' list.", file=sys.stderr)
        return 2

    client = ApifyClient(token)
    print(f"Starting {ACTOR_ID} for {len(run_input['apps'])} app(s)/extension(s)...")
    try:
        # apify-client 3.x returns a typed Run object (run.status); 2.x returned a dict (run["status"]).
        run = client.actor(ACTOR_ID).call(run_input=run_input)
    except ApifyApiError as exc:
        print(f"Apify API error: {exc}", file=sys.stderr)
        return 1
    if run is None:
        print("The run did not return any information.", file=sys.stderr)
        return 1
    print(f"Run {run.id} finished with status {run.status}")
    if run.status_message:
        # The Actor reports things like an empty Apple feed or a wrong ID here.
        print(f"Status message: {run.status_message}")

    items = list(client.dataset(run.default_dataset_id).iterate_items())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    per_store: dict[str, int] = {}
    for item in items:
        per_store[item.get("store", "?")] = per_store.get(item.get("store", "?"), 0) + 1
    print(f"Saved {len(items)} reviews to {out}  {per_store}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
