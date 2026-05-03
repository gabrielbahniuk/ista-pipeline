🇬🇧 **[English version](README.md)**

<div align="center">

<img src="docs/images/logo-readme.svg" alt="Stilisierte Figur mit Euromünzen als Brille." width="100" height="65" />

# ISTA EcoTrend Reporter

[![ISTA EcoTrend Reporter](https://img.shields.io/badge/GitHub_Actions-ISTA_EcoTrend_Reporter-2088FF?logo=githubactions&logoColor=white)](https://github.com/gabrielbahniuk/ista-ecotrend-exporter/actions/workflows/report.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<!-- ista-report-nav:begin -->
<!-- ista-report-nav:end -->

Holt Heiz- und Warmwasserdaten aus ISTA EcoTrend wie die App, committet Markdown, Charts und eine CSV unter `generated/`. Am sinnvollsten mit **privatem** Repo.

![Demo: Einrichtung und Reports ansehen](docs/report-demo.gif)

## Einrichtung

1. **Use this template** → **Create a new repository** (Name, **Private** Sichtbarkeit empfohlen).
2. **Settings** → **Secrets and variables** → **Actions** → Secrets anlegen (Namen exakt):

   | Name | Wert |
   |------|------|
   | `ISTA_EMAIL` | ISTA-EcoTrend-Login-E-Mail |
   | `ISTA_PASSWORD` | Passwort |

3. **Actions** → **ISTA EcoTrend Reporter** → **Run workflow** auf dem Standard-Branch.

Sobald die Reports bereit sind, oben **Neuesten Report öffnen →** nutzen (oder **`generated/reports/REPORT.md`** im Repo).

Geplanter Lauf jeden Monat am **18., 06:00 UTC** (bei Bedarf anpassen; ISTA-Mail oft bis zum 16.).




## Disclaimer

- Zugriff auf EcoTrend hier über keine offiziellen, garantiert stabilen Schnittstellen der ISTA — das kann jederzeit ausfallen. **Kein ISTA-Produkt, keine Freigabe, keine Zusicherung, kein gehosteter Dienst** — nur Automation in deinem Fork. **Eigene Verantwortung.**
- Zugangsdaten und Verbrauchsdaten sensibel behandeln: Repo **privat** halten, **`.env`** niemals committen, **`ISTA_EMAIL`** / **`ISTA_PASSWORD`** nicht in Issues oder Screenshots. Passwort **rotieren**, falls es geleakt wurde.

## Lokal (optional)

```bash
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip && python -m pip install -r requirements.txt
cp .env.example .env   # ISTA_EMAIL und ISTA_PASSWORD setzen
set -a && source .env && set +a && python -m src.pipeline.report
python -m pytest -q
```
