# Design System — FoodieMeasure AI

## Product Context
- **What this is:** AI-powered food nutrition analyzer for Gout patients
- **Who it's for:** Vietnamese Gout patients, primarily 40–70 years old, on mobile
- **Space/industry:** Health & nutrition, mobile-first, Vietnamese market
- **Project type:** Streamlit web app

## Aesthetic Direction
- **Direction:** Organic/Natural + Clinical Trust
- **Decoration level:** Intentional — warm greens, subtle shadows, no decorative blobs
- **Mood:** Like a caring Vietnamese doctor who understands home cooking. Warm, approachable, and medically credible. Not sterile. Not trendy.

## Typography
- **Display/Hero:** Plus Jakarta Sans (800, 700, 600) — warm, modern, full Vietnamese tonal mark support (à ả ã á ạ ă â ê ô ơ ư đ...)
- **Body:** DM Sans (400, 500, 600) — clean, readable at 15–16px on mobile screens
- **UI/Labels:** Plus Jakarta Sans (600–700) for badges, buttons, metric labels
- **Loading:** Google Fonts CDN via @import in CSS block
- **Scale:**
  - Hero:    clamp(1.6rem, 5vw, 2.2rem) — 800 weight
  - H2:      1.25rem — 700 weight
  - Body:    1rem (16px desktop, 15px mobile) — 400 weight
  - Small:   0.875rem — 400 weight, muted color
  - Label:   0.8rem — 700 weight, uppercase+tracking for badges

## Color
- **Approach:** Restrained — greens carry the identity, color is meaningful not decorative
- **Primary:**    #1B4332 — deep forest green (headers, trust signals)
- **Accent:**     #40916C — medium green (CTAs, borders, active states)
- **Success:**    #52B788 — light green (Low purine, safe foods)
- **Neutrals:**   Surface #FDFCF9 (warm cream cards) · Background #F7FAF8 · Surface-2 #EDF4EF
- **Amber:**      #F59E0B — caution / Medium purine level (replaces old orange #f4a261)
- **Danger:**     #E63946 — High purine / cannot eat
- **Semantic:** success #52B788, warning #F59E0B, error #E63946
- **Dark mode:** Not implemented yet — see TODOS.md

## Spacing
- **Base unit:** 8px
- **Density:** Comfortable — generous enough for older users, touch-friendly
- **Mobile tap targets:** Minimum 44px height on all interactive elements; primary CTA 52px

## Layout
- **Approach:** Grid-disciplined, single-column on mobile
- **Max content width:** Streamlit wide layout (controlled by Streamlit)
- **Border radius:** Badges/pills 9999px · Cards 12px · Containers 16px · Rows 8px
- **Mobile:** Cards reduce padding at ≤640px; font-size drops to 15px

## Motion
- **Approach:** Minimal-functional — nothing that slows older users
- **Primary CTA:** translateY(-1px) + box-shadow lift on hover (150ms ease-out)
- **No entrance animations** — Streamlit re-renders on every interaction

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-19 | Plus Jakarta Sans + DM Sans | Full Vietnamese tonal mark support; warm, modern, not generic Inter |
| 2026-03-19 | Amber #F59E0B for Medium purine | Old orange #f4a261 was too warm and clashed; amber reads clearer as "caution" |
| 2026-03-19 | Warm cream #FDFCF9 for cards | Cold white felt clinical/harsh; cream aligns with Organic/Natural aesthetic |
| 2026-03-19 | 5px left border (was 6px) | Thinner border is more refined; still provides clear level signal |
| 2026-03-19 | 52px min-height on primary CTA | Mobile thumb-friendly; WCAG 2.5.5 AAA touch target recommendation |
