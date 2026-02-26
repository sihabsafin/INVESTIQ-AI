<div align="center">

<img src="https://img.shields.io/badge/InvestIQ-AI-00D4FF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTEyIDJMMiA3bDEwIDUgMTAtNS0xMC01ek0yIDE3bDEwIDUgMTAtNS0xMC01LTEwIDV6TTIgMTJsMTAgNSAxMC01LTEwLTUtMTAgNXoiLz48L3N2Zz4=&logoColor=white" alt="InvestIQ AI" />

# InvestIQ AI

**A 6-agent AI pipeline that performs institutional-grade startup due diligence in under 3 minutes.**

*Built for investors, analysts, and founders who make decisions on incomplete information.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=flat-square)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com)
[![Firebase](https://img.shields.io/badge/Firebase-Auth%20%2B%20Firestore-FFCA28?style=flat-square&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-00FFB3?style=flat-square)](LICENSE)

<br/>

[**Live Demo**](https://investiq-ai.streamlit.app) · [**Video Walkthrough**](https://www.linkedin.com/posts/sihabsafin_python-ai-buildinpublic-activity-7432805402154549248-d07D?utm_source=social_share_send&utm_medium=member_desktop_web&rcm=ACoAAEiVzoQById1u8Wjx5N3vhgO_z_XrH-DGKg) · [**Report a Bug**](https://github.com/sihabsafin/investiq-ai/issues) · [**Request Feature**](https://github.com/sihabsafin/investiq-ai/issues)

</div>

---

## The Problem This Solves

A VC analyst doing proper due diligence on a single startup takes **3–5 days**. That process involves pulling market data, sizing the opportunity, mapping competitors, stress-testing the financial model, cataloguing risks, and synthesizing it all into a coherent recommendation.

Most people doing startup evaluation — angels, operators, analysts at smaller funds — don't have 5 days. They have an hour. So they rely on gut feel and pitch deck narratives written by the people trying to sell them.

InvestIQ AI runs that entire workflow through a coordinated pipeline of 6 specialized AI agents. Each agent handles one domain. A synthesizer agent reads all five reports and produces a final verdict. The whole thing runs in under 3 minutes and outputs a structured, scored investment report.

It doesn't replace human judgment. It gives you a rigorous second opinion — consistently, at scale, without scheduling a call.

---

## Architecture

```
User Input (startup details)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                       │
│                  ai/pipeline.py                               │
│                                                               │
│  Agent 1          Agent 2          Agent 3                    │
│  Market           Competitive      Financial                  │
│  Intelligence  ── Landscape     ── Viability                  │
│  LLaMA 3.3 70B    LLaMA 3.3 70B   LLaMA 3.3 70B             │
│                                                               │
│  Agent 4          Agent 5          Agent 6                    │
│  Risk             Innovation       Lead Analyst               │
│  Assessment    ── Scorer        ── (Synthesizer)              │
│  DeepSeek R1      LLaMA 3.3 70B   Gemini 2.5 Flash           │
│                                                               │
│  Per-agent error isolation — one failure never kills the run  │
└───────────────────────────────────────────────────────────────┘
        │
        ▼
Structured Report
  • Overall score /100
  • 5-dimension radar breakdown
  • Invest / Consider / Reject recommendation
  • One-line verdict
  • Full per-agent analysis (readable prose)
        │
        ▼
  Save to Firestore · Export PDF · Share publicly · Compare
```

**Why this model routing?**
- Agents 1–3, 5 → `llama-3.3-70b-versatile` via Groq: fastest inference, strong instruction following
- Agent 4 (Risk) → `deepseek-r1` via Groq: chain-of-thought reasoning catches edge cases that faster models miss
- Agent 6 (Synthesis) → `gemini-2.5-flash`: best at long-context integration across 5 independent reports

All models are user-switchable in the UI at runtime.

---

## Features

### Core Analysis Engine
- **6 specialized agents** — each with its own system prompt, scoring rubric, and output schema
- **Per-agent error isolation** — if one agent fails, the pipeline continues and marks that dimension as unavailable
- **Structured JSON output** — every agent returns validated JSON; the synthesizer cannot hallucinate scores
- **Real-time terminal UI** — live execution log shows each agent as it runs, not a spinner

### User-Facing Features
| Feature | Description |
|---------|-------------|
| Startup Analyzer | Full 6-agent analysis with configurable model selection |
| Investment Score | 0–100 gauge with color-coded recommendation |
| Radar Chart | 5-dimension breakdown: Market, Competition, Financial, Risk, Innovation |
| My Analyses | Personal history, searchable and filterable by score/recommendation |
| Side-by-Side Compare | Two startups head-to-head across all dimensions |
| PDF Export | Print-ready investment report via ReportLab |
| Public Share Links | Unique token-based URLs — no account required to view |
| User Dashboard | Personal KPIs, portfolio charts, score trends, top startup |

### Platform Features (Admin)
| Feature | Description |
|---------|-------------|
| Role-Based Admin Access | UID whitelist in `secrets.toml` — zero attack surface |
| Platform KPIs | Total users, analyses, avg score, recommendation breakdown |
| Activity Feed | Real-time log of every analysis across all users |
| Analytics Charts | Daily volume, score distribution, industry breakdown |
| User Management | Per-user table with analyses count, avg score, last active |
| System Health | Live API ping for Groq, Gemini, Firestore |
| Content Moderation | Revoke public links, flag/delete suspicious high-score analyses |

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Frontend** | Streamlit 1.35+ | Rapid iteration, Python-native, handles state well for multi-page apps |
| **AI Agents** | Groq API (LLaMA 3.3 70B, DeepSeek R1) | Sub-second inference; DeepSeek R1 for chain-of-thought risk reasoning |
| **Synthesis** | Google Gemini 2.5 Flash | Best-in-class long-context synthesis across 5 independent agent reports |
| **Auth** | Firebase Auth (Email/Password) | Managed, production-grade, pyrebase4 REST integration |
| **Database** | Firestore (REST API) | Schema-less; no service account needed — user id_token for all ops |
| **PDF** | ReportLab | Full layout control; no external dependencies |
| **Charts** | Plotly | Interactive, dark-theme native, works well in Streamlit |

**On the Firestore REST approach**: The app uses Firebase REST API with user `id_token` rather than the Admin SDK. This means zero service account credentials needed — users can only access their own data, and the admin reads cross-user data via Firestore security rules that whitelist specific UIDs. Simpler to deploy, fewer secrets to manage.

---

## Project Structure

```
investiq-ai/
│
├── main.py                      # Entry point, routing, sidebar nav
│
├── ai/
│   ├── agents.py                # All 6 agent definitions, model configs, prompts
│   └── pipeline.py              # Orchestrator — runs agents, handles errors, assembles results
│
├── auth/
│   ├── firebase_auth.py         # Login, signup, session management, user registry writes
│   └── admin_auth.py            # Role-based access control (UID whitelist from secrets.toml)
│
├── db/
│   ├── firestore.py             # User-scoped CRUD — save, fetch, list, delete, share
│   └── admin_firestore.py       # Admin-scoped reads — UID discovery, platform stats, moderation
│
├── pages/
│   ├── home.py                  # Landing page
│   ├── analyze.py               # Analysis form + pipeline execution + results display
│   ├── history.py               # User's saved analyses
│   ├── compare.py               # Side-by-side comparison
│   ├── dashboard.py             # Personal user dashboard with charts
│   ├── admin.py                 # Admin control panel (role-gated)
│   └── shared.py                # Public share link viewer (no auth required)
│
├── components/
│   ├── agent_loader.py          # Terminal-style live execution UI
│   ├── gauge.py                 # Score gauge + color utilities
│   ├── radar.py                 # Plotly radar chart
│   ├── score_cards.py           # Dimension score cards, strengths/weaknesses
│   └── pdf_export.py            # ReportLab PDF generation
│
├── styles/
│   └── theme.py                 # Dark theme CSS, Space Grotesk + JetBrains Mono fonts
│
├── requirements.txt
└── .streamlit/
    └── secrets.toml             # API keys and config (never commit this)
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- A [Groq](https://console.groq.com) account (free tier works)
- A [Google AI Studio](https://aistudio.google.com/app/apikey) account (free tier works)
- A [Firebase](https://console.firebase.google.com) project with Auth + Firestore enabled

### 1. Clone and install

```bash
git clone https://github.com/yourusername/investiq-ai.git
cd investiq-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure secrets

Create `.streamlit/secrets.toml`:

```toml
[firebase]
apiKey            = "AIza..."
authDomain        = "your-project.firebaseapp.com"
projectId         = "your-project-id"
storageBucket     = "your-project.appspot.com"
messagingSenderId = "123456789"
appId             = "1:123..."

[groq]
api_key = "gsk_..."

[google]
api_key = "AIza..."

[app]
base_url = "http://localhost:8501"

# Optional — enables admin dashboard for whitelisted UIDs
[admin]
uids = ["your-firebase-uid"]
```

> **Getting your Firebase UID:** Firebase Console → Authentication → Users → copy the value in the "User UID" column after you create your first account.

### 3. Set Firestore Security Rules

In Firebase Console → Firestore Database → Rules, paste:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null && request.auth.uid in ["YOUR_ADMIN_UID"];
    }

    match /users/{userId}/analyses/{analysisId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    match /{path=**}/analyses/{analysisId} {
      allow read: if request.auth != null && request.auth.uid in ["YOUR_ADMIN_UID"];
    }

    match /{path=**}/analyses/{analysisId} {
      allow read: if resource.data.is_public == true;
    }

    match /platform_stats/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null && request.auth.uid in ["YOUR_ADMIN_UID"];
    }
  }
}
```

Replace `YOUR_ADMIN_UID` with your Firebase UID. Click **Publish**.

### 4. Run

```bash
streamlit run main.py
```

Open `http://localhost:8501`, sign up for an account, and run your first analysis.

