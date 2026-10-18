# app-reviews-pain-points

A small example that collects reviews from the **Apple App Store, Google Play and the Chrome Web Store in one run** and turns them into a pain-point report with Python.

It uses the [App Store, Google Play & Chrome Web Store Reviews Scraper](https://apify.com/tiandu-tech/apify-002-app-reviews) on Apify through the official [`apify-client`](https://pypi.org/project/apify-client/) package.

> Apple's public review feed has been unreliable since October 2026 and may return no reviews. Google Play and Chrome Web Store work normally. The scraper reports empty Apple feeds in its run status message, which `scrape_reviews.py` prints.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export APIFY_TOKEN=...   # Apify Console -> Settings -> API & Integrations
```

The token is read from the `APIFY_TOKEN` environment variable only. Never commit it; `.env` is git-ignored.

## 1. Collect reviews

Edit `input.example.json` (or make your own), then:

```bash
python scrape_reviews.py --input input.example.json --out data/reviews.json
```

`apps` accepts any mix of:

| Store | Example |
|---|---|
| Apple App Store | `310633997` or an `apps.apple.com` URL |
| Google Play | `com.whatsapp` or a `play.google.com` URL |
| Chrome Web Store | `ddkjiahejlhfcafbddmgiahcphecmpfh` or a `chromewebstore.google.com` URL |

Other input fields: `countries` (default `["us"]`, ignored for Chrome), `language` (default `en`, Google Play and Chrome), `maxReviewsPerApp` (default 100; Apple max 500 per app per country), `includeReviewerName` (masked, default off), `sentiment` (simple rule-based label, default off).

## 2. Analyze

```bash
python analyze_reviews.py --data data/reviews.json --outdir data
```

Prints an overview per store and app, the lowest-rated app versions, the most common complaint phrases and a theme ranking, and writes:

- `data/overview.csv`
- `data/pain_points_by_store.csv`
- `data/top_negative_reviews.csv`

Edit `THEMES` in `analyze_reviews.py` after reading the top phrases for your own apps.

## Output fields used

`store`, `appId`, `country`, `language`, `reviewId`, `rating`, `title`, `text`, `appVersion`, `thumbsUp`, `reviewedAt`, `developerReply`, plus optional `sentiment` and `reviewerName`.

## Notes

- Costs: the Actor has no fee of its own; runs use Apify platform credits on your account.
- Review text can contain personal details that reviewers typed themselves (emails and phone numbers are redacted by the Actor). Keep exports private and follow the privacy rules that apply to you.
- This project is not affiliated with Apple or Google.

## Try the analysis without an Apify account

`data/sample_reviews.json` contains four made-up reviews in the same format, so you can run:

```bash
python analyze_reviews.py --data data/sample_reviews.json --outdir /tmp/report
```
