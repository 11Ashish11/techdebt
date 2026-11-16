# Technical Debt & Code Smell Assessment: Example Report & Guide

This document serves as an **exemplar assessment** and a **student template**. It demonstrates how to combine the automated metrics from `analyze.py`, visual charts from `visualize.py`, and manual code inspection into a rigorous technical debt analysis.

---

# Part 1: Exemplar Assessment (Case Study: `tabulate`)

**Target Project**: `python-tabulate/tabulate`  
**Analyzed Scope**: `tabulate/` (3 core source files, 76 functions)  
**Evaluator**: Engineering Assessment Team  

---

## 1. Executive Summary & Metric Overview

Running `python analyze.py ../python-tabulate/tabulate --out out-tabulate --plot` generated the following evidence:

| Metric Indicator | Value / Summary | Interpretation |
| :--- | :--- | :--- |
| **Total Source Lines (SLOC)** | 1,842 lines across 3 files | Compact library, but heavily centralized in `__init__.py` |
| **Complexity Tail (Ranks C–F)** | 11 functions (14.5% of codebase) | Significant high-risk complexity concentrated in formatting engines |
| **Top Complexity Function** | `_normalize_tabular_data` (CC = 76, Rank F, Length = 184 LOC) | Giant multi-branching data conversion routine |
| **Maintainability Index (MI)** | `__init__.py`: 0.0 (Rank C) | Extremely low maintainability due to size, volume, and CC |
| **Import Coupling** | 8 modules in `__init__.py`, 6 in `cli.py` | Modest external coupling, but high internal coupling |
| **Self-Admitted Debt (SATD)** | 6 comments (`TODO`, `WORKAROUND`) | Known issues in column alignment and multiline table handling |
| **Code Duplication** | 4 repeated format normalization blocks | Duplicate whitespace and padding loops across formats |

---

## 2. Visual Analysis

The generated charts highlight the risk profile:

### Figure 1: Function Complexity Distribution
![Complexity Distribution](plots/complexity_distribution.png)
*Insight*: While ~75% of functions are simple (Rank A), the "long tail" contains 5 functions in ranks D, E, and F. This indicates that core features were implemented as monolithic functions rather than composed modules.

### Figure 2: Hotspot Risk Matrix (SLOC vs Max CC)
![Hotspots Scatter](plots/hotspots_scatter.png)
*Insight*: `tabulate/__init__.py` sits in the extreme upper-right danger zone (SLOC > 1600, Max CC = 76, MI = 0), making it the single highest-priority candidate for refactoring.

### Figure 3: Top Functions by Complexity & Length
![Top Functions](plots/top_functions_comparison.png)
*Insight*: High correlation between function length and cyclomatic complexity. `_normalize_tabular_data` and `tabulate` dominate both metrics.

---

## 3. Deep-Dive: Top Code Hotspots & Smells

### Hotspot 1: `tabulate/__init__.py::_normalize_tabular_data` (Line 1428)
- **Metrics**: Cyclomatic Complexity = 76 (Rank F), Length = 184 lines.
- **Code Inspection Findings**:
  - Contains nested `isinstance` checks supporting lists, dictionaries, pandas DataFrames, numpy arrays, and record arrays.
  - Mixes row normalization, key extraction, column header inference, and data type coercion in a single sequential block.
  - High risk of regression when adding support for any new tabular data structure.

### Hotspot 2: `tabulate/__init__.py::tabulate` (Line 1696)
- **Metrics**: Cyclomatic Complexity = 62 (Rank F), Length = 210 lines.
- **Code Inspection Findings**:
  - The primary public API entrypoint.
  - Intertwines parameter validation, format lookup, multiline wrapping calculation, and ANSI escape code handling.

### Hotspot 3: Self-Admitted Debt & Duplication
- **Line 748**: `# TODO: Add multiline support for the remaining table formats`
- **Line 1224**: `# TODO: refactor column alignment in single-line and multiline modes`
- **Duplicate Blocks**: Format padding routines in markdown, grid, and html formatters share repetitive string formatting loops.
- **Synthesis**: The SATD comments confirm that developers recognized the multiline alignment logic was becoming unmanageable.

