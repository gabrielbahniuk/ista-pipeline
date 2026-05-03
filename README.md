🇩🇪 **[Deutsche Version](README.de.md)**

<div align="center">

<img src="docs/images/logo-readme.svg" alt="Cartoon character wearing sunglasses made from two euro coins." width="100" height="65" />

# ISTA EcoTrend Reporter

[![ISTA EcoTrend Reporter](https://img.shields.io/badge/GitHub_Actions-ISTA_EcoTrend_Reporter-2088FF?logo=githubactions&logoColor=white)](https://github.com/gabrielbahniuk/ista-ecotrend-exporter/actions/workflows/report.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<!-- ista-report-nav:begin -->
<h3 align="center"><a href="./generated/reports/REPORT.md">Open Latest Report →</a></h3>
<p align="center"><sup>Last updated · 03.05.2026 12:01</sup></p>
<!-- ista-report-nav:end -->

Pulls ISTA EcoTrend heating and hot-water data like the app does, then commits Markdown, charts, and a CSV under `generated/`. Best with a **private** repo.

![Demo: setup and viewing reports](docs/report-demo.gif)

## Setup

1. **Use this template** → **Create a new repository** (name, **Private** visibility is recommended).
2. **Settings** → **Secrets and variables** → **Actions** → add secrets (names exact):

   | Name | Value |
   |------|--------|
   | `ISTA_EMAIL` | ISTA EcoTrend login email |
   | `ISTA_PASSWORD` | that password |

3. **Actions** → **ISTA EcoTrend Reporter** → **Run workflow** on your default branch.

Once the reports are ready, use **Open Latest Report →** above (or **`generated/reports/REPORT.md`** in the repo).

Report scheduled monthly on **18th, 06:00 UTC** (change if you like; ISTA email is often by the 16th).




## Disclaimer

- EcoTrend access here relies on undocumented or unofficial endpoints; they can stop working anytime. **Not an ISTA product, endorsement, warranty, or hosted service** — just automation in your fork. Use at **your own risk**.
- Credentials and meter-style data are sensitive: keep the repo **private**, never commit **`.env`**, and never post **`ISTA_EMAIL`** / **`ISTA_PASSWORD`** in issues or screenshots. Rotate the password if it was leaked.

## Local (optional)

```bash
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip && python -m pip install -r requirements.txt
cp .env.example .env   # set ISTA_EMAIL and ISTA_PASSWORD
set -a && source .env && set +a && python -m src.pipeline.report
python -m pytest -q
```
