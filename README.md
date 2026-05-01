<div align="center">

<img src="docs/images/logo-readme.svg" alt="Cartoon character wearing sunglasses made from two euro coins." width="100" height="65" />

# hasta la vISTA, baby

[![Generate ISTA report](https://img.shields.io/badge/GitHub_Actions-Generate_report-2088FF?logo=githubactions&logoColor=white)](https://github.com/gabrielbahniuk/ista-pipeline/actions/workflows/report.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## What

Fetches data from your **ISTA EcoTrend** account, normalizes it, and generates Markdown reports (**`REPORT.md`** as an index plus **`REPORT_YYYY.md`** per year) and SVG charts under **`assets/charts/`**. No database or data collection. Everything stays under your control in the repository files. A **private fork** is recommended. Consumption and costs end up in git history.


## Why

Stop hunting numbers in the EcoTrend UI. Get consumption + costs as **Markdown + charts** in **your private** repo instead.

- **3 minutes to wire up**, then it can run quietly every month without you babysitting exports.
- **Year-over-year at a glance.** Tables and charts you actually want to scroll.


---

## Quick start

You do not need Python or a terminal on your machine — only **GitHub** and **ISTA**.

### Step by step

1. **Fork this repository** (preferably **private**, so only you can see reports with your real data).
2. In your fork, open **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** and add two secrets (names must match exactly):

   | Name               | Value                                       |
   |--------------------|---------------------------------------------|
   | `ISTA_EMAIL`       | your ISTA EcoTrend account email            |
   | `ISTA_PASSWORD`    | that account’s password                     |

4. Make sure **GitHub Actions** is enabled on the fork: **Settings** → **Actions** → **General** → allow workflows to run (forks sometimes have Actions restricted by default).
5. Open the **Actions** tab, select the **Generate ISTA report** workflow.
6. Click **Run workflow** → choose your default branch (often `main`) → **Run workflow**.

When it finishes successfully, the repo will show updated **`REPORT.md`** (year index), **`REPORT_2026.md`** (and other years as data allows), and **`assets/charts/`**. Open the `.md` files right on GitHub.

### Or just wait for the schedule

The same workflow runs automatically on the **18th of every month at 06:00 UTC**. Change the time in [.github/workflows/report.yml](.github/workflows/report.yml) if needed.
Why on this date? Normally ISTA sends out the monthly consumption email between 13th and 16th.

---

## How it looks like?

TODO tutorial and examples....

## Who this is for

**A good fit if you:**

- Check ISTA EcoTrend often (e.g. after the monthly email).
- Like a year-over-year view with fancy charts and tables, without maintainance costs.
- Will not be deeply sad if ISTA changes their API and the app breaks. (We can always fix it though)
- Want to contribute in any form. 

**Probably not worth it if you:**

- Open the EcoTrend app once or twice a year.
- Do not want to touch GitHub (forks, Actions, secrets) at all.
- Need an official or guaranteed access. 

---

## Disclaimer & scope

- **ISTA unofficial API risk:** data is fetched with the unofficial library **`pyecotrend-ista`** ([upstream](https://github.com/Ludy87/pyecotrend-ista); pinned via git in [`requirements.txt`](requirements.txt)). ISTA may change endpoints or terms. **Use at your own risk.**

- **Not** a commercial app, hosted DB, realtime dashboard, or official ISTA product — just automation that commits reports **into git** in **your private fork**.

- **Secrets** (`ISTA_EMAIL` / `ISTA_PASSWORD`) live in GitHub — **never** screenshot the values.

---

## How it works (short)

- **Extract**: `pyecotrend-ista` client  
- **Transform**: `normalize()`  
- **Report**: `python -m src.pipeline.report` (on GitHub Actions runners)  
- **CI**: [.github/workflows/report.yml](.github/workflows/report.yml) — monthly cron (18th, 06:00 UTC) plus **Run workflow** anytime  

---

## Local development (optional)

To generate reports on your computer:

### 1) Virtualenv and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 2) Environment variables

```bash
cp .env.example .env
# edit .env — set ISTA_EMAIL and ISTA_PASSWORD
set -a && source .env && set +a
```

### 3) Generate the report

```bash
python -m src.pipeline.report
```

Open `REPORT.md` and `REPORT_YYYY.md`; charts live in `assets/charts/`.

Offline using a JSON shaped like `ista_dump` (`{ "<uuid>": { "consumption": … } }`):

```bash
REPORT_FIXTURE_JSON=/path/to/dump.json python -m src.pipeline.report
```

### Tests

```bash
python -m pytest -q
```

## Environment variables (local only)

| Variable | Purpose |
|----------|---------|
| `ISTA_EMAIL`, `ISTA_PASSWORD` | ISTA login (live API fetch) |
| `PIPELINE_SOURCE` | defaults to `ista` |
| `PIPELINE_TIMEZONE` | defaults to `UTC` |
| `PIPELINE_DEBUG` | set `true` for extra extract diagnostics |
| `REPORT_FIXTURE_JSON` | path to offline JSON instead of the API |

## Security

- Never commit **`/.env`** or credentials in tracked source files.
- Rotate your ISTA password immediatelz if it was ever exposed.
- After forking, make sure you use a **private** repository, so that your  consumption data is only visible to you :)
