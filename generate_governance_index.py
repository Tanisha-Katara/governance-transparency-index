#!/usr/bin/env python3
"""
Generates the Governance Transparency & Engagement Index dashboard.

HOW TO UPDATE (for the team):
    1. Add a new month's scores to MONTHLY_SCORES below
    2. Run: python3 generate_governance_index.py
    3. Commit the updated governance-index.html

Or: use the CSV upload button on the dashboard itself to preview new data.

The CSV source is: "Filecoin Governance Transparency and Engagement Index - Final Scores.csv"
"""

import json
from datetime import datetime

# =============================================================================
# DATA — Edit this section to add new months
# =============================================================================

# Category definitions with weights (must sum to 1.0)
# Denominators from the CSV: Artifacts=10, CoreDevs=6, Comms=9, GitHub=18
CATEGORIES = [
    {
        "id": "artifacts",
        "name": "Published Governance Artifacts",
        "short": "Artifacts",
        "weight": 0.30,
        "color": "#0891b2",       # cyan-600
        "description": "Measures existence and freshness of canonical governance documents.",
        "denominator": "10 points (2 + 4 + 4)",
        "metrics": [
            "FIP Editor Handbook published & current",
            "Governance Overview docs published & current",
            "Monthly Governance Summary Reports",
        ],
    },
    {
        "id": "core_devs",
        "name": "Core Devs Transparency",
        "short": "Core Devs",
        "weight": 0.35,
        "color": "#7c3aed",       # violet-600
        "description": "Tracks documentation quality of core developer meetings.",
        "denominator": "6 points (1 + 1 + 4)",
        "metrics": [
            "Core Devs meeting recordings published",
            "Meeting notes published on time",
            "Agenda published in advance with FIP discussion items",
        ],
    },
    {
        "id": "comms",
        "name": "Governance Communications",
        "short": "Communications",
        "weight": 0.25,
        "color": "#ea580c",       # orange-600
        # Note: This category was mislabeled as "Core Devs Transparency" in the
        # second occurrence in the source CSV. The correct name is "Governance
        # Communications" based on the category structure (weight 25%, denom 9).
        "description": "Evaluates public communication about governance activities.",
        "denominator": "9 points (6 + 3)",
        "metrics": [
            "Governance blog posts or newsletters published",
            "Community calls with governance updates",
            "Social media or forum posts about governance decisions",
        ],
    },
    {
        "id": "github",
        "name": "GitHub Activity Index",
        "short": "GitHub",
        "weight": 0.10,
        "color": "#059669",       # emerald-600
        "description": "Measures engagement quality on governance repositories.",
        "denominator": "18 points (6 + 6 + 6)",
        "metrics": [
            "New FIPs submitted and advancing through lifecycle",
            "PR review turnaround and community engagement",
            "Discussion activity on governance repos",
        ],
    },
]

# Monthly scores — each value is a ratio between 0 and 1
# To add a new month: copy the last entry, update the key and scores.
MONTHLY_SCORES = {
    "2024-07": {"artifacts": 0.800, "core_devs": 0.333, "comms": 0.000, "github": 0.167},
    "2024-08": {"artifacts": 0.800, "core_devs": 0.667, "comms": 0.556, "github": 0.389},
    "2024-09": {"artifacts": 0.800, "core_devs": 0.500, "comms": 0.778, "github": 0.389},
    "2024-10": {"artifacts": 0.600, "core_devs": 0.833, "comms": 0.667, "github": 0.500},
    "2024-11": {"artifacts": 0.600, "core_devs": 0.667, "comms": 0.556, "github": 0.611},
    "2024-12": {"artifacts": 0.500, "core_devs": 0.667, "comms": 0.667, "github": 0.278},
}

# =============================================================================
# COMPUTATION
# =============================================================================

def compute_index_scores():
    """Compute weighted index scores for each month."""
    weights = {c["id"]: c["weight"] for c in CATEGORIES}
    results = []
    for month_key in sorted(MONTHLY_SCORES.keys()):
        scores = MONTHLY_SCORES[month_key]
        weighted = sum(scores[cat_id] * weights[cat_id] for cat_id in scores)
        results.append({
            "month": month_key,
            "category_scores": scores,
            "index_score": round(weighted, 3),
        })
    return results


