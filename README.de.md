🇬🇧 **[English version](README.md)**

<div align="center">

<img src="docs/images/logo-readme.svg" alt="Stilisierte Figur mit Euromünzen als Brille." width="100" height="65" />

# ISTA la vista

[![Generate ISTA report](https://img.shields.io/badge/GitHub_Actions-Generate_report-2088FF?logo=githubactions&logoColor=white)](https://github.com/gabrielbahniuk/ista-ecotrend-exporter/actions/workflows/report.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

<!-- ista-report-nav:begin -->
<!-- ista-report-nav:end -->

## Was

Einordnung der finanziellen Auswirkungen deines Heiz- und Warmwasserverhaltens über das Jahr, mit Daten aus der ISTA EcoTrend App.

![Demo: Einrichtung und Reports ansehen](docs/report-demo.gif)

## Warum

**Nützlich:** Schluss mit dem Zahlen-Suchen in der offiziellen App.

**Schnell:** Minimales Setup. Nur ein ISTA-Konto und ein paar Klicks auf **GitHub**.

**Sicher:** Repository und Daten **privat** halten. Nichts muss nach außen.

## Schnellstart

1. **Use this template** → **Create a new repository**.
2. Namen wählen, optional Beschreibung, Sichtbarkeit **private** empfohlen.
3. Im Repo: **Settings** → **Secrets and variables** → **Actions**.
4. **New repository secret** — zwei Secrets anlegen (Namen exakt so):

   | Name               | Wert                                        |
   |--------------------|---------------------------------------------|
   | `ISTA_EMAIL`       | deine ISTA-EcoTrend-Login-E-Mail            |
   | `ISTA_PASSWORD`    | das Passwort dieses Kontos                  |

5. Tab **Actions** → Workflow **Generate ISTA report**.
6. **Run workflow** → Branch (idR `main`) → **Run workflow**.

Im Repo **`generated/reports/REPORT.md`** öffnen (oder Ordner **`generated/reports/`** durchsuchen) für den Report‑Index.

### (Optional) einfach warten

Derselbe Workflow läuft automatisch am **18. jedes Monats um 06:00 UTC**. Zeitpunkt in [.github/workflows/report.yml](.github/workflows/report.yml) anzupassen. 
Warum an dem Tag? ISTA schickt die Verbrauchs-Mail meist zwischen dem **13. und 16.** des Monats.

## Disclaimer

- **Inoffizielle ISTA-API:** Daten kommen über die Bibliothek **`pyecotrend-ista`** ([Upstream](https://github.com/Ludy87/pyecotrend-ista); in [`requirements.txt`](requirements.txt) per Git gepinnt). ISTA kann Schnittstellen oder Bedingungen ändern. **Nutzung auf eigenes Risiko.**

- **Kein** kommerzielles Produkt, keine gehostete Datenbank, kein Echtzeit-Dashboard und **kein** offizielles ISTA-Angebot — nur Automation, die Reports **in Git** in **deinem privaten Fork** committet.

- **Secrets** (`ISTA_EMAIL` / `ISTA_PASSWORD`) liegen bei GitHub — **niemals** die Werte in Screenshots zeigen.

## Lokal entwickeln (optional)

Reports auf dem eigenen Rechner erzeugen:

### 1) Virtualenv und Abhängigkeiten

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 2) Umgebungsvariablen

```bash
cp .env.example .env
# .env bearbeiten — ISTA_EMAIL und ISTA_PASSWORD setzen
set -a && source .env && set +a
```

### 3) Report erstellen

```bash
python -m src.pipeline.report
```

### Tests

```bash
python -m pytest -q
```

## Umgebungsvariablen (nur lokal)

| Variable | Zweck |
|----------|--------|
| `ISTA_EMAIL`, `ISTA_PASSWORD` | ISTA-Login (Live-API) |

## Sicherheit

- Niemals **`/.env`** oder Zugangsdaten in versionierten Dateien committen.
- ISTA-Passwort sofort rotieren, wenn es je geleakt wurde.
- Repo **privat** nutzen, damit Verbrauchsdaten nicht öffentlich sind.
