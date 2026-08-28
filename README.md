# Texas Rated — GitHub / Cloudflare-ready build

Fresh static rebuild for TexasRated.com, designed for GitHub Pages or Cloudflare Pages.

## Included
- Consumer-first homepage and category/location rankings
- Texas Rated Score terminology throughout
- 768 static, independently indexable company profile pages
- Unclaimed profiles have no outbound company website link
- Claimed Top-10 demo profiles use a normal outbound link; claimed profiles outside Top 10 use `rel="ugc nofollow"`
- Claim/profile-verification flow
- Verified-owner dashboard with leads, messages, competition, profile analytics and rank/score cards
- Live-emblem architecture using a single iframe URL per company; update generated widget data and the emblem changes without changing embed code
- TexasBusinessWorth.com handoff on claim page and owner dashboard
- Static market/category index pages for Austin, North Austin, South Austin and San Antonio
- Sitemap and robots.txt

## Important before production
`DEMO_MODE=True` is intentionally enabled in `scripts/build_site.py`. This outputs `noindex,nofollow` and blocks crawling in `robots.txt` so placeholder rankings cannot accidentally be indexed. After replacing the sample dataset with validated companies, set `DEMO_MODE=False` and rebuild.

The included company records and ranking numbers are **illustrative placeholder data** for design/development. Do not publish them as factual rankings. Replace `data/companies.json` with validated businesses and finalize the production scoring methodology/data ingestion.

## Regenerate static pages
Run:

```bash
python3 scripts/build_site.py
```

The generator creates all company pages, market/category ranking pages, widget pages and the sitemap.

## Production backend still required for
- authentication / owner verification
- database-backed profile edits
- lead ingestion + email delivery
- on-site messaging
- real-time analytics
- automated scoring/rank updates
- owner notifications

## Domain
The public root is `https://texasrated.com/`. A `CNAME` file is included for GitHub Pages; Cloudflare can provide DNS/proxying or deploy the repository directly with Cloudflare Pages.
