# Filecoin Governance Transparency & Engagement Index

A dashboard tracking how transparently and consistently Filecoin governance is conducted each month, across four weighted categories.

## What it measures

| Category | Weight | What it tracks |
|---|---|---|
| Published Governance Artifacts | 30% | FIP Editor Handbook, Governance Overview docs, Monthly Summary Reports |
| Core Devs Transparency | 35% | Meeting recordings, notes published on time, advance agendas |
| Governance Communications | 25% | Blog posts/newsletters, community calls, forum/social posts |
| GitHub Activity Index | 10% | New FIPs advancing through lifecycle, PR review turnaround, community engagement |

Scores are calculated monthly from a source CSV: `Filecoin Governance Transparency and Engagement Index - Final Scores.csv`.

## Files

- `governance-index.html` — the self-contained dashboard (open in any browser, no build step)
- `generate_governance_index.py` — regenerates the HTML from hardcoded monthly scores

## How to update

**Option A — Script (for committing new data):**
1. Open `generate_governance_index.py` and add a new entry to `MONTHLY_SCORES`
2. Run:
   ```bash
   python3 generate_governance_index.py
   ```
3. Commit the updated `governance-index.html`

**Option B — CSV upload (for previewing without committing):**
Use the CSV upload button on the dashboard itself to preview new data directly in the browser.

## How to view locally

Open `governance-index.html` directly in a browser — no server or dependencies needed.
