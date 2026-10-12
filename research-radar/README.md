# Research Radar

A two-panel, lightweight physics research dashboard with a dark **Physics Tasks** sidebar and live-refreshing content pane. This folder is separate from the existing paperpitch and football pages.

## Sections
- **Overview** for all published results
- **New Papers** for carefully selected physics preprints; include SER quantisation as well as q-desics
- **Jobs & Grants** for senior positions in Austria, Germany, Slovenia, Slovakia, Czechia and Switzerland, and eligible international funding calls

The page polls the two JSON data files every five minutes while the tab is open, and checks again when the tab becomes active. The **Refresh feeds** button checks immediately. Search, filters, **Save**, and **Mark reviewed** all work in the browser; saved/reviewed states are stored in browser localStorage, not sent to GitHub.

## Publishing on GitHub Pages
This dashboard lives at `research-radar/index.html` on `main`. If repository Pages is configured to deploy the `main` branch root, it appears at:

https://physicalintuition.github.io/GPTstuff/research-radar/

If Pages has not been enabled, a repository administrator must open **Settings → Pages**, select **Deploy from a branch → main → /(root)**, and save. GitHub Pages content is publicly accessible, so do not put private notes, unpublished research or personal information into these JSON files.

## Feed data
To publish a new vetted report, edit the following files and commit changes to `main`:

- `data/papers.json`: `{ "updatedAt":"2026-10-12T08:00:00Z", "items":[...] }`
- `data/opportunities.json`: `{ "updatedAt":"2026-10-12T08:00:00Z", "jobs":[...], "grants":[...] }`

**Paper item example (schema only, not a real publication):**

```json
{
  "id": "arxiv-YYYY-NNNNN",
  "title": "Verified paper title",
  "authors": "A. Author, B. Author",
  "date": "2026-10-12",
  "url": "https://arxiv.org/abs/YYYY.NNNNN",
  "priority": "High relevance",
  "topic": "SER quantisation",
  "summary": "2–4 sentences about the core scientific idea.",
  "relevance": "Precisely why it matters for q-desics and/or SER quantisation."
}
```

**Job/grant item example (schema only):**

```json
{
  "id": "stable-source-identifier",
  "title": "Verified programme or job name",
  "institution": "University or institution for jobs",
  "funder": "Agency for grants",
  "country": "Austria",
  "date": "2026-10-12",
  "deadline": "2026-11-12",
  "url": "https://official.example/opportunity",
  "priority": "High relevance",
  "eligibility": "Eligibility checked against the official call.",
  "relevance": "Reason for fit and important caveats.",
  "notes": "Useful details (optional)."
}
```

A record must contain `id`, `title` and an HTTPS `url` to appear. Avoid duplicated IDs. No filler content should be published merely to populate the page. Remove expired positions and obsolete grants on later updates.

## Important integration limitation
This webpage cannot read private ChatGPT task results by itself. Scheduled ChatGPT tasks do not natively commit their output into a GitHub repository. **Updates to the GitHub JSON files require a separate integration or an explicit GitHub update performed in a ChatGPT conversation.** GitHub Pages reflects published file changes after deployment. The dashboard's refresh is not equivalent to running the research tasks.

## Preview locally
Run `python3 -m http.server 8000` from the `research-radar` folder, then visit http://localhost:8000.

No third-party JavaScript dependencies are included. Relevance voting calls the shared service described below; hosting infrastructure may set its own operational cookies.

## Shared relevance votes

Each paper has − (less relevant), 0 (neutral), and + (relevant) buttons with shared counts and bars. No sign-in is required. The service stores one vote per paper and hashed random browser voting key. Selecting another option replaces the vote; selecting the active option removes it. Clearing browser storage or using another browser creates a new identity, so this is intended for a trusted internal group, not an abuse-resistant public poll. The page and voting endpoint are publicly reachable.

The client keeps its random voting key in localStorage (`radar-voter-key-v1`). Counts refresh once per minute while visible and on Refresh feeds. Counts are stored centrally in a Sites D1 database, not in the JSON feeds. API: https://research-radar-votes.flowygoose1.chatgpt.site/api/votes . Sites project: `appgprj_6accd23ff8608191bfb8a09055c3e49d`. Backend source is maintained in that Sites project's source repository. The endpoint validates paper IDs against `data/papers.json`, supports CORS for `https://physicalintuition.github.io`, and never returns other voters' identifiers.
