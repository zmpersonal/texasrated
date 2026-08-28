# TexasRated.com — real-data static build
Cloudflare redeploy
GitHub / Cloudflare-ready static site for **Texas Rated**.

## What changed
- Uses the supplied Texas emblem/logo (`assets/logo.png`) and favicon.
- Rebuilt Popular Rankings with custom service medallions instead of emoji.
- Rebuilt Texas Markets with branded market cards.
- `categories.html` is a true category index: all 16 service categories, each with its current top five companies.
- Navigation: Rankings / Categories / Scores / Fastest Rising / Methodology / For Businesses.
- `scores.html` replaces the prior Independent Companies concept.
- Real company seed dataset: `data/companies.csv` (public listing snapshot dated 2026-08-28).
- Every company in the CSV automatically receives a static, indexable `/company/<slug>.html` page.
- Unclaimed companies do **not** receive an outbound website link.
- Claimed + verified companies can activate their website link; Top-10 claimed profiles can use a direct editorial link, while other owner-supplied links are generated as `rel="ugc nofollow"`.
- Claim page retains TexasBusinessWorth.com as the separate private valuation handoff.
- Fastest Rising is no longer fabricated. It appears only after at least two historical score snapshots exist.

## Texas Rated Score (launch model)
The launch score is intentionally auditable:
- up to **85 points**: Bayesian-adjusted public rating / reputation
- up to **10 points**: review-depth confidence (log scaled)
- up to **5 points**: verified profile data after a business claims its page

Paying, accepting leads, installing the emblem or linking to Texas Rated does not add score points.

## Refresh or add companies
`data/companies.csv` is the source of truth. **The build script never overwrites it.**

### Add/update companies via import CSV
Start with:

`data/import-template.csv`

Then run:

```bash
python3 scripts/import_companies.py data/new-companies.csv --build
```

The importer:
1. matches by `external_id` if supplied;
2. otherwise matches by normalized phone;
3. otherwise matches by company name + city;
4. updates matching public fields while preserving owner fields when the import field is blank;
5. appends new companies;
6. `--build` automatically creates their company pages, updates rankings/category cards, exports JSON and updates the sitemap.

Pipe-delimit multiple categories/markets, e.g.:

```text
categories: HVAC|Plumbing
markets: Austin|North Austin
```

### Rebuild without importing

```bash
python3 scripts/build_site.py
```

### Record a score snapshot for real momentum rankings
Run this after each scheduled data refresh:

```bash
python3 scripts/snapshot_scores.py
python3 scripts/build_site.py
```

`fastest-rising.html` remains in a transparent “collecting history” state until at least two snapshot dates exist.

## Data freshness
Current public rating/review values are a snapshot collected **2026-08-28** and are displayed as such. These values should be refreshed on a recurring schedule before marketing the rankings as current.

## Backend features still represented as UI/prototype
The static package contains owner/claim/dashboard UI, but production versions of these require a backend:
- authentication and ownership verification
- database-backed profile editing
- lead routing + email delivery
- on-site messaging
- analytics
- server-side/live emblem state

Cloudflare Workers + D1/KV are a sensible next layer without changing the public static page architecture.