---

## 4. Technical Debt Quadrant Classification

| Dimension | Classification | Justification |
| :--- | :--- | :--- |
| **Quadrant** | **Prudent & Deliberate** (Fowler Debt Quadrant) | The author intentionally supported dozens of disparate data structures in single fast functions to make the library zero-dependency and easy to install. The TODO comments show conscious awareness of the trade-off between rapid feature delivery and architectural elegance. |

```
                       Prudent
                          |
     (Prudent /           |   ★ tabulate normalization
      Deliberate)         |     (Deliberate / Prudent)
  "We must ship now,      |
   we know the trade-offs"|
--------------------------+--------------------------
  Deliberate              |               Inadvertent
                          |
                          |   (Inadvertent / Reckless)
                          |   "What is layering?"
                          |
                       Reckless
```

---

## 5. Architectural Recommendation & Repayment ROI

### Recommended Action: **Targeted Refactoring (Strategy: Extract Parser Hierarchy)**

1. **Proposed Fix**:
   - Extract `_normalize_tabular_data` into a polymorphic `DataNormalizer` registry pattern (`DictNormalizer`, `DataFrameNormalizer`, `SequenceNormalizer`).
   - Separate string width/ANSI escape calculation from table grid assembly.
2. **Cost of the Debt**:
   - Estimated 4 hours of debugging overhead per new tabular format PR due to high cyclomatic complexity.
   - Ongoing risk of regression in table formatting corner cases.
3. **Cost of the Fix**:
   - ~12 engineering hours to extract normalizers and create unit tests for each adapter.
4. **Break-Even Analysis**:
   - Payoff occurs after 3 major feature additions or formatting PRs ($3 \times 4\text{ hours} = 12\text{ hours}$).
   - Break-even estimated within **3 to 4 months** of active maintenance.
5. **Pre-Refactoring Safeguards**:
   - Verify comprehensive regression test suite on existing tabular output before altering the signature.

---

# Part 2: Student Assessment Template

*Students should copy the template below into `notes.md` or `assessment.md` for their chosen open-source project.*

```markdown
# Technical Debt Assessment: [Project Name]

**Group Members**: [Name 1, Name 2, Name 3]  
**Analyzed Path**: [e.g., `src/dotenv/`]  
**Date**: [YYYY-MM-DD]  

## 1. Project Overview & Metrics Summary

- **Total Files Analyzed**: 
- **Total Functions**: 
- **Complexity Profile (Counts)**: A: __, B: __, C: __, D: __, E: __, F: __
- **Maintainability Index (Worst & Best)**: 
- **Self-Admitted Debt Comments**: __ found across __ files
- **Duplicate Code Blocks**: __ detected
- **Import Coupling Highlights**: 

## 2. Key Hotspots & Findings

| File | Max CC | SLOC | MI (Rank) | Imports | Priority Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |
| | | | | | |
| | | | | | |

### Top Function Analysis
1. **[Function Name]** (`file:line`):
   - Complexity: __ | Length: __ LOC
   - What the code does:
   - Why it is complex (nested loops, many branches, long dispatch):

### Code Smells & SATD Analysis
- Notable TODO / FIXME / HACK comments:
- Do smells coincide with the highest-complexity files?

## 3. Visual Insights (from `visualize.py`)
- **Complexity Distribution**: [Describe what the bar chart reveals about the tail]
- **Hotspots Scatter Matrix**: [Describe outlier files in the scatter plot]
- **Function Comparison**: [Describe relationship between length and complexity]

## 4. Debt Quadrant Classification
- **Selected Finding**: 
- **Quadrant**: [Deliberate/Inadvertent × Prudent/Reckless]
- **Rationale**: [2-3 sentences explaining why with evidence from code/comments]

## 5. Recommendation & Break-Even
- **Decision**: [Refactor / Replace / Leave Alone]
- **Estimated Current Cost**: 
- **Estimated Fix Effort**: 
- **Break-Even Point**: 
- **Key Risks & Verification**: 
```
