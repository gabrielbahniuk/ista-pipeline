from __future__ import annotations

import re
from calendar import month_abbr
from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from src.pipeline.report_data import CHART_METRIC_PAIRS, compute_chart_series
from src.pipeline.schemas import EnrichedRecord

REL_CHART_ROOT = "assets/charts"

_COL_PAGE = "#f1f5f9"
_COL_AXIS = "#64748b"
_COL_TITLE = "#0f172a"
_COL_GRID = "#e2e8f0"
_BAR_YOU = "#0f766e"
_BAR_AVG = "#d97706"
_BAR_EDGE = "#ffffff"

_LEGEND_AVG_SERIES = "Average consumption"

# Euro on the benchmark bar assumes “cost scales with consumption”. With near-zero own
# use (fixes, base charges) the implied €/kWh blows up — skip the label when stretch is huge.
_MAX_BENCH_TO_YOU_RATIO_FOR_EUR_ESTIMATE = 10.0
_EUR_LABEL_PAD_PT = 4
_YLIM_PAD_GROUPED = 1.16
_YLIM_PAD_SINGLE = 1.12


def _safe_filename(metric: str, year: int) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", metric.strip(), flags=re.ASCII)
    return f"{cleaned}_{year}.svg"


def _canon_measurement_unit(unit: str) -> str:
    """Lowercase slug for comparisons (m³/m3→m3; Einheiten→units). Unknown kept lowercased."""
    t = unit.strip().lower().replace("³", "3")
    if t in ("m3", "m³"):
        return "m3"
    if t == "kwh":
        return "kwh"
    if t in ("units", "einheiten"):
        return "units"
    return t


def _format_axis_unit(unit: str) -> str:
    slug = _canon_measurement_unit(unit)
    if slug == "m3":
        return "m³"
    if slug == "kwh":
        return "kWh"
    if slug == "units":
        return "Units"
    return unit


def _ylabel(metric_key: str, consumption_unit: str | None) -> str:
    if consumption_unit:
        return _format_axis_unit(consumption_unit)
    if metric_key == "hot_water":
        return "m³"
    if metric_key == "heating":
        return "Units"
    return "Consumption"


def _units_compatible(u1: str, u2: str) -> bool:
    return _canon_measurement_unit(u1) == _canon_measurement_unit(u2)


def _representative_unit(
    enriched: list[EnrichedRecord], year: int, metric_key: str
) -> str | None:
    rows = sorted(
        (
            r
            for r in enriched
            if int(r["year"]) == year and str(r["metric"]) == metric_key
        ),
        key=lambda r: int(r["month"]),
    )
    if not rows:
        return None
    return str(rows[0]["unit"])


def _fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-6:
        return str(int(round(v)))
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _month_tick_labels(months: list[int]) -> list[str]:
    return [month_abbr[m] for m in months]


def _euro_bar_label(ax, container, labels: list[str], *, fontsize: float) -> None:
    """€ on top-center of each bar (bar_label forbids ha/va; annotate gives exact placement)."""
    for patch, lbl in zip(container.patches, labels, strict=True):
        raw = lbl.strip()
        if not raw:
            continue
        cx = patch.get_x() + patch.get_width() / 2.0
        top = patch.get_height() + patch.get_y()
        ax.annotate(
            raw,
            xy=(cx, top),
            xytext=(0, _EUR_LABEL_PAD_PT),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=fontsize,
            color=_COL_TITLE,
            fontweight="500",
        )


def _estimated_eur_from_usage(
    you_cons: float, you_cost_eur: float | None, bench_cons: float
) -> float | None:
    """Optional € on the average bar: invoice heating cost × (avg cons ÷ your cons).

    Omitted when avg/your ratio is above _MAX_BENCH_TO_YOU_RATIO_FOR_EUR_ESTIMATE so
    fixed charges + tiny measured use do not produce nonsense (e.g. 13 € → 839 €).
    """
    if you_cost_eur is None:
        return None
    if you_cons <= 0:
        return None
    ratio = bench_cons / you_cons
    if ratio > _MAX_BENCH_TO_YOU_RATIO_FOR_EUR_ESTIMATE:
        return None
    return you_cost_eur * ratio


@contextmanager
def _chart_style():
    with plt.rc_context(
        {
            "figure.facecolor": _COL_PAGE,
            "axes.facecolor": _COL_PAGE,
            "axes.edgecolor": _COL_GRID,
            "axes.linewidth": 0.0,
            "axes.labelcolor": _COL_AXIS,
            "axes.titlecolor": _COL_TITLE,
            "text.color": _COL_AXIS,
            "xtick.color": _COL_AXIS,
            "ytick.color": _COL_AXIS,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "600",
            "axes.labelsize": 10,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "legend.frameon": False,
            "legend.fontsize": 9,
        }
    ):
        yield