---

## Deploying to Streamlit Cloud

1. Push your repository to GitHub (make sure `.streamlit/secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repository, branch `main`, main file `main.py`
4. Click **Advanced settings** → **Secrets** → paste the entire contents of your `secrets.toml`
5. Update `[app] base_url` to your Streamlit Cloud URL (e.g. `https://your-app.streamlit.app`)
6. Click **Deploy**

---

## The 6 Agents — What They Actually Do

<details>
<summary><b>Agent 1 — Market Intelligence</b> (click to expand)</summary>

**Model:** `llama-3.3-70b-versatile` via Groq

Evaluates the startup's market opportunity with a focus on TAM/SAM/SOM sizing, demand validation, and timing. The agent looks for evidence of organic demand signals rather than accepting projected market size numbers at face value. It scores across: market size, growth rate, demand evidence, market timing, and geographic reach.

**Output fields:** `market_score` (0–10), `market_size_assessment`, `growth_potential`, `target_market_fit`, `market_timing`, `key_opportunities []`, `market_risks []`, `summary`

</details>

<details>
<summary><b>Agent 2 — Competitive Landscape</b> (click to expand)</summary>

**Model:** `llama-3.3-70b-versatile` via Groq

Maps the competitive environment, identifies direct and indirect competitors, and assesses defensibility. The agent specifically looks for moat evidence — network effects, switching costs, proprietary data, or regulatory barriers. It penalises startups that claim "no competition" without structural justification.

**Output fields:** `competition_score` (0–10), `competitive_intensity`, `direct_competitors []`, `indirect_competitors []`, `competitive_advantages []`, `competitive_risks []`, `moat_assessment`, `summary`

</details>

<details>
<summary><b>Agent 3 — Financial Viability</b> (click to expand)</summary>

**Model:** `llama-3.3-70b-versatile` via Groq

Assesses the business model's financial logic — unit economics, revenue model clarity, burn rate sustainability, and path to profitability. Evaluates what can be inferred from the available information rather than requiring a full P&L. Applies higher scrutiny to claims that lack supporting metrics.

**Output fields:** `financial_score` (0–10), `revenue_model_clarity`, `unit_economics`, `burn_sustainability`, `funding_efficiency`, `financial_strengths []`, `financial_concerns []`, `summary`

</details>

<details>
<summary><b>Agent 4 — Risk Assessment</b> (click to expand)</summary>

**Model:** `deepseek-r1-distill-llama-70b` via Groq

The only agent using a chain-of-thought reasoning model. DeepSeek R1 is specifically chosen here because risk identification benefits from explicit step-by-step reasoning — the model works through regulatory exposure, execution risk, founder risk, technology risk, and macro risk systematically. Its `<think>` blocks are stripped before output; only the final structured assessment is returned.

**Output fields:** `risk_score` (0–10, inverted — higher is safer), `overall_risk_level`, `regulatory_risk`, `execution_risk`, `market_risk`, `technology_risk`, `top_risks []`, `risk_mitigants []`, `summary`

</details>

<details>
<summary><b>Agent 5 — Innovation Scorer</b> (click to expand)</summary>

**Model:** `llama-3.3-70b-versatile` via Groq

Evaluates the novelty and defensibility of the startup's core innovation — whether it's technology, business model, distribution, or some combination. The agent specifically distinguishes between "new application of existing tech" and "genuinely novel approach" and scores accordingly. It avoids inflating scores for buzzword-heavy descriptions.

**Output fields:** `innovation_score` (0–10), `innovation_type`, `technical_novelty`, `business_model_innovation`, `ip_potential`, `innovation_strengths []`, `innovation_limitations []`, `summary`

</details>

<details>
<summary><b>Agent 6 — Lead Analyst (Synthesizer)</b> (click to expand)</summary>

**Model:** `gemini-2.5-flash` via Google AI

Reads all five agent reports and produces the final integrated analysis. Gemini 2.5 Flash is used here specifically for its long-context window and synthesis capability — it receives the full structured output from all 5 agents and must reconcile disagreements between them (e.g., a strong market score with a weak financial score), produce a weighted overall assessment, and write a coherent one-line verdict that a human analyst would be proud of.

**Output fields:** `overall_investment_score` (0–100), `final_recommendation` (Strong Invest / Consider / Reject), `one_line_verdict`, `key_strengths []`, `key_weaknesses []`, `investment_thesis`, `concerns`, `summary`

</details>

---

## Configuration Reference

### Model Selector

Users can switch models at runtime from the sidebar. Supported configurations:

| Setting | Options |
|---------|---------|
| Primary provider | `groq` \| `gemini` |
| Groq model | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `deepseek-r1-distill-llama-70b`, `gemma2-9b-it`, `mixtral-8x7b-32768` |
| Gemini model | `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash` |
| Synthesizer | `groq` \| `gemini` |

Agent 4 (Risk) always uses DeepSeek R1 regardless of primary model selection — the chain-of-thought reasoning is structural, not optional.

### Admin Access

Admin access is controlled entirely through `secrets.toml`. No database writes, no UI toggle:

```toml
[admin]
uids = ["uid1", "uid2"]  # Firebase UIDs of admin accounts
```

Accounts in this list see a `🛡️ Admin Panel` button in the sidebar. All other accounts see nothing. The check happens server-side on every page render.

---

## Data Model

Each analysis stored in Firestore at `users/{uid}/analyses/{docId}`:

```
startup_name          string
description           string
industry              string
target_market         string
business_model        string
revenue_model         string
funding_stage         string

overall_investment_score    int (0–100)
final_recommendation        string
one_line_verdict            string
key_strengths               string[]
key_weaknesses              string[]
investment_thesis           string

market_score          int (0–10)
competition_score     int (0–10)
financial_score       int (0–10)
risk_score            int (0–10)
innovation_score      int (0–10)

market_analysis       object (full agent output)
competition_analysis  object
financial_analysis    object
risk_analysis         object
innovation_analysis   object

uid                   string
doc_id                string
created_at            ISO 8601 timestamp
is_public             bool
public_token          string (UUID)
```

---

## Known Limitations

**This is a v1 production build. These are honest limitations, not excuses:**

- **No real-time data** — agents reason from the description you provide. They don't crawl the web for current market data, competitor funding rounds, or regulatory filings. What goes in shapes what comes out.

- **Score calibration** — the scoring rubric was designed for early-stage startups (pre-seed through Series A). Later-stage companies with complex financials may receive lower scores than their actual investment merit warrants.

- **Single-language input** — agents perform best with English-language startup descriptions. Non-English inputs may produce lower-quality analysis.

- **Firebase free tier limits** — Firestore has a 50k read/20k write daily limit on the free Spark plan. At scale, you'll hit this. Upgrade to Blaze (pay-as-you-go) before launching publicly.

- **No streaming** — agent responses aren't streamed; each agent completes before the next starts. The terminal UI gives the appearance of real-time progress, but there's no partial output until each agent finishes.

---

## Contributing

Issues and PRs are open. A few things worth knowing before you contribute:

- The agent prompt engineering in `ai/agents.py` is the most consequential code in the repo. Changes to scoring rubrics need to be tested against the full prompt suite in the test section below.
- The Firestore REST layer in `db/firestore.py` deliberately avoids the Firebase Admin SDK. Keep it that way — it means zero service account credentials for deployment.
- All HTML in Streamlit `st.markdown()` blocks must be HTML comment-free. Streamlit's sanitizer strips comments and corrupts surrounding markup.

```bash
# Run the app locally before submitting a PR
streamlit run main.py

# Check for syntax errors across all Python files
python -m py_compile ai/agents.py ai/pipeline.py auth/*.py db/*.py pages/*.py components/*.py
```

---

## License

MIT. Do what you want with it. If you build something interesting on top of this architecture, I'd genuinely like to hear about it.

---

<div align="center">

Built by [Sihab Islam Safin](https://linkedin.com/in/sihabsafin)

*If this project saved you time or taught you something, a ⭐ on the repo is appreciated.*

</div>
