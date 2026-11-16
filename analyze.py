"""Tech debt analyzer: complexity, size, maintainability, smells, coupling, and duplication.

Usage:
    python analyze.py PATH_TO_CODE [--out DIR] [--plot]

Writes report.md and report.json, and optionally generates visualization charts.
"""
import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit
from radon.raw import analyze

# Directories and path segments to skip so we only analyze core application source code
EXCLUDE = ("test", "tests", "testing", "docs", ".github", ".venv", "venv", "examples", "locale")

# Regular expression pattern to detect Self-Admitted Technical Debt (SATD) marker comments
SATD = re.compile(
    r"#.*\b(TODO|FIXME|HACK|XXX|DEPRECATED|WORKAROUND|TEMPORARY|FOR NOW)\b",
    re.IGNORECASE,
)


def py_files(root):
    """Find all Python source files under root, skipping tests and excluded directories."""
    return [
        p for p in root.rglob("*.py")
        if not any(part in EXCLUDE for part in p.relative_to(root).parts)
        and not p.name.startswith("test_")
    ]


def count_file_imports(text):
    """Count import statements and collect imported module names using AST analysis."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, []

    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    return len(modules), sorted(modules)


def collect_structure(root, files):
    """Collect per-function complexity/length, per-file SLOC, maintainability, and imports.

    Computes:
      - SLOC (Source Lines of Code): lines excluding blanks and comments
      - Cyclomatic Complexity (CC): number of independent execution paths
      - Function Length: endline - lineno + 1
      - Maintainability Index (MI): 0-100 composite score
      - Import Coupling: unique external/internal module import count
    """
    funcs = []
    file_metrics = {}

    for f in files:
        rel = str(f.relative_to(root))
        text = f.read_text(errors="ignore")

        # Raw size
        raw_stats = analyze(text)
        sloc = raw_stats.sloc

        # Maintainability Index
        try:
            mi_score = max(0.0, min(100.0, round(mi_visit(text, multi=True), 2)))
        except Exception:
            mi_score = 0.0
        mi_letter = mi_rank(mi_score)

        # Import coupling
        import_count, imported_modules = count_file_imports(text)

        file_metrics[rel] = {
            "sloc": sloc,
            "mi": mi_score,
            "mi_rank": mi_letter,
            "imports_count": import_count,
            "imported_modules": imported_modules,
        }

        # Inspect functions and methods
        for b in cc_visit(text):
            end_line = getattr(b, "endline", b.lineno)
            length = max(1, end_line - b.lineno + 1)
            funcs.append({
                "file": rel,
                "name": b.fullname,
                "line": b.lineno,
                "end_line": end_line,
                "length": length,
                "complexity": b.complexity,
                "rank": cc_rank(b.complexity),
            })

    return funcs, file_metrics


def collect_smells(root, files):
    """Scan source files for self-admitted technical debt comments and group by file."""
    found = []
    for f in files:
        rel = str(f.relative_to(root))
        for n, text in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            stripped = text.strip()
            if "re.compile" in text or stripped.startswith(('r"', 'r\'', '"', "'")):
                continue
            if "#" in stripped:
                comment_part = stripped[stripped.index("#"):]
                match = SATD.search(comment_part)
                if match:
                    keyword = match.group(1).upper()
                    found.append({
                        "file": rel,
                        "line": n,
                        "keyword": keyword,
                        "text": stripped,
                    })
    return found


def collect_duplicates(root, files, chunk_size=4):
    """Detect duplicated code blocks across files using sliding normalized line chunk hashing."""
    hashes = defaultdict(list)

    for f in files:
        rel = str(f.relative_to(root))
        lines = f.read_text(errors="ignore").splitlines()

        # Filter out purely blank lines or single-line comments for normalization
        indexed_lines = []
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                indexed_lines.append((idx, stripped))

        if len(indexed_lines) < chunk_size:
            continue

        for i in range(len(indexed_lines) - chunk_size + 1):
            chunk = indexed_lines[i : i + chunk_size]
            normalized_text = "\n".join(text for _, text in chunk)
            chunk_hash = hashlib.md5(normalized_text.encode("utf-8")).hexdigest()
            start_line = chunk[0][0]
            end_line = chunk[-1][0]
            hashes[chunk_hash].append({
                "file": rel,
                "start_line": start_line,
                "end_line": end_line,
                "sample": normalized_text[:120],
            })

    # Keep only duplicated chunks
    duplicates = []
    for h, occurrences in hashes.items():
        if len(occurrences) > 1:
            # Check if occurrences are distinct (not identical overlapping offsets in same file)
            distinct_locs = {(loc["file"], loc["start_line"]) for loc in occurrences}
            if len(distinct_locs) > 1:
                duplicates.append({
                    "hash": h,
                    "instances": len(occurrences),
                    "locations": occurrences,
                    "sample": occurrences[0]["sample"],
                })

    # Sort duplicates by frequency
    duplicates.sort(key=lambda d: -d["instances"])
    return duplicates


def rank_of(values):
    """Compute dense ranking for a list of values (1 = highest value; ties share the same rank)."""
    return {v: i + 1 for i, v in enumerate(sorted(set(values), reverse=True))}


def hotspots(funcs, file_metrics):
    """Rank files by combining maximum function complexity and size (SLOC).

    Hotspot score = (Max CC rank) + (SLOC rank).
    Lower total score indicates high-priority candidate for investigation.
    """
    maxcc = {f: 0 for f in file_metrics}
    for fn in funcs:
        maxcc[fn["file"]] = max(maxcc[fn["file"]], fn["complexity"])

    rows = []
    for f, metrics in file_metrics.items():
        rows.append({
            "file": f,
            "max_complexity": maxcc[f],
            "sloc": metrics["sloc"],
            "mi": metrics["mi"],
            "mi_rank": metrics["mi_rank"],
            "imports": metrics["imports_count"],
        })

    cc_r = rank_of([r["max_complexity"] for r in rows])
    sz_r = rank_of([r["sloc"] for r in rows])

    for r in rows:
        r["score"] = cc_r[r["max_complexity"]] + sz_r[r["sloc"]]

    # Sort files so lowest score (highest priority candidate) comes first
    return sorted(rows, key=lambda r: r["score"])


def write_report(out, root, funcs, smells, hot, duplicates, file_metrics):
    """Generate comprehensive report.md summary and complete report.json data."""
    # Count how many functions fall into each complexity rank band (A through F)
    bands = Counter(f["rank"] for f in funcs)
    # Identify top 10 most complex functions
    top_cc = sorted(funcs, key=lambda f: -f["complexity"])[:10]
    # Identify five longest functions
    longest = sorted(funcs, key=lambda f: -f["length"])[:5]

    # Group smells by file
    smells_by_file = defaultdict(list)
    for s in smells:
        smells_by_file[s["file"]].append(s)

    md = [
        f"# Tech Debt Report: {root.name}",
        "",
        "## Metric definitions",
        "- **Complexity**: Radon cyclomatic complexity per function (A=1-5, B=6-10, C=11-20, D=21-30, E=31-40, F=41+).",
        "- **Function Length**: Physical lines of code from function definition to endline.",
        "- **Size (SLOC)**: Source lines of code (excluding blanks and comments) per file.",
        "- **Maintainability Index (MI)**: 0-100 composite score based on Halstead volume, CC, and SLOC (A: 20-100, B: 10-19, C: 0-9).",
        "- **Import Coupling**: Count of distinct external/internal modules imported (higher = more coupled).",
        "- **Duplication**: Repeated blocks of normalized consecutive lines across the codebase.",
        "- **Hotspot score**: max-complexity rank + size rank per file (lower score = higher investigation priority).",
        f"- **Excluded paths**: {', '.join(EXCLUDE)}.",
        "",
        "## Complexity distribution",
        "| Rank | Functions |",
        "| --- | --- |",
    ]
    md += [f"| {r} | {bands.get(r, 0)} |" for r in "ABCDEF"]

    md += [
        "",
        "### Top 10 functions by complexity",
        "| Function | File:Line | CC | Rank | Length (LOC) |",
        "| --- | --- | --- | --- | --- |",
    ]
    md += [
        f"| `{f['name']}` | {f['file']}:{f['line']} | {f['complexity']} | {f['rank']} | {f['length']} |"
        for f in top_cc
    ]

    md += [
        "",
        "### Five longest functions",
        "| Function | File:Line | Length (LOC) | CC | Rank |",
        "| --- | --- | --- | --- | --- |",
    ]
    md += [
        f"| `{f['name']}` | {f['file']}:{f['line']} | {f['length']} | {f['complexity']} | {f['rank']} |"
        for f in longest
    ]

    md += [
        "",
        "## Hotspots (complex and large files)",
        "| File | Max CC | SLOC | MI | Imports | Score |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    md += [
        f"| {h['file']} | {h['max_complexity']} | {h['sloc']} | {h['mi']} ({h['mi_rank']}) | {h['imports']} | {h['score']} |"
        for h in hot[:10]
    ]

    md += [
        "",
        f"## Smells: self-admitted debt ({len(smells)} found in {len(smells_by_file)} files)",
    ]
    if smells:
        for file_path, file_smells in sorted(smells_by_file.items(), key=lambda kv: -len(kv[1])):
            md.append(f"\n### {file_path} ({len(file_smells)} notes)")
            for s in file_smells[:10]:
                md.append(f"- Line {s['line']} `[{s['keyword']}]`: `{s['text']}`")
            if len(file_smells) > 10:
                md.append(f"- *(and {len(file_smells) - 10} more in report.json)*")
    else:
        md.append("No self-admitted technical debt comments found.")

    md += [
        "",
        f"## Code Duplication ({len(duplicates)} duplicate patterns detected)",
    ]
    if duplicates:
        for i, dup in enumerate(duplicates[:5], 1):
            md.append(f"\n#### Duplicate #{i} ({dup['instances']} occurrences)")
            for loc in dup["locations"]:
                md.append(f"- {loc['file']}:{loc['start_line']}-{loc['end_line']}")
    else:
        md.append("No duplicated blocks detected across analyzed files.")

    md += [
        "",
        "## What to investigate first",
        "1. **Primary Hotspot**: Which file and function represent the highest immediate risk?",
        "2. **Maintainability & Coupling**: Are the complex files also tightly coupled or poorly rated in MI?",
        "3. **Smells & Duplication**: Do known debt comments align with the highest-risk hotspots?",
    ]

    # Write Markdown summary and complete JSON dataset
    (out / "report.md").write_text("\n".join(md) + "\n")

    json_payload = {
        "project": root.name,
        "summary": {
            "total_files": len(file_metrics),
            "total_functions": len(funcs),
            "total_smells": len(smells),
            "total_duplicate_patterns": len(duplicates),
            "complexity_bands": dict(bands),
        },
        "functions": funcs,
        "longest_functions": longest,
        "hotspots": hot,
        "smells": smells,
        "smells_by_file": {f: s for f, s in smells_by_file.items()},
        "duplicates": duplicates,
        "file_metrics": file_metrics,
    }
    (out / "report.json").write_text(json.dumps(json_payload, indent=2))


def main():
    """Parse CLI arguments and run the technical debt analysis pipeline."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path, help="directory containing Python source")
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--plot", action="store_true", help="generate visualization charts using matplotlib")
    a = ap.parse_args()

    root = a.path.resolve()
    files = py_files(root)
    funcs, file_metrics = collect_structure(root, files)
    smells = collect_smells(root, files)
    duplicates = collect_duplicates(root, files)
    hot = hotspots(funcs, file_metrics)

    a.out.mkdir(parents=True, exist_ok=True)
    write_report(a.out, root, funcs, smells, hot, duplicates, file_metrics)
    print(f"Analyzed {len(files)} files, {len(funcs)} functions -> {a.out}/report.md")

    if a.plot:
        try:
            from visualize import generate_visualizations
            generate_visualizations(a.out / "report.json", a.out)
            print(f"Generated visualizations -> {a.out}/*.png")
        except ImportError:
            print("Notice: matplotlib is required for --plot. Run: pip install matplotlib")
        except Exception as e:
            print(f"Failed to generate visualizations: {e}")


if __name__ == "__main__":
    main()