def write_combo_chart_svg(
    consumption_key: str,
    cost_key: str,
    chart_title: str,
    year: int,
    series: dict[tuple[int, str], tuple[list[int], list[float]]],
    charts_dir: Path,
    enriched: list[EnrichedRecord],
) -> Path | None:
    """Consumption per month (bar); bar tops show EUR cost when available.

    Optional second bar per month when API benchmark exists and shares the same unit.
    """
    cons = series.get((year, consumption_key))
    cost = series.get((year, cost_key))
    bench_pair = series.get((year, f"{consumption_key}_benchmark"))

    cons_map: dict[int, float] = {}
    if cons:
        sm, sv = cons
        cons_map = dict(zip(sm, sv, strict=True))

    bench_map: dict[int, float] = {}
    if bench_pair:
        bm, bv = bench_pair
        bench_map = dict(zip(bm, bv, strict=True))

    cost_map: dict[int, float] = {}
    if cost:
        cm, cv = cost
        cost_map = dict(zip(cm, cv, strict=True))

    months = sorted(cons_map.keys())
    if not months:
        return None

    cons_unit = _representative_unit(enriched, year, consumption_key)
    bench_unit = _representative_unit(enriched, year, f"{consumption_key}_benchmark")
    use_grouped = (
        bool(bench_map)
        and cons_unit is not None
        and bench_unit is not None
        and _units_compatible(cons_unit, bench_unit)
    )

    vals = [cons_map[m] for m in months]
    bar_labels: list[str] = []
    for m in months:
        if m in cost_map:
            bar_labels.append(f"{_fmt_num(cost_map[m])} €")
        else:
            bar_labels.append("")

    def bench_bar_label(month: int, you_cons: float) -> str:
        if month not in bench_map:
            return ""
        est = _estimated_eur_from_usage(
            you_cons, cost_map.get(month), bench_map[month]
        )
        if est is None:
            return ""
        return f"{_fmt_num(est)} €"

    charts_dir.mkdir(parents=True, exist_ok=True)
    out_file = charts_dir / _safe_filename(consumption_key, year)
    tick_labels = _month_tick_labels(months)
    label_fs = max(7, min(9, int(110 / max(len(months), 1))))

    with _chart_style():
        fig, ax = plt.subplots(figsize=(10, 5.1))
        fig.patch.set_facecolor(_COL_PAGE)
        ax.set_facecolor(_COL_PAGE)

        x_index = list(range(len(months)))
        width = 0.36 if use_grouped else 0.58

        if use_grouped:
            for i, m in enumerate(months):
                cost_lbl = bar_labels[i]
                r1 = ax.bar(
                    x_index[i] - width / 2,
                    vals[i],
                    width,
                    color=_BAR_YOU,
                    edgecolor=_BAR_EDGE,
                    linewidth=1.0,
                    zorder=2,
                )
                if cost_lbl:
                    _euro_bar_label(ax, r1, [cost_lbl], fontsize=label_fs)
                if m in bench_map:
                    r2 = ax.bar(
                        x_index[i] + width / 2,
                        bench_map[m],
                        width,
                        color=_BAR_AVG,
                        edgecolor=_BAR_EDGE,
                        linewidth=1.0,
                        zorder=2,
                    )
                    b_lbl = bench_bar_label(m, vals[i])
                    if b_lbl:
                        _euro_bar_label(ax, r2, [b_lbl], fontsize=label_fs)
            handles = [
                Patch(facecolor=_BAR_YOU, edgecolor=_BAR_EDGE, linewidth=1, label="You"),
                Patch(
                    facecolor=_BAR_AVG,
                    edgecolor=_BAR_EDGE,
                    linewidth=1,
                    label=_LEGEND_AVG_SERIES,
                ),
            ]
            ax.legend(
                handles=handles,
                loc="upper left",
                bbox_to_anchor=(0, -0.14),
                ncol=2,
                labelcolor=_COL_TITLE,
                columnspacing=1.4,
                handletextpad=0.6,
            )
            fig.subplots_adjust(bottom=0.2)
        else:
            bars = ax.bar(
                x_index,
                vals,
                width=width,
                color=_BAR_YOU,
                edgecolor=_BAR_EDGE,
                linewidth=1.0,
                zorder=2,
            )
            _euro_bar_label(ax, bars, bar_labels, fontsize=label_fs)
            fig.subplots_adjust(bottom=0.12)

        ax.set_xticks(x_index, tick_labels, fontsize=10)
        ax.set_xlabel("Month", fontsize=10, color=_COL_AXIS, labelpad=8)
        ax.set_ylabel(_ylabel(consumption_key, cons_unit), fontsize=10, color=_COL_AXIS, labelpad=8)

        ax.set_title(f"{chart_title} — {year}", loc="left", pad=14)
        ax.yaxis.grid(True, linestyle="-", linewidth=0.9, color=_COL_GRID, zorder=0)
        ax.set_axisbelow(True)
        ax.set_ylim(bottom=0)

        ymin, ymax = ax.get_ylim()
        ax.set_ylim(
            ymin, ymax * (_YLIM_PAD_GROUPED if use_grouped else _YLIM_PAD_SINGLE)
        )

        plt.savefig(out_file, format="svg", facecolor=_COL_PAGE, edgecolor="none", bbox_inches="tight", pad_inches=0.12)
        plt.close(fig)

    return out_file


def generate_chart_assets(
    enriched: list[EnrichedRecord],
    charts_dir: Path,
) -> dict[tuple[int, str], str]:
    """One combined chart per (year, consumption metric); labels on bars show cost in € only."""
    paths: dict[tuple[int, str], str] = {}
    series = compute_chart_series(enriched)

    years_needed = sorted({int(r["year"]) for r in enriched}, reverse=True)

    for year in years_needed:
        for consumption_key, cost_key, chart_title in CHART_METRIC_PAIRS:
            out_file = write_combo_chart_svg(
                consumption_key,
                cost_key,
                chart_title,
                year,
                series,
                charts_dir,
                enriched,
            )
            if out_file is None:
                continue
            rel_path = f"{REL_CHART_ROOT}/{out_file.name}"
            paths[(year, consumption_key)] = rel_path

    return paths
