# FoodieMeasure AI — Claude Instructions

## Project Overview
FoodieMeasure AI is a Streamlit app that analyzes food images for Gout patients using Google Gemini AI.
It is deployed on Streamlit Cloud at: https://foodiemeasureai.streamlit.app

## Tech Stack
- Python + Streamlit
- Google Gemini API (gemini-2.5-flash-lite, free tier)
- Deployed on Streamlit Cloud (GitHub: luanle7290/foodiemeasureAI)

## gstack

Use gstack skills for all planning, code review, QA, and shipping tasks.

**IMPORTANT:** For all web browsing, use the `/browse` skill from gstack.
NEVER use `mcp__claude-in-chrome__*` tools — they are slow and unreliable compared to gstack's browser.

### Available Skills

| Skill | What it does |
|---|---|
| `/plan-ceo-review` | Product planning — review features, priorities, user value |
| `/plan-eng-review` | Engineering planning — review architecture, tech decisions |
| `/plan-design-review` | Design review — UI/UX decisions and feedback |
| `/review` | Code review — catch bugs, security issues, best practices |
| `/ship` | Ship workflow — pre-flight checks before deploying |
| `/browse` | Headless browser — QA test the live app, verify deployments |
| `/qa` | Full QA — test + fix issues found |
| `/qa-only` | QA report only — find issues without auto-fixing |
| `/qa-design-review` | QA with design eye — layout, responsiveness, visual bugs |
| `/setup-browser-cookies` | Set up browser auth cookies for protected pages |
| `/retro` | Retrospective — what went well, what to improve |
| `/document-release` | Document a release — changelog, release notes |

### Typical Workflow for This App
1. `/plan-eng-review` — before adding new features
2. `/review` — after writing code changes
3. `/browse` — to QA test the live Streamlit app
4. `/ship` — before pushing to GitHub (auto-deploys to Streamlit Cloud)
