# TODOS — FoodieMeasure AI

Items deferred from engineering reviews. Pick up any P1/P2 before the next feature sprint.

---

## P2 — Add structured logging for production observability

**What:** Add Python `logging` calls to `analyze_food()` success and failure paths so Streamlit Cloud logs show scan activity in real time.

**Why:** Currently blind in production — impossible to know if users are hitting errors, hitting quota, or how many scans are happening each day.

**Pros:**
- Zero new dependencies (stdlib `logging`)
- Streamlit Cloud surfaces console output in the app dashboard
- Immediately shows quota exhaustion, error rates, and popular dish names

**Cons:**
- Minimal — a few lines of code

**Context:** Add `import logging` and `logger = logging.getLogger("foodiemeasure")` at the top of `app.py`. Log `scan_ok` with `dish_name` and `purine_level` after a successful `analyze_food()` call. Log `scan_fail` with `type(e).__name__` in each `except` branch. Streamlit Cloud exposes these in the app's **Manage app → Logs** panel.

**Effort:** S
**Priority:** P2
**Depends on:** Nothing

---

## P3 — Daily purine budget meter

**What:** A progress bar in the sidebar showing today's cumulative purine intake vs the recommended daily limit (~300 mg for Gout patients).

**Why:** Gout management is about patterns over a day, not single meals. Users need to know "I've had 220 mg today, I'm close to my limit" — not just "this dish is 80 mg."

**Pros:**
- High clinical value — mirrors what dietitians track
- Uses data already collected in `scan_history`
- No external service needed (session-only to start)

**Cons:**
- Requires summing `total_purine_mg` from session history
- Resets on page refresh (acceptable at session-only stage)

**Context:** Sum `total_purine_mg` from `st.session_state.scan_history` for entries with today's date. Display as `st.progress(total / 300)` with colour coding (green < 200, amber < 300, red >= 300). Consider making the limit user-configurable (some patients have a lower threshold).

**Effort:** S
**Priority:** P3
**Depends on:** Nothing (session-only); Supabase if persistence is added

---

## P3 — Persistent history via Supabase (free tier)

**What:** Replace session-only `scan_history` with a Supabase Postgres database so history survives page refreshes and is accessible across devices.

**Why:** Users lose their entire scan history on every refresh. For a chronic disease management tool, persistent data is table stakes for the 12-month product vision.

**Pros:**
- Supabase free tier: 500 MB, unlimited reads, no credit card
- Enables daily purine tracking, weekly reports, doctor export
- Unlocks uric acid journal and trend charts

**Cons:**
- Requires user identity (anonymous UUID stored in browser cookie, or Google login)
- Adds `supabase-py` dependency
- Increases architectural complexity from 1 file to multi-module

**Context:** Use `supabase-py` with the Supabase anon key (safe to expose client-side). Store scans in a `scans` table: `(id, session_id, dish_name, purine_level, total_purine_mg, calories, scanned_at)`. Session identity via `st.session_state` UUID persisted in `st.query_params` or a cookie via `streamlit-cookies-controller`.

**Effort:** M
**Priority:** P3
**Depends on:** Design decision on user identity model first
