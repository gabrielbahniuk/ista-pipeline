🇩🇪 **[Deutsche Version](README.de.md)**

<div align="center">

<img src="docs/images/logo-readme.svg" alt="Cartoon character wearing sunglasses made from two euro coins." width="100" height="65" />

# ISTA la vista

[![Generate ISTA report](https://img.shields.io/badge/GitHub_Actions-Generate_report-2088FF?logo=githubactions&logoColor=white)](https://github.com/gabrielbahniuk/ista-ecotrend-exporter/actions/workflows/report.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<!-- ista-report-nav:begin -->
<!-- ista-report-nav:end -->

## What

Understanding the financial impact of your yearly heating & showering behaviour, using data from ISTA EcoTrend.

![Demo: setup and viewing reports](docs/report-demo.gif)

## Why

**Useful:** Stop chasing numbers in the official app. See your year in one place.

**Quick:** Minimal setup. Only an ISTA account + a few Github clicks.

**Safe:** Keep your repository and data private. No need to expose any of it.

## Quick start

1. Click on **Use this template** → **Create a new repository**.
2. Choose a name, an optional description and select **private** visibility.
3. On the repository page, open **Settings** → **Secrets and variables** → **Actions**.
4. Click **New repository secret** and add two secrets (names must match exactly):

   | Name               | Value                                       |
   |--------------------|---------------------------------------------|
   | `ISTA_EMAIL`       | your ISTA EcoTrend account email            |
   | `ISTA_PASSWORD`    | that account’s password                     |


5. Open the **Actions** tab, select the **Generate ISTA report** workflow.
6. Click **Run workflow** → choose your default branch (often `main`) → **Run workflow**.

Open **`generated/reports/REPORT.md`** (or browse **`generated/reports/`**) on the repo home page for the Markdown report index.

### (Optional) just wait for the schedule

The same workflow runs automatically on the **18th of every month at 06:00 UTC**. Change the time in [.github/workflows/report.yml](.github/workflows/report.yml) if needed.
Why on this date? Usually ISTA sends out the consumption email between 13th and 16th each month.

## Disclaimer

- **ISTA unofficial API risk:** data is fetched with the unofficial library **`pyecotrend-ista`** ([upstream](https://github.com/Ludy87/pyecotrend-ista); pinned via git in [`requirements.txt`](requirements.txt)). ISTA may change endpoints or terms. **Use at your own risk.**

- **Not** a commercial app, hosted DB, realtime dashboard, or official ISTA product — just automation that commits reports into git in your private fork.

- **Secrets** (`ISTA_EMAIL` / `ISTA_PASSWORD`) live in GitHub — **never** screenshot the values.

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

### Tests

```bash
python -m pytest -q
```

## Environment variables (local only)

| Variable | Purpose |
|----------|---------|
| `ISTA_EMAIL`, `ISTA_PASSWORD` | ISTA login (live API fetch) |

## Security

- Never commit **`/.env`** or credentials in tracked source files.
- Rotate your ISTA password immediately if it was ever exposed.
- Ensure you use a **private** repository, so that your consumption data is not public.

