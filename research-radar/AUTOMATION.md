# Automatic publishing for Research Radar

The automatic publisher is independent of the two ChatGPT scheduled tasks.
Its results appear in the same GitHub Pages dashboard, but it runs through
GitHub Actions and the paid OpenAI API.

## One-time setup (required)

1. Create an API key at https://platform.openai.com/api-keys .
   API requests are billed separately from ChatGPT subscriptions.
   You can configure API budgets in the OpenAI Platform billing settings.
2. Open the GitHub repository Actions-secrets page:
   https://github.com/physicalintuition/GPTstuff/settings/secrets/actions
3. Select **New repository secret**. Set:
   - Name: OPENAI_API_KEY
   - Secret: your API key
   Do not put the key in the web page, any .json file or a chat message.
4. Check GitHub **Settings > Actions > General**, and make sure workflows can
   write repository contents. This workflow explicitly requests contents: write.
5. Open https://github.com/physicalintuition/GPTstuff/actions/workflows/research-radar.yml
   and choose **Run workflow**. Test **papers** first; then **opportunities**.
   A successful result is a new commit to research-radar/data/ if a new item passed
   the high relevance threshold. Zero additions is a valid successful result.
6. Open https://physicalintuition.github.io/GPTstuff/research-radar/
   and click **Refresh feeds**. The tab checks for changes every five minutes
   while visible and on return to the browser tab.

## Scheduled runs

- Papers every **Monday** at about **08:17 Europe/Vienna**.
- Jobs and grants every **Monday** at about **08:27 Europe/Vienna**.

Both feeds therefore run once per week. GitHub may delay scheduled execution. If no strong new items are found,
the old feed remains unchanged and no new commit is created.

## Selection

Papers: recent arXiv records in gr-qc, hep-th, quant-ph and selected astro-ph;
strict relevance to BOTH of the user's research programmes: (1) q-desics
and quantum-connection geodesics; (2) SER/SSS quantisation, its metric and
connection operators, expectation values and uncertainties. Five at most,
zero when no strong match.

Opportunities: senior-level theoretical-physics roles located in Austria,
Germany, Slovenia, Slovakia, Czechia or Switzerland (or truly fully remote).
International grants are acceptable only with a realistic applicant/host
arrangement. Official URLs, known deadlines, eligibility and a precise
reason for fit are required; expired calls are removed from the results.
Strong relevance is preferred over numbers.

## Limitations / important distinctions

- These are **not** the same executions as the existing ChatGPT Tasks.
  You can pause those ChatGPT Tasks after checking that the separate GitHub
  workflow produces satisfactory results.
- The API is **not included** with ChatGPT Plus. Usage may incur costs.
- Some arXiv feeds or job pages may become temporarily unavailable; the script
  preserves existing results if searches fail to produce usable output.
- A successful run does not guarantee complete search coverage or factual
  accuracy. Verify official requirements before applying.
- GitHub Pages based on the existing public repository is also **public**.
  Do not publish private proposals or unpublished work in these JSON files.
- GitHub may automatically disable schedule triggers after 60 days without
  repository activity in a public repository.

## Controls

View history and failures in the GitHub **Actions** tab.
Use **Disable workflow** to pause all GitHub autopublishing; **Enable workflow**
to resume it. This is separate from pausing the ChatGPT Tasks.

Code:
- .github/workflows/research-radar.yml
- research-radar/scripts/update_feeds.py
- research-radar/data/papers.json
- research-radar/data/opportunities.json

No API key has been stored in this repository.
