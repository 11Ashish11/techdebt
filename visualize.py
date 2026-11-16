"""Generate visualization charts from Tech Debt Analyzer report.json data using matplotlib.

Usage:
    python visualize.py PATH_TO_REPORT_JSON [--out DIR]
"""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def set_plot_style():
    """Configure clean, legible styling for matplotlib figures."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.autolayout": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def plot_complexity_distribution(data, out_path):
    """Plot cyclomatic complexity rank distribution (A-F)."""
    fig, ax = plt.subplots(figsize=(7, 4.5))

    bands = data.get("summary", {}).get("complexity_bands", {})
    ranks = ["A", "B", "C", "D", "E", "F"]
    counts = [bands.get(r, 0) for r in ranks]

    colors = ["#2ecc71", "#27ae60", "#f39c12", "#e67e22", "#d35400", "#c0392b"]
    bars = ax.bar(ranks, counts, color=colors, edgecolor="#2c3e50", linewidth=0.8, width=0.55)

    ax.set_title("Function Complexity Distribution (Radon CC Ranks)")
    ax.set_xlabel("Complexity Rank (A = Simple, F = Very High Risk)")
    ax.set_ylabel("Number of Functions")

    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                str(count),
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_hotspots_scatter(data, out_path):
    """Plot file hotspots: Max Cyclomatic Complexity vs SLOC with Maintainability Index."""
    hotspots = data.get("hotspots", [])
    if not hotspots:
        return

    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    slocs = [h["sloc"] for h in hotspots]
    max_ccs = [h["max_complexity"] for h in hotspots]
    mis = [h.get("mi", 50.0) for h in hotspots]
    files = [h["file"] for h in hotspots]

    scatter = ax.scatter(
        slocs,
        max_ccs,
        c=mis,
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        s=180,
        edgecolor="#2c3e50",
        linewidth=1.2,
        alpha=0.85,
    )

    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Maintainability Index (0 = Hard, 100 = Easy)")

    # Annotate top hotspots (e.g. top 5 or prominent outliers)
    for i, (x, y, fname) in enumerate(zip(slocs, max_ccs, files)):
        if i < 5 or y >= 15 or x >= 300:
            ax.annotate(
                fname,
                (x, y),
                textcoords="offset points",
                xytext=(8, 5),
                ha="left",
                fontsize=8.5,
                weight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#bdc3c7", alpha=0.8),
            )

    ax.set_title("Hotspot Risk Matrix: File Size vs Maximum Complexity")
    ax.set_xlabel("Source Lines of Code (SLOC)")
    ax.set_ylabel("Maximum Function Cyclomatic Complexity (CC)")

    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_top_functions(data, out_path):
    """Plot top 8 most complex functions and top 8 longest functions side-by-side."""
    funcs = data.get("functions", [])
    longest = data.get("longest_functions", [])

    if not funcs:
        return

    top_cc = sorted(funcs, key=lambda f: -f["complexity"])[:8]
    top_len = longest[:8] if longest else sorted(funcs, key=lambda f: -f.get("length", 0))[:8]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Top CC
    names_cc = [f"{f['name']}\n({f['file'].split('/')[-1]}:{f['line']})" for f in reversed(top_cc)]
    vals_cc = [f["complexity"] for f in reversed(top_cc)]
    bars1 = ax1.barh(names_cc, vals_cc, color="#e74c3c", edgecolor="#2c3e50", height=0.6)
    ax1.set_title("Top Functions by Cyclomatic Complexity (CC)")
    ax1.set_xlabel("Cyclomatic Complexity")
    for bar in bars1:
        ax1.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(int(bar.get_width())),
            va="center",
            fontweight="bold",
            fontsize=8,
        )

    # Top Length
    names_len = [f"{f['name']}\n({f['file'].split('/')[-1]}:{f['line']})" for f in reversed(top_len)]
    vals_len = [f.get("length", 1) for f in reversed(top_len)]
    bars2 = ax2.barh(names_len, vals_len, color="#3498db", edgecolor="#2c3e50", height=0.6)
    ax2.set_title("Top Functions by Length (Lines of Code)")
    ax2.set_xlabel("Physical Function Length (Lines)")
    for bar in bars2:
        ax2.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            str(int(bar.get_width())),
            va="center",
            fontweight="bold",
            fontsize=8,
        )

    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_smells_and_coupling(data, out_path):
    """Plot smells count and import coupling per file."""
    file_metrics = data.get("file_metrics", {})
    smells_by_file = data.get("smells_by_file", {})

    all_files = sorted(file_metrics.keys())[:10]  # Show top 10 files
    if not all_files:
        return

    import_counts = [file_metrics[f].get("imports_count", 0) for f in all_files]
    smell_counts = [len(smells_by_file.get(f, [])) for f in all_files]
    short_names = [f.split("/")[-1] for f in all_files]

    fig, ax = plt.subplots(figsize=(8.5, 4.5))

    x = range(len(all_files))
    width = 0.35

    ax.bar([i - width / 2 for i in x], import_counts, width=width, label="Import Coupling (Modules)", color="#9b59b6")
    ax.bar([i + width / 2 for i in x], smell_counts, width=width, label="SATD Smells (Comments)", color="#e67e22")

    ax.set_xticks(list(x))
    ax.set_xticklabels(short_names, rotation=30, ha="right")
    ax.set_title("Import Coupling & Self-Admitted Debt by File")
    ax.set_ylabel("Count")
    ax.legend()

    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def generate_visualizations(report_json_path, out_dir):
    """Load report.json and generate all visualization charts."""
    json_file = Path(report_json_path)
    if not json_file.exists():
        raise FileNotFoundError(f"Report JSON not found at: {report_json_path}")

    out_folder = Path(out_dir)
    out_folder.mkdir(parents=True, exist_ok=True)

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    set_plot_style()
    plot_complexity_distribution(data, out_folder / "complexity_distribution.png")
    plot_hotspots_scatter(data, out_folder / "hotspots_scatter.png")
    plot_top_functions(data, out_folder / "top_functions_comparison.png")
    plot_smells_and_coupling(data, out_folder / "smells_coupling_breakdown.png")


def main():
    """Parse CLI arguments and run visualization generation."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", type=Path, help="path to report.json generated by analyze.py")
    parser.add_argument("--out", type=Path, default=Path("."), help="directory to save generated PNG charts")
    args = parser.parse_args()

    generate_visualizations(args.report, args.out)
    print(f"Generated visualization charts in {args.out.resolve()}")


if __name__ == "__main__":
    main()
