# AdVerdict decks

Built 2026-11-14 for Mykolas Belickas's LinkedIn campaign (offer: +30% revenue by keeping and upselling clients, no results no pay, Stickytales $80k+ last quarter).
Same engine as SharePay / Vistamails (reveal.js 1280x720 + phone mode). AdVerdict look taken from adverdict.io: bg #0c0a09, cream #f4f1ea, emerald #34d399, Archivo / Inter / JetBrains Mono, mark in `assets/logos/adverdict_mark.svg`.

4 slides: Cover (AdVerdict x lead, sample verdict card) · How we work (message 1 offer) · What it did for Stickytales · Let's talk (Calendly belickas-mykolas).
Only the lead slots change: company, first and last name, optional logo, sender.

## Building a deck (from `_src`)
1. `py tools/slug.py "<Company>" <First> <Last>` -> slug
2. `specs/<slug>.json` with slug, company, first_name, last_name (fields documented in `build.py`)
3. Optional logo: `py tools/logo.py <slug> "<Company>" https://<domain> --bg #0c0a09 --out ../assets/leadlogos --preview ../assets/leadlogos/_preview --spec specs/<slug>.json --badge-key logo_badge --on-none remove`
4. `py build.py specs/<slug>.json` -> `../<slug>/index.html`

## All leads prebuilt (2026-11-15)
Every lead in the two AdVerdict HeyReach campaigns (Mykolas list 1150153, Augustas list 1150152) already has a deck.
A request for a lead's deck is a lookup: `py _src/tools/all_leads.py find <name or company>`.
Refresh for new leads, from `_src`: `py tools/all_leads.py pull`, then `shots`, then `build`, then commit and push.
Auto specs carry `"auto": true` and are rewritten each build; hand-made specs (no `auto`) are never touched and win for the same person.
Junk sites (parked, expired, 404, placeholder, a builder or platform domain) never go on a cover; the deck shows the verdict card instead.
The lead index (lead -> URL, LinkedIn, HeyReach id) lives outside this public repo: `AIOS\brain\notes\sales-resources\adverdict\deck_index.csv` and Drive Sales Resources / AdVerdict.

## Hosting
Repo `ThomasTzouridis/adverdict-decks` (public), GitHub Pages on `main` /, custom domain `adverdict-cases.com` (bought 2026-11-15 on Spaceship account ACTISCALE, auto-renew on, basic DNS: 4 GitHub A records + `www` CNAME to thomastzouridis.github.io). Deck URL: `https://adverdict-cases.com/<slug>/`. Push = live in about a minute. No tracking beacon yet.