def compute_quarterly(monthly_results):
    """Aggregate monthly results into quarters."""
    quarters = {}
    for m in monthly_results:
        year, month = m["month"].split("-")
        q_num = (int(month) - 1) // 3 + 1
        q_key = f"{year}-Q{q_num}"
        if q_key not in quarters:
            quarters[q_key] = []
        quarters[q_key].append(m)

    quarterly = []
    for q_key in sorted(quarters.keys()):
        months = quarters[q_key]
        avg_index = round(sum(m["index_score"] for m in months) / len(months), 3)
        cat_avgs = {}
        for cat in CATEGORIES:
            cat_avgs[cat["id"]] = round(
                sum(m["category_scores"][cat["id"]] for m in months) / len(months), 3
            )
        quarterly.append({
            "quarter": q_key,
            "avg_index": avg_index,
            "category_avgs": cat_avgs,
            "month_count": len(months),
        })
    return quarterly


# =============================================================================
# HTML GENERATION
# =============================================================================

def format_month_label(month_key):
    """Convert '2024-07' to 'Jul 2024'."""
    dt = datetime.strptime(month_key, "%Y-%m")
    return dt.strftime("%b %Y")


def format_month_short(month_key):
    """Convert '2024-07' to 'Jul'."""
    dt = datetime.strptime(month_key, "%Y-%m")
    return dt.strftime("%b")


def format_quarter_label(q_key):
    """Convert '2024-Q3' to 'Q3 2024'."""
    year, q = q_key.split("-")
    return f"{q} {year}"


