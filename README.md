# Responsible-AI — FairLoan AI Dashboard

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Why Responsible AI?](#2-why-responsible-ai)
3. [Project Structure](#3-project-structure)
4. [Architecture & Data Flow](#4-architecture--data-flow)
5. [Backend: `app.py`](#5-backend-apppy)
   - [Simulated Datasets](#simulated-datasets)
   - [Fairness Engine: `evaluate_fairness()`](#fairness-engine-evaluate_fairness)
   - [API Routes](#api-routes)
6. [Frontend: `templates/index.html`](#6-frontend-templatesindexhtml)
7. [Frontend Logic: `static/app.js`](#7-frontend-logic-staticappjs)
8. [Styling: `static/style.css`](#8-styling-staticstylecss)
9. [Fairness Metrics Explained](#9-fairness-metrics-explained)
10. [Input Validation Rules](#10-input-validation-rules)
11. [API Reference](#11-api-reference)
12. [Run Locally](#12-run-locally)
13. [Example Walkthrough](#13-example-walkthrough)

---

## 1. Project Overview

**FairLoan AI** is a lightweight, browser-based **Responsible AI audit dashboard** built with Python (Flask) and vanilla JavaScript. Its primary purpose is to help data scientists, ML engineers, and product teams detect and understand **demographic bias** in automated loan-approval (or any binary-decision) models.

The dashboard accepts either a pre-built sample dataset (Gender or Age) or a fully custom user-defined dataset, computes several standard fairness metrics, renders interactive charts, and surfaces a plain-English recommendation so that teams can decide whether their model requires re-training or fairness constraints.

---

## 2. Why Responsible AI?

Machine-learning models trained on historical data can inherit and amplify societal biases. In the context of loan approvals, a biased model may systematically approve loans for one demographic group at a higher rate than another — not because of creditworthiness, but because of protected attributes such as gender or age. Regulations such as the **Equal Credit Opportunity Act (ECOA)** in the United States and the **EU AI Act** require that high-stakes algorithmic decisions be auditable and demonstrably fair.

The most widely used quantitative test for such bias is the **80% Rule** (also called the **Disparate Impact Rule**), which is codified in the US EEOC's Uniform Guidelines. This project implements that rule, along with additional supporting metrics, in an accessible web interface.

---

## 3. Project Structure

```
Responsible-AI/
├── app.py               # Flask web server + all fairness-metric logic
├── requirements.txt     # Python runtime dependencies (Flask)
├── templates/
│   └── index.html       # Server-rendered HTML shell of the dashboard
└── static/
    ├── app.js           # All client-side audit logic, chart rendering, history
    └── style.css        # Complete dashboard styling (CSS variables, grid, responsive)
```

| File | Role | Language |
|---|---|---|
| `app.py` | HTTP server, data store, computation engine | Python |
| `templates/index.html` | Markup skeleton, loads JS/CSS | HTML |
| `static/app.js` | Fetch calls, DOM updates, Chart.js integration | JavaScript |
| `static/style.css` | Visual design, layout, responsiveness | CSS |
| `requirements.txt` | Pins `Flask>=3.0,<4.0` | Plain text |

---

## 4. Architecture & Data Flow

```
Browser
  │
  │  1. User selects dimension (gender / age) or fills custom form
  │  2. JS calls GET /audit-data?dimension=... or POST /audit-data
  ▼
Flask Server (app.py)
  │
  │  3. Validates input (POST path only)
  │  4. Calls evaluate_fairness(payload)
  │     ├── Computes ratio, parity_gap, status, fairness_score
  │     └── Picks recommendation text
  │  5. Returns JSON response
  ▼
Browser (app.js)
  │
  │  6. renderKpis()     → updates 4 KPI cards
  │  7. renderCharts()   → draws/replaces 2 Chart.js bar charts
  │  8. addHistoryEntry()→ prepends row to audit history table (max 8 rows)
  └── setInsight()       → writes full diagnostic sentence to insight box
```

The application has **no database** and **no persistent state** on the server. All audit history is stored in a JavaScript array in the browser and is reset on page reload.

---

## 5. Backend: `app.py`

### Simulated Datasets

```python
SIMULATED_DATASETS = {
    "gender": {
        "labels": ["Group A (Majority)", "Group B (Minority)"],
        "approval_rates": [85, 42],
        "grouping": "Gender",
    },
    "age": {
        "labels": ["Age 26+ (Majority)", "Age 18-25 (Minority)"],
        "approval_rates": [78, 51],
        "grouping": "Age",
    },
}
```

Two hard-coded demographic scenarios are provided for demonstration:

| Dimension | Majority Group | Approval % | Minority Group | Approval % |
|---|---|---|---|---|
| Gender | Group A | 85% | Group B | 42% |
| Age | Age 26+ | 78% | Age 18–25 | 51% |

These values are illustrative and intentionally show one scenario where the 80% rule is **violated** (Gender: 42/85 ≈ 0.49) and one where it is **satisfied** (Age: 51/78 ≈ 0.65, which is below 0.80 — also a failure, showing that bias can exist in both built-in examples).

### Fairness Engine: `evaluate_fairness()`

This single function is the computational heart of the application. It accepts a dictionary containing `labels`, `approval_rates`, and `threshold`, and returns a rich result dictionary.

```python
def evaluate_fairness(payload: dict) -> dict:
    labels          = payload["labels"]
    approval_rates  = payload["approval_rates"]  # [majority_rate, minority_rate]
    threshold       = float(payload.get("threshold", 0.8))

    majority_rate = float(approval_rates[0])
    minority_rate = float(approval_rates[1])

    ratio        = minority_rate / majority_rate   # Disparate Impact Ratio
    parity_gap   = majority_rate - minority_rate   # Raw approval gap in percentage points
    status       = "Bias Detected" if ratio < threshold else "Fair Model"
    ...
```

**Returned dictionary keys:**

| Key | Type | Description |
|---|---|---|
| `data.labels` | list[str] | Group labels as provided |
| `data.approval_rates` | list[float] | Approval rates as provided |
| `data.threshold` | float | Fairness threshold used |
| `data.required_minority_rate` | float | Minimum minority approval % to satisfy the threshold (`majority_rate × threshold`) |
| `ratio` | float | Disparate Impact Ratio (2 decimal places) |
| `parity_gap` | float | Majority rate minus minority rate, in percentage points |
| `majority_rate` | float | Approval rate of the majority group |
| `minority_rate` | float | Approval rate of the minority group |
| `fairness_score` | float | Normalised score 0–100%, capped at 100% (`min(ratio/threshold, 1.0) × 100`) |
| `status` | str | `"Bias Detected"` or `"Fair Model"` |
| `recommendation` | str | One-sentence actionable guidance |

### API Routes

#### `GET /` — Dashboard page

Renders `templates/index.html` using Flask's `render_template`. No parameters.

#### `GET /audit-data` — Simulated audit

Query parameter: `dimension` (`gender` or `age`, defaults to `gender`).

Looks up the matching entry in `SIMULATED_DATASETS`, calls `evaluate_fairness()`, and appends `dimension` and `grouping` keys to the response before returning JSON.

#### `POST /audit-data` — Custom audit

Accepts a JSON body and runs full server-side validation before calling `evaluate_fairness()`.

---

## 6. Frontend: `templates/index.html`

The HTML file is a **Jinja2 template** served by Flask. It contains no logic — it is purely structural markup.

**Key sections:**

| Section | HTML element | Purpose |
|---|---|---|
| Background orbs | `<div class="bg-orb orb-1/2">` | Decorative animated blobs (CSS only, `aria-hidden`) |
| Top bar | `<header class="topbar">` | Application title and subtitle |
| Audit Controls | `<section class="controls-panel">` | Sample dataset selector + Run Sample Audit button |
| Custom Simulation | Sub-section of controls | 5-field form (2 labels, 2 rates, 1 threshold) + Run Custom Audit button |
| KPI Cards | `<section class="stats-grid">` | 4 live metric tiles: Status, Ratio, Parity Gap, Fairness Score |
| Charts | `<section class="chart-wrap">` | Two `<canvas>` elements for Chart.js |
| Insight Box | `<article id="insightBox">` | Full diagnostic message paragraph |
| Audit History | `<article class="history-card">` | Scrollable table of past audit runs (kept in JS memory) |

External dependencies loaded in `<head>`:
- **Chart.js** (CDN): `https://cdn.jsdelivr.net/npm/chart.js` — for bar charts
- **Space Grotesk** (Google Fonts): body text
- **IBM Plex Serif** (Google Fonts): dashboard heading

---

## 7. Frontend Logic: `static/app.js`

All client-side behaviour lives in this single file. There is no bundler, no framework — just plain ES2017+ JavaScript.

### Global State

```js
let approvalChart;       // Chart.js instance for the approval-rate bar chart
let ratioChart;          // Chart.js instance for the ratio comparison chart
const MAX_HISTORY = 8;   // Maximum audit history rows kept in memory
const auditHistory = []; // In-memory array of { kind, ratio, status } objects
```

### Functions

| Function | Description |
|---|---|
| `formatPercent(value)` | Utility — formats a number as `"XX.X%"` |
| `setInsight(message, isError)` | Writes a message to the Insight Box; toggles the `.error` CSS class for red styling on errors |
| `renderKpis(result)` | Updates the 4 KPI card headings from a result object |
| `renderHistory()` | Re-renders the entire history `<tbody>` from `auditHistory[]` |
| `addHistoryEntry(kind, result)` | Prepends a new entry to `auditHistory[]`, trims to `MAX_HISTORY`, calls `renderHistory()` |
| `renderCharts(result)` | Destroys any existing Chart.js instances and creates two new ones |
| `renderAuditResults(result, auditKind)` | Orchestrates all rendering: KPIs → charts → history → insight |
| `runAudit()` | Reads the `<select>` value, calls `GET /audit-data?dimension=...`, passes result to `renderAuditResults` |
| `runCustomAudit()` | Reads all 5 form inputs, calls `POST /audit-data` with JSON body, handles validation errors inline |

### Charts

**Chart 1 — Loan Approval Rate** (`biasChart` canvas):
- Type: `bar`
- X-axis labels: the two group labels from the result
- Y-axis: 0–100% (approval rate)
- Bars: green for majority group, red for minority group

**Chart 2 — Disparate Impact** (`ratioChart` canvas):
- Type: `bar`
- X-axis labels: `["Observed Ratio", "Threshold Ratio"]`
- Y-axis: 0–1.2 (ratio scale)
- Bars: blue for observed ratio, yellow/gold for threshold — visual comparison makes it immediately obvious whether the model passes or fails

### Auto-Run on Load

```js
window.addEventListener("load", runAudit);
```

The dashboard automatically runs the Gender audit when the page first loads, so the user sees live data immediately without having to click anything.

---

## 8. Styling: `static/style.css`

The stylesheet uses **CSS custom properties** (variables) defined in `:root` for a consistent colour palette:

| Variable | Value | Used for |
|---|---|---|
| `--bg-1` | `#f4efe6` | Page background gradient start |
| `--bg-2` | `#dbe9ee` | Page background gradient end |
| `--panel` | `#fffdf8` | Panel / card backgrounds |
| `--ink` | `#14212b` | Primary text |
| `--muted` | `#4d687a` | Secondary / label text |
| `--accent` | `#0d7c66` | Primary button (green) |
| `--warn` | `#b63f4d` | Warning accent, insight card border |
| `--cool` | `#2d6cdf` | History card border, secondary button |

**Layout approach:** CSS Grid throughout — `.main-content`, `.stats-grid`, `.chart-wrap`, `.lower-grid`, and `.custom-grid` are all CSS Grid containers with `gap` spacing. This gives the dashboard its clean, structured two-column appearance on desktop.

**Responsiveness:**
- At ≤ 980 px: KPI grid collapses from 4 columns to 2; charts and lower panels stack vertically.
- At ≤ 640 px: everything collapses to a single column; chart height reduces to 285 px to preserve readability on small phones.

**Animated background orbs:** Two `position: fixed` blurred circles (`.bg-orb`) use a CSS `@keyframes drift` animation to float gently, adding visual depth without affecting layout.

---

## 9. Fairness Metrics Explained

### Disparate Impact Ratio

```
ratio = minority_approval_rate / majority_approval_rate
```

This is the primary metric. A value of `1.0` means both groups are approved at exactly the same rate (perfect parity). A value below `1.0` means the minority group is approved less frequently.

### The 80% Rule (Four-Fifths Rule)

The 80% rule states: if the selection rate (approval rate) of any protected group is less than **80%** of the rate of the highest-scoring group, that difference is considered evidence of adverse impact.

```
Bias Detected : ratio < threshold (default 0.8)
Fair Model    : ratio >= threshold
```

Example — Gender dataset:
```
ratio = 42 / 85 = 0.494  →  0.494 < 0.8  →  "Bias Detected"
```

### Parity Gap

```
parity_gap = majority_rate - minority_rate
```

This is the raw difference in percentage points between the two groups' approval rates. While the ratio tells you the *relative* disparity, the parity gap quantifies the *absolute* shortfall. For the Gender dataset: `85 - 42 = 43 percentage points`.

### Fairness Score

```
fairness_score = min(ratio / threshold, 1.0) × 100
```

A normalised 0–100% score expressing how close the model is to satisfying the threshold. A score of `100%` means the model fully meets the fairness requirement. Scores below `100%` proportionally reflect how far short the model falls.

### Required Minority Rate

```
required_minority_rate = majority_rate × threshold
```

The minimum approval rate the minority group would need to achieve in order to satisfy the threshold. For the Gender dataset with the default 0.8 threshold: `85 × 0.8 = 68%`. This gives a concrete, actionable target for model improvement.

### Recommendation Text

The server returns one of two messages depending on the outcome:

- **Bias Detected:** *"Review training data and feature engineering for proxy bias, then retrain with fairness constraints."*
- **Fair Model:** *"Continue monitoring with fresh cohorts and drift checks to sustain fairness over time."*

---

## 10. Input Validation Rules

The `POST /audit-data` endpoint enforces the following rules server-side:

| Rule | Error message | HTTP status |
|---|---|---|
| `approval_rates` must contain exactly 2 values | `"approval_rates must contain exactly two numeric values."` | 400 |
| Both rates and threshold must be numeric | `"approval_rates and threshold must be numeric."` | 400 |
| Majority rate must be > 0; minority rate must be ≥ 0 | `"approval_rates must be valid percentages and majority must be > 0."` | 400 |
| Both rates must be ≤ 100 | `"approval_rates must be in the range 0-100."` | 400 |
| Threshold must be in (0, 1] | `"threshold must be in the range (0, 1]."` | 400 |

These errors are caught by `runCustomAudit()` in `app.js` and displayed in the Insight Box with red styling.

---

## 11. API Reference

### `GET /audit-data`

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `dimension` | string | `"gender"` | Dataset to use. Accepts `"gender"` or `"age"`. |

**Success response (200):**

```json
{
  "data": {
    "labels": ["Group A (Majority)", "Group B (Minority)"],
    "approval_rates": [85, 42],
    "threshold": 0.8,
    "required_minority_rate": 68.0
  },
  "ratio": 0.49,
  "parity_gap": 43.0,
  "majority_rate": 85.0,
  "minority_rate": 42.0,
  "fairness_score": 61.76,
  "status": "Bias Detected",
  "recommendation": "Review training data and feature engineering for proxy bias, then retrain with fairness constraints.",
  "dimension": "gender",
  "grouping": "Gender"
}
```

---

### `POST /audit-data`

**Request body (JSON):**

```json
{
  "labels": ["Group A (Majority)", "Group B (Minority)"],
  "approval_rates": [85, 42],
  "threshold": 0.8
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `labels` | list[str] | No | Display names for the two groups. Defaults to `["Group A (Majority)", "Group B (Minority)"]`. |
| `approval_rates` | list[number] | Yes | Exactly two values: `[majority_rate, minority_rate]`, both in the range 0–100. |
| `threshold` | number | No | Fairness threshold in the range (0, 1]. Defaults to `0.8`. |

**Success response (200):** Same structure as `GET /audit-data` but without the `dimension` and `grouping` keys.

**Error response (400):**

```json
{ "error": "<validation message>" }
```

---

## 12. Run Locally

### Prerequisites

- Python 3.9 or later
- pip

### Steps

1. Clone the repository:

```bash
git clone https://github.com/sundara-raghav/Responsible-AI.git
cd Responsible-AI
```

2. (Optional but recommended) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate     # macOS / Linux
.venv\Scripts\activate        # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the development server:

```bash
python app.py
```

5. Open your browser and navigate to `http://127.0.0.1:5000`.

The Gender audit runs automatically on load. Use the **Sample Dataset** selector to switch to Age, or fill in the **Custom Simulation Input** form and click **Run Custom Audit** to test arbitrary values.

---

## 13. Example Walkthrough

### Scenario: Does the model treat younger applicants fairly?

1. Open the dashboard at `http://127.0.0.1:5000`.
2. Select **Age** from the Sample Dataset dropdown and click **Run Sample Audit**.
3. The dashboard shows:
   - **Status:** Bias Detected
   - **Disparate Impact Ratio:** 0.65 (Age 18–25 approved at 51% vs Age 26+ at 78%)
   - **Parity Gap:** 27.0 pts
   - **Fairness Score:** 81.41%
   - **Required Minority Rate:** 62.4% — young applicants need at least 62.4% approval to satisfy the 80% rule
4. The Insight Box explains: the ratio of 0.65 is below the 0.8 threshold, and recommends reviewing training data for proxy bias.

### Scenario: Testing a theoretically fair model

Fill the Custom Simulation form with:
- Group A Approval %: `80`
- Group B Approval %: `75`
- Fairness Threshold: `0.8`

The ratio is `75/80 = 0.9375`, which exceeds the 0.8 threshold, resulting in **Fair Model** status and a recommendation to continue monitoring.