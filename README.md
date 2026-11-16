# Exercise: Tech Debt Analyzer & Visualizer

Work in groups of about 3. This exercise is not graded. Fork the exercise repo and commit your report, generated visualizations, and assessment notes.

## Overview

In this exercise you will point an automated analysis and visualization toolchain at real open-source Python projects and use its output to answer a practical engineering question: **if a team had one afternoon to address technical debt in this codebase, where should they start, what are the trade-offs, and what is the return on investment (ROI) for repayment?**

The toolchain produces **multi-dimensional evidence** (cyclomatic complexity, maintainability index, function length, import coupling, code duplication, and self-admitted debt) along with **visual charts**. Your job is to analyze the evidence, inspect the actual source code, categorize debt types, and write an actionable technical debt assessment.

### How the exercise is organized

| Part | What you do | Rough time |
| --- | --- | --- |
| [Step 1: Setup](#step-1-setup) | Install dependencies and pick a project | 10 min |
| [Step 2: Try individual metrics on a single file](#step-2-try-individual-metrics-on-a-single-file) | Explore radon & AST metric concepts | 10 min |
| [Step 3: Run the analyzer & visualizer](#step-3-run-the-analyzer--visualizer) | Generate Markdown, JSON, and PNG charts | 5 min |
| [Step 4: Read the report and charts](#step-4-read-the-report-and-charts) | Learn what each metric and visualization means | 10 min |
| [Step 5: Inspect the source code](#step-5-inspect-the-source-code) | Check the metrics against real implementation | 15 min |
| 🟢 / 🟡 / 🔴 tiers | Investigate, classify, and write your debt assessment | rest of session |

Everyone does Steps 1 to 5 and the 🟢 Starter. Move on to 🟡 Intermediate and 🔴 Stretch for full analysis and recommendation.

**What you need:** Python 3.8+, `git` (or a browser to download a zip), and a text editor or IDE.

---

## Step 1: Setup

### 1a. Get the exercise files

Fork the exercise repo, clone your fork, and open a terminal in the folder that contains `analyze.py`, `visualize.py`, and `requirements.txt`.

### 1b. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies installed:
- [Radon](https://radon.readthedocs.io/): Measures cyclomatic complexity, raw lines of code, and maintainability index.
- [Matplotlib](https://matplotlib.org/): Generates visual distribution and hotspot charts.

### 1c. Pick a project to analyze

Choose **one** project from the table (or analyze two for comparison in the Intermediate tier).

| Project | Source folder to analyze | Size | Why it is interesting |
| --- | --- | --- | --- |
| [`schedule`](https://github.com/dbader/schedule) | `schedule/` | Tiny (1 file) | Quick first run, one obvious complex function |
| [`tabulate`](https://github.com/astanin/python-tabulate) | `tabulate/` | Small (3 files) | **Recommended.** Several very complex functions and known SATD comments |
| [`python-dotenv`](https://github.com/theskumar/python-dotenv) | `src/dotenv/` | Small (8 files) | A healthier codebase, good for contrast |
| [`humanize`](https://github.com/python-humanize/humanize) | `src/humanize/` | Small (6 files) | Complexity from lots of time and unit branching |
| [`pluggy`](https://github.com/pytest-dev/pluggy) | `src/pluggy/` | Medium (13 files) | Compact but very active plugin engine |
| [`click`](https://github.com/pallets/click) | `src/click/` | Large (17 files) | High complexity and nesting; a lot to read |

Not sure? Use `tabulate`.

### 1d. Download the project's code

Clone it outside your exercise repo:

```bash
git clone --depth 100 https://github.com/astanin/python-tabulate
```

> **Point the script at the source folder, not the whole repo.** For `tabulate`, that is `python-tabulate/tabulate/` (the folder with `__init__.py` inside).

---

## Step 2: Try individual metrics on a single file

Before generating an aggregated report across an entire codebase, try running individual metric calculations on a single file:

### 2a. Cyclomatic complexity (`radon cc`)
```bash
radon cc analyze.py -s
```
- Scores: `A` (1–5, simple) through `F` (41+, extremely branchy).

### 2b. Maintainability Index (`radon mi`)
```bash
radon mi analyze.py -s
```
- Composite score (0–100) combining Halstead volume, cyclomatic complexity, and SLOC (`A` = 20–100, `B` = 10–19, `C` = 0–9).

### 2c. Inspect metrics in Python
```python
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze

code = open("analyze.py").read()
print(f"SLOC: {analyze(code).sloc}, MI: {mi_visit(code, multi=True):.2f}")
for b in cc_visit(code):
    print(f"Function `{b.name}`: CC={b.complexity}, Length={getattr(b, 'endline', b.lineno) - b.lineno + 1}")
```

---

## Step 3: Run the analyzer & visualizer

Run the enhanced analyzer with the `--plot` flag to generate reports and charts in one step:

```bash
python analyze.py ../python-tabulate/tabulate --out out-tabulate --plot
```

Output:
```text
Analyzed 3 files, 76 functions -> out-tabulate/report.md
Generated visualizations -> out-tabulate/*.png
```

You can also run `visualize.py` directly on any existing `report.json`:
```bash
python visualize.py out-tabulate/report.json --out out-tabulate/plots
```

---

## Step 4: Read the report and charts

The analyzer creates the `--out` folder and generates:
- `report.md`: Readable Markdown summary table with metric definitions.
- `report.json`: Full structured JSON dataset with all raw function entries, smells, and clones.
- `complexity_distribution.png`: Bar chart showing function counts across CC ranks (A–F).
- `hotspots_scatter.png`: Hotspot matrix plotting SLOC vs Max CC, color-coded by Maintainability Index.
- `top_functions_comparison.png`: Dual horizontal bar charts comparing Top Complex vs Longest functions.
- `smells_coupling_breakdown.png`: Bar chart breakdown of SATD smells and AST import coupling per file.

### Section by section in `report.md`

1. **Complexity distribution**: Shape of the codebase. Look for the "tail" (functions in ranks C, D, E, F).
2. **Top 10 functions by complexity**: Highest CC functions with file, line, rank, and physical length.
3. **Five longest functions**: Longest functions by line count. Check if they overlap with the top CC functions.
4. **Hotspots table**: Combines Max CC, SLOC, Maintainability Index (MI), and Import Coupling into a priority score.
5. **Smells (SATD)**: `TODO`, `FIXME`, `HACK`, `WORKAROUND`, and `DEPRECATED` comments grouped by file.
6. **Code Duplication**: Repeated multi-line normalized code blocks across files.

---

## Step 5: Inspect the source code

Metrics are clues, not verdicts. Spend 15 minutes checking the source code:
1. Jump to the #1 most complex function in your editor. Is it deeply nested? Does it do too many things (low cohesion)?
2. Look at the #1 longest function. Is it complex, or just boilerplate / table definitions?
3. Review the SATD comments in the hotspot files. What were the original developers struggling with?

---

## 🟢 Starter

Run the tool on your project and answer these in a notes file (`notes.md` or `assessment.md`):

1. **Where would you look first?** Which file and function rank as the highest priority in the hotspot table, and what does the code inspection reveal?
2. **Is the worst function really debt?** Look at the top function by CC. Is it necessary domain complexity (e.g. many formats) or accidental complexity that should be refactored?
3. **Do the signals agree?** Do the TODO/FIXME comments and duplication sit in the same files as the high-complexity functions?

---

## 🟡 Intermediate

1. **Compare Two Projects**: Run the analyzer and visualizer on a second project (e.g., `python-dotenv` or `humanize`).
2. **Distribution & Hotspot Contrast**: Compare the `complexity_distribution.png` and `hotspots_scatter.png` between both projects. Which codebase has a healthier profile?
3. **Technical Debt Quadrant**: Select one significant finding (such as a complex function or a workaround comment) and classify it on Martin Fowler's Technical Debt Quadrant:
   - *Prudent vs Reckless*
   - *Deliberate vs Inadvertent*
   - Provide 2–3 sentences of justification based on comments and code design.

---

## 🔴 Stretch

Produce a complete **Technical Debt Assessment & Recommendation** using [`example_assessment/example_assessment.md`](example_assessment/example_assessment.md) as a guide.

Your assessment must include:
1. **Evidence Summary**: Synthesize the automated metrics (CC tail, MI, Longest Functions, Coupling, Duplication) and visual charts.
2. **Hotspot Deep Dive**: Detailed code inspection of the top 2–3 candidate files/functions.
3. **Architectural Recommendation**: Recommend one action (**Refactor**, **Replace**, or **Leave Alone**).
4. **ROI & Break-Even Analysis**:
   - Estimated ongoing cost of the debt (bugs, developer hours per change).
   - Estimated one-time cost to fix/refactor.
   - Break-even timeline (e.g. number of changes or months to pay off).
5. **Risks & Verification**: What tests or dependencies must be verified before refactoring?

---

## What to commit

Commit the following to your repository:
- Your completed assessment (`assessment.md` or `notes.md` using the template from [`example_assessment/example_assessment.md`](example_assessment/example_assessment.md))
- Generated outputs: `out-<project>/report.md`, `out-<project>/report.json`, and the `.png` charts