def generate_html(monthly, quarterly, categories):
    """Generate the full HTML dashboard."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    latest = monthly[-1]
    latest_score = latest["index_score"]
    latest_pct = round(latest_score * 100, 1)
    latest_label = format_month_label(latest["month"])

    # Prepare JSON data for JS charts
    chart_data = {
        "months": [format_month_short(m["month"]) for m in monthly],
        "monthsFull": [format_month_label(m["month"]) for m in monthly],
        "indexScores": [round(m["index_score"] * 100, 1) for m in monthly],
        "categories": [],
    }
    for cat in categories:
        chart_data["categories"].append({
            "id": cat["id"],
            "name": cat["name"],
            "short": cat["short"],
            "weight": cat["weight"],
            "color": cat["color"],
            "scores": [round(m["category_scores"][cat["id"]] * 100, 1) for m in monthly],
        })

    chart_data_json = json.dumps(chart_data)

    # Build category cards HTML
    cat_cards_html = ""
    for cat in categories:
        cat_score = latest["category_scores"][cat["id"]]
        cat_pct = round(cat_score * 100, 1)
        metrics_html = "".join(f'<li>{m}</li>' for m in cat["metrics"])
        cat_cards_html += f"""
        <div class="cat-card">
            <div class="cat-card-header">
                <div class="cat-dot" style="background:{cat['color']};"></div>
                <div>
                    <h3>{cat['name']}</h3>
                    <span class="cat-weight" style="color:{cat['color']};">{int(cat['weight']*100)}% weight</span>
                </div>
            </div>
            <div class="cat-score-ring">
                <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="6"/>
                    <circle cx="40" cy="40" r="34" fill="none" stroke="{cat['color']}" stroke-width="6"
                        stroke-dasharray="{cat_pct * 2.136} {213.6 - cat_pct * 2.136}"
                        stroke-dashoffset="53.4" stroke-linecap="round"/>
                    <text x="40" y="44" text-anchor="middle" fill="#e2e8f0" font-size="16" font-weight="700">{cat_pct}</text>
                </svg>
                <span class="cat-max">/ 100</span>
            </div>
            <p class="cat-desc">{cat['description']}</p>
            <details class="cat-metrics">
                <summary>View metrics</summary>
                <ul>{metrics_html}</ul>
                <p class="cat-denom">Denominator: {cat['denominator']}</p>
            </details>
        </div>
        """

    # Quarterly cards
    q_cards_html = ""
    for i, q in enumerate(quarterly):
        q_label = format_quarter_label(q["quarter"])
        q_pct = round(q["avg_index"] * 100, 1)
        delta_html = ""
        if i > 0:
            prev = quarterly[i-1]["avg_index"]
            d = q["avg_index"] - prev
            d_pct = round(d / prev * 100, 1) if prev else 0
            arrow = "&#9650;" if d >= 0 else "&#9660;"
            color = "#059669" if d >= 0 else "#ef4444"
            delta_html = f'<span class="q-delta" style="color:{color};">{arrow} {d_pct:+.1f}%</span>'
        q_cards_html += f"""
        <div class="q-card">
            <div class="q-label">{q_label}</div>
            <div class="q-score">{q_pct}</div>
            {delta_html}
        </div>
        """

    # Data table
    table_header = "<tr><th>Month</th>"
    for cat in categories:
        table_header += f"<th>{cat['short']}</th>"
    table_header += "<th>Index</th></tr>"
    table_rows = ""
    for m in monthly:
        table_rows += f"<tr><td>{format_month_label(m['month'])}</td>"
        for cat in categories:
            v = round(m["category_scores"][cat["id"]] * 100, 1)
            table_rows += f"<td>{v}%</td>"
        table_rows += f"<td><strong>{round(m['index_score'] * 100, 1)}%</strong></td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Transparency Index — Filecoin</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: rgb(30, 41, 59);
            color: rgb(226, 232, 240);
            min-height: 100vh;
            line-height: 1.5;
        }}

        /* ---- layout ---- */
        .page {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 60px; }}

        .header {{
            text-align: center;
            padding: 48px 20px 32px;
        }}
        .header h1 {{
            font-size: 2.2em;
            font-weight: 800;
            background: linear-gradient(90deg, rgb(226,232,240) 0%, rgb(148,163,184) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header .subtitle {{
            color: rgb(100,116,139);
            font-size: 14px;
            margin-top: 4px;
        }}
        .header .desc {{
            color: rgb(148,163,184);
            max-width: 700px;
            margin: 16px auto 0;
            font-size: 14px;
            line-height: 1.6;
        }}

        .nav {{
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }}
        .nav a {{
            color: rgb(148,163,184);
            text-decoration: none;
            font-size: 13px;
            padding: 6px 14px;
            border-radius: 6px;
            border: 1px solid rgba(148,163,184,0.2);
            transition: all 0.2s;
        }}
        .nav a:hover {{
            color: #e2e8f0;
            border-color: rgba(148,163,184,0.5);
            background: rgba(148,163,184,0.1);
        }}

        /* ---- CSV upload ---- */
        .upload-bar {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }}
        .upload-btn {{
            background: rgba(148,163,184,0.1);
            color: rgb(148,163,184);
            border: 1px dashed rgba(148,163,184,0.3);
            padding: 8px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        .upload-btn:hover {{
            border-color: #0891b2;
            color: #0891b2;
        }}
        .csv-info {{
            font-size: 12px;
            color: rgb(100,116,139);
            padding: 8px 14px;
            border-radius: 8px;
            background: rgba(100,116,139,0.1);
        }}
        #csv-status {{
            text-align: center;
            font-size: 13px;
            margin-bottom: 16px;
            min-height: 20px;
        }}

        /* ---- hero score ---- */
        .hero {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .hero-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgb(100,116,139);
            margin-bottom: 12px;
        }}
        .hero-score {{
            font-size: 5em;
            font-weight: 800;
            color: #e2e8f0;
            line-height: 1;
        }}
        .hero-max {{
            font-size: 16px;
            color: rgb(100,116,139);
            margin-top: 4px;
        }}
        .hero-month {{
            font-size: 13px;
            color: rgb(100,116,139);
            margin-top: 8px;
        }}

        /* ---- quarterly row ---- */
        .q-row {{
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-bottom: 48px;
            flex-wrap: wrap;
        }}
        .q-card {{
            background: rgba(51,65,85,0.5);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 12px;
            padding: 20px 32px;
            text-align: center;
            min-width: 140px;
        }}
        .q-label {{
            font-size: 12px;
            color: rgb(100,116,139);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .q-score {{
            font-size: 2em;
            font-weight: 700;
            color: #e2e8f0;
        }}
        .q-delta {{
            font-size: 13px;
            font-weight: 600;
            margin-top: 4px;
        }}

        /* ---- section ---- */
        .section {{
            margin-bottom: 48px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: rgb(148,163,184);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-title::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(148,163,184,0.15);
        }}

        /* ---- charts ---- */
        .chart-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 48px;
        }}
        .chart-box {{
            background: rgba(51,65,85,0.4);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 12px;
            padding: 24px;
        }}
        .chart-box h3 {{
            font-size: 13px;
            color: rgb(148,163,184);
            margin-bottom: 16px;
            font-weight: 500;
        }}

        /* ---- category cards ---- */
        .cat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 48px;
        }}
        .cat-card {{
            background: rgba(51,65,85,0.4);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 12px;
            padding: 20px;
        }}
        .cat-card-header {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 16px;
        }}
        .cat-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-top: 6px;
            flex-shrink: 0;
        }}
        .cat-card h3 {{
            font-size: 14px;
            color: rgb(226,232,240);
            font-weight: 600;
            margin-bottom: 2px;
        }}
        .cat-weight {{
            font-size: 12px;
            font-weight: 500;
        }}
        .cat-score-ring {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .cat-max {{
            font-size: 13px;
            color: rgb(100,116,139);
        }}
        .cat-desc {{
            font-size: 12px;
            color: rgb(100,116,139);
            line-height: 1.5;
            margin-bottom: 10px;
        }}
        .cat-metrics {{
            font-size: 12px;
            color: rgb(100,116,139);
        }}
        .cat-metrics summary {{
            cursor: pointer;
            color: rgb(148,163,184);
            font-weight: 500;
            padding: 4px 0;
        }}
        .cat-metrics ul {{
            margin: 8px 0 6px 16px;
        }}
        .cat-metrics li {{
            margin-bottom: 4px;
        }}
        .cat-denom {{
            font-style: italic;
            margin-top: 6px;
        }}

        /* ---- weight simulator ---- */
        .simulator {{
            background: rgba(51,65,85,0.4);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 48px;
        }}
        .sim-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .sim-header h3 {{
            font-size: 14px;
            color: rgb(148,163,184);
            font-weight: 600;
        }}
        .sim-header p {{
            font-size: 12px;
            color: rgb(100,116,139);
        }}
        .sim-result {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .sim-result-score {{
            font-size: 2.5em;
            font-weight: 700;
            color: #e2e8f0;
        }}
        .sim-result-label {{
            font-size: 12px;
            color: rgb(100,116,139);
        }}
        .sim-sliders {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .sim-slider-group label {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: rgb(148,163,184);
            margin-bottom: 6px;
        }}
        .sim-slider-group input[type=range] {{
            width: 100%;
            accent-color: #0891b2;
        }}

        /* ---- data table ---- */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .data-table th, .data-table td {{
            padding: 10px 14px;
            text-align: center;
            border-bottom: 1px solid rgba(148,163,184,0.1);
        }}
        .data-table th {{
            color: rgb(100,116,139);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .data-table tr:hover td {{
            background: rgba(148,163,184,0.05);
        }}

        /* ---- methodology ---- */
        .methodology {{
            background: rgba(51,65,85,0.3);
            border: 1px solid rgba(148,163,184,0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 48px;
        }}
        .methodology summary {{
            font-size: 14px;
            font-weight: 600;
            color: rgb(148,163,184);
            cursor: pointer;
            padding: 4px 0;
        }}
        .methodology .method-body {{
            margin-top: 16px;
            font-size: 13px;
            color: rgb(100,116,139);
            line-height: 1.7;
        }}
        .methodology h4 {{
            color: rgb(148,163,184);
            margin: 16px 0 6px;
            font-size: 13px;
        }}
        .methodology code {{
            background: rgba(148,163,184,0.15);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
        }}

        /* ---- footer ---- */
        .footer {{
            text-align: center;
            padding-top: 32px;
            border-top: 1px solid rgba(148,163,184,0.1);
        }}
        .footer p {{
            font-size: 13px;
            color: rgb(100,116,139);
        }}
        .footer .update-note {{
            font-size: 12px;
            color: rgb(71,85,105);
            margin-top: 8px;
        }}

        @media (max-width: 700px) {{
            .chart-row {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 1.5em; }}
            .hero-score {{ font-size: 3.5em; }}
        }}
    </style>
</head>
<body>

<div class="page">
    <div class="header">
        <h1>Governance Transparency Index</h1>
        <div class="subtitle">Filecoin Protocol &middot; Dynamic Dashboard</div>
        <p class="desc">A quantitative framework measuring governance legibility, structure,
        and transparency. Upload your CSV data to update the dashboard in real-time.</p>
    </div>

    <div class="nav">
        <a href="index.html">&larr; Home</a>
        <a href="fips-dashboard-static.html">FIPs Dashboard</a>
        <a href="fips-timeline-tracker.html">Timeline Tracker</a>
    </div>

    <!-- CSV Upload -->
    <div class="upload-bar">
        <label class="upload-btn" id="upload-label">
            &#128203; Upload CSV
            <input type="file" id="csv-input" accept=".csv" style="display:none;">
        </label>
        <div class="csv-info">CSV Format: same layout as the Final Scores spreadsheet</div>
    </div>
    <div id="csv-status"></div>

    <!-- Hero Score -->
    <div class="hero" id="hero">
        <div class="hero-label">Overall Index Score</div>
        <div class="hero-score" id="hero-score">{latest_pct}</div>
        <div class="hero-max">OUT OF 100</div>
        <div class="hero-month" id="hero-month">{latest_label}</div>
    </div>

    <!-- Quarterly -->
    <div class="q-row" id="q-row">
        {q_cards_html}
    </div>

    <!-- Charts -->
    <div class="section">
        <div class="section-title">Score Trend</div>
        <div class="chart-row">
            <div class="chart-box">
                <h3>Category Breakdown</h3>
                <canvas id="radarChart"></canvas>
            </div>
            <div class="chart-box">
                <h3>Score Trend</h3>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Category Cards -->
    <div class="section">
        <div class="section-title">Score Components</div>
        <div class="cat-grid" id="cat-grid">
            {cat_cards_html}
        </div>
    </div>

    <!-- Weight Simulator -->
    <div class="simulator">
        <div class="sim-header">
            <div>
                <h3>Weight Simulator</h3>
                <p>Adjust category weights to see how different priorities affect the score</p>
            </div>
        </div>
        <div class="sim-result">
            <div class="sim-result-score" id="sim-score">{latest_pct}</div>
            <div class="sim-result-label">Custom Score</div>
        </div>
        <div class="sim-sliders" id="sim-sliders"></div>
    </div>

    <!-- Performance Over Time -->
    <div class="section">
        <div class="section-title">Category Performance Over Time</div>
        <div class="chart-box">
            <canvas id="areaChart"></canvas>
        </div>
    </div>

    <!-- Data Table -->
    <div class="section">
        <div class="section-title">Full Data</div>
        <div style="overflow-x:auto;">
            <table class="data-table" id="data-table">
                {table_header}
                {table_rows}
            </table>
        </div>
    </div>

    <!-- Methodology -->
    <details class="methodology">
        <summary>Methodology</summary>
        <div class="method-body">
            <h4>What is this index?</h4>
            <p>The Governance Transparency Index is a composite score measuring how open,
            communicative, and active Filecoin&rsquo;s governance processes are each month.
            It combines four categories into a single weighted score between 0 and 100.</p>

            <h4>Categories &amp; Weights</h4>
            <ul>
                <li><strong>Published Governance Artifacts (30%)</strong> &mdash;
                Existence and freshness of canonical governance documents.
                Max raw score: 10 points.</li>
                <li><strong>Core Devs Transparency (35%)</strong> &mdash;
                Documentation quality of core developer meetings.
                Max raw score: 6 points.</li>
                <li><strong>Governance Communications (25%)</strong> &mdash;
                Public communication about governance activities.
                Max raw score: 9 points.</li>
                <li><strong>GitHub Activity Index (10%)</strong> &mdash;
                Engagement quality on governance repositories.
                Max raw score: 18 points.</li>
            </ul>

            <h4>Scoring</h4>
            <p>Each category is scored as a ratio: <code>actual / max</code>,
            yielding a value between 0 and 1 (displayed as 0&ndash;100).
            The final index is the weighted sum:</p>
            <p><code>Index = 0.30 &times; Artifacts + 0.35 &times; CoreDevs
            + 0.25 &times; Comms + 0.10 &times; GitHub</code></p>

            <h4>Design Principle</h4>
            <p>This index is designed to measure transparency, not to incentivize
            engagement farming. The weights reflect the relative importance of
            each category to genuine governance legibility.</p>

            <h4>How to Update</h4>
            <p>Option 1: Edit <code>MONTHLY_SCORES</code> in
            <code>generate_governance_index.py</code> and run the script.<br>
            Option 2: Use the CSV upload button above to preview data dynamically.</p>
        </div>
    </details>

    <div class="footer">
        <p>Governance Transparency Index Framework &middot; Open Methodology</p>
        <p class="update-note">Last generated: {now} &middot;
        Data loaded from <code>generate_governance_index.py</code></p>
    </div>
</div>

<script>
// ============================================================
// Embedded data (generated by Python)
// ============================================================
const DATA = {chart_data_json};

// ============================================================
// Charts
// ============================================================

const chartDefaults = {{
    color: 'rgb(148,163,184)',
    borderColor: 'rgba(148,163,184,0.1)',
}};
Chart.defaults.color = chartDefaults.color;
Chart.defaults.borderColor = chartDefaults.borderColor;

// Radar chart
new Chart(document.getElementById('radarChart'), {{
    type: 'radar',
    data: {{
        labels: DATA.categories.map(c => c.short),
        datasets: [{{
            label: DATA.monthsFull[DATA.monthsFull.length - 1],
            data: DATA.categories.map(c => c.scores[c.scores.length - 1]),
            borderColor: '#0891b2',
            backgroundColor: 'rgba(8,145,178,0.15)',
            pointBackgroundColor: '#0891b2',
            borderWidth: 2,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            r: {{
                beginAtZero: true,
                max: 100,
                grid: {{ color: 'rgba(148,163,184,0.1)' }},
                angleLines: {{ color: 'rgba(148,163,184,0.1)' }},
                pointLabels: {{ color: 'rgb(148,163,184)', font: {{ size: 12 }} }},
                ticks: {{ display: false }}
            }}
        }}
    }}
}});

// Trend line chart
new Chart(document.getElementById('trendChart'), {{
    type: 'line',
    data: {{
        labels: DATA.months,
        datasets: [{{
            label: 'Index Score',
            data: DATA.indexScores,
            borderColor: '#0891b2',
            backgroundColor: 'rgba(8,145,178,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#0891b2',
            borderWidth: 2,
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
            y: {{ min: 0, max: 100, ticks: {{ callback: v => v + '%' }} }},
            x: {{ grid: {{ display: false }} }}
        }}
    }}
}});

// Area chart — category performance over time
new Chart(document.getElementById('areaChart'), {{
    type: 'line',
    data: {{
        labels: DATA.months,
        datasets: DATA.categories.map(c => ({{
            label: c.short + ' (' + Math.round(c.weight * 100) + '%)',
            data: c.scores,
            borderColor: c.color,
            backgroundColor: c.color + '18',
            fill: true,
            tension: 0.3,
            pointRadius: 3,
            borderWidth: 2,
        }}))
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 16 }} }} }},
        scales: {{
            y: {{ min: 0, max: 100, ticks: {{ callback: v => v + '%' }} }},
            x: {{ grid: {{ display: false }} }}
        }}
    }}
}});

// ============================================================
// Weight Simulator
// ============================================================
(function() {{
    const container = document.getElementById('sim-sliders');
    const scoreEl = document.getElementById('sim-score');
    const latestScores = {{}};
    DATA.categories.forEach(c => {{
        latestScores[c.id] = c.scores[c.scores.length - 1] / 100;
    }});

    const sliders = {{}};
    DATA.categories.forEach(c => {{
        const group = document.createElement('div');
        group.className = 'sim-slider-group';
        const label = document.createElement('label');
        label.innerHTML = '<span>' + c.short + '</span><span id="sw-' + c.id + '">'
            + Math.round(c.weight * 100) + '%</span>';
        const input = document.createElement('input');
        input.type = 'range';
        input.min = 0; input.max = 100; input.value = Math.round(c.weight * 100);
        input.dataset.catId = c.id;
        input.addEventListener('input', recalcSim);
        group.appendChild(label);
        group.appendChild(input);
        container.appendChild(group);
        sliders[c.id] = input;
    }});

    function recalcSim() {{
        let totalW = 0;
        DATA.categories.forEach(c => {{ totalW += parseInt(sliders[c.id].value); }});
        if (totalW === 0) totalW = 1;
        let score = 0;
        DATA.categories.forEach(c => {{
            const w = parseInt(sliders[c.id].value) / totalW;
            document.getElementById('sw-' + c.id).textContent = Math.round(w * 100) + '%';
            score += latestScores[c.id] * w;
        }});
        scoreEl.textContent = (score * 100).toFixed(1);
    }}
}})();

// ============================================================
// CSV Upload (dynamic preview — does not persist)
// ============================================================
document.getElementById('csv-input').addEventListener('change', function(e) {{
    const file = e.target.files[0];
    if (!file) return;
    const statusEl = document.getElementById('csv-status');
    const reader = new FileReader();
    reader.onload = function(ev) {{
        try {{
            const text = ev.target.result;
            const parsed = parseCSV(text);
            if (parsed) {{
                statusEl.innerHTML = '<span style="color:#059669;">&#10003; CSV loaded: '
                    + parsed.months.length + ' months of data</span>';
                updateDashboard(parsed);
            }}
        }} catch (err) {{
            statusEl.innerHTML = '<span style="color:#ef4444;">Error parsing CSV: '
                + err.message + '</span>';
        }}
    }};
    reader.readAsText(file);
}});

function parseCSV(text) {{
    // Parse the specific CSV format used by the Transparency Index spreadsheet
    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
    const sections = {{}};
    let currentSection = null;
    let collectingMonths = false;

    for (const line of lines) {{
        if (line.startsWith('Published Governance')) {{ currentSection = 'artifacts'; collectingMonths = false; }}
        else if (line.startsWith('Core Devs') && !sections['core_devs']) {{ currentSection = 'core_devs'; collectingMonths = false; }}
        else if (line.startsWith('Core Devs') && sections['core_devs']) {{ currentSection = 'comms'; collectingMonths = false; }}
        else if (line.startsWith('Governance Communications')) {{ currentSection = 'comms'; collectingMonths = false; }}
        else if (line.startsWith('GitHub Activity')) {{ currentSection = 'github'; collectingMonths = false; }}
        else if (line.startsWith('FINAL SCORE')) {{ currentSection = 'final'; collectingMonths = false; }}
        else if (line === 'Month,Score' || line === 'Month,Final Index Score') {{
            collectingMonths = true;
        }} else if (collectingMonths && currentSection) {{
            const parts = line.split(',');
            if (parts.length >= 2 && !isNaN(parseFloat(parts[1]))) {{
                if (!sections[currentSection]) sections[currentSection] = {{}};
                sections[currentSection][parts[0].trim()] = parseFloat(parts[1]);
            }}
        }}
    }}

    // Reconstruct DATA-like structure
    const months = Object.keys(sections['artifacts'] || sections['final'] || {{}});
    if (months.length === 0) throw new Error('No monthly data found');

    return {{
        months: months,
        indexScores: months.map(m => {{
            if (sections['final'] && sections['final'][m] !== undefined)
                return Math.round(sections['final'][m] * 1000) / 10;
            return 0;
        }}),
        categories: DATA.categories.map(c => ({{
            ...c,
            scores: months.map(m => {{
                if (sections[c.id] && sections[c.id][m] !== undefined)
                    return Math.round(sections[c.id][m] * 1000) / 10;
                return 0;
            }})
        }}))
    }};
}}

function updateDashboard(newData) {{
    // Update hero
    const lastIdx = newData.indexScores.length - 1;
    document.getElementById('hero-score').textContent = newData.indexScores[lastIdx].toFixed(1);
    document.getElementById('hero-month').textContent = newData.months[lastIdx] + ' (CSV)';
}}
</script>
</body>
</html>"""

    return html


# =============================================================================
# MAIN
# =============================================================================

def main():
    monthly = compute_index_scores()
    quarterly = compute_quarterly(monthly)
    html = generate_html(monthly, quarterly, CATEGORIES)

    output_file = "governance-index.html"
    with open(output_file, "w") as f:
        f.write(html)
    print(f"Generated {output_file}")
    print(f"Latest index score: {round(monthly[-1]['index_score'] * 100, 1)}%")


if __name__ == "__main__":
    main()
