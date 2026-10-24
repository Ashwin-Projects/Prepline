# UI redesign + "How PREPLINE Works" scroll story: design

Date: 2026-10-24 · Status: approved in brainstorming, awaiting spec review · Scope: `dashboard/web/` only

## Goal

Make the PREPLINE dashboard look substantially better and add a memorable, scroll-driven explanation of how PREPLINE
works. All existing functionality, data, scoring logic, routes and workflows stay as they are.

## Decisions (owner, 2026-10-24)

| Question | Decision |
|---|---|
| Scroll visuals | Code-native SVG/DOM scenes drawn from live API data. No Higgsfield/AI generation and no paid calls. This uses scroll-site-generator's "still + animation / pure animation" chapter path. |
| Placement | New route `/how-it-works`, full-bleed. `/` stays the Overview. |
| Visual direction | Editorial academic: warm paper / deep ink, a serif display face, one ink-blue accent, hairline rules, numbered chapters. |
| Motion technique | The `motion` package (useScroll/useTransform), lazy-loaded on the story route only. |

## Non-goals and hard constraints

- No changes to `backend/`, `pipeline/`, `config/`, `data/`, `results/`, the API, the taxonomy or the scoring.
- Never hard-code, invent or round away displayed values. Every number in the story comes from the existing endpoints.
- Every existing feature stays: the charts, tables, filters, company selector, score and confidence badges,
  Provisional chip, priority gaps, study links, PDF download, theme toggle, limitations text and all `data-testid` hooks.
- No new paid services, no secrets, no 21st.dev dependency (its MCP is not installed).

## 1. Story: `/how-it-works`

A full-bleed page outside the sidebar layout, with its own slim header: a serif wordmark, the existing `TargetSelect`,
the theme toggle and a "Dashboard →" link. The selected target is shared with the dashboard (`TargetProvider`).

Data: `GET /api/v1/results/{target}` and `GET /api/v1/comparison` via the existing `useApi`. While loading, the page
shows chapter text with skeleton visuals; on an API error, the existing `ErrorState`.

| # | Chapter | Visual (scroll-scrubbed) | Data used |
|---|---|---|---|
| 0 | Opening | Serif headline posing the question; scroll cue | none |
| §1 | University syllabus | Course codes from the file names stack as index cards, then collapse into one combined syllabus | `result.syllabus_files` (count and codes parsed from file names) |
| §2 | Taxonomy | Topic dots gather into domain clusters, then split by type | `topics[]`: total, per-domain counts, `high_level_concept` / `granular_skill` counts |
| §3 | Interview evidence | Per company, one mark per collected report; filtered-out marks fade; the gate line at `min_reports` | comparison rows: `raw_report_count`, `report_count`, `min_reports`, `density_gate_passed`; selected target's `interview_filter` |
| §4 | Alignment and scoring | Connectors from syllabus to topics to interview evidence; S_comp counts up to the saved value; formula (existing `Tex`) | `result.S_comp`, `scoring_universe_size`, `scoring_config` (τ, γ). Insufficient data shows the existing insufficient state, never a number |
| §5 | Gaps, confidence, study | Top priority gaps as bars (existing `GapBars` styling); confidence badge + Provisional chip; mapping-limitations note; CTA | `top_priority_gaps`, `confidenceOf(result, min_reports)`; CTA links to `/`, `/confidence`, `/methodology` |

Mechanics: each chapter is a tall section (desktop about 200–250vh, mobile about 150vh) holding a `position: sticky`,
full-viewport stage. A shared `useChapterProgress(ref)` hook returns 0→1 progress (Motion `useScroll` with
`offset: ["start start", "end end"]`). Only transform and opacity are animated, with no layout properties.

Reduced motion (`useReducedMotion`): chapters render in their final state, in normal document flow, with no sticky
pinning, scrubbing or count-up. The content is identical.

Accessibility: one `h1` (opening) and an `h2` per chapter. Visuals are `aria-hidden`, with the same facts in visible
text; the CTA and links are keyboard reachable; colors meet WCAG AA in both themes.

## 2. Design system (all pages)

- **Tokens** (`src/index.css`): the same token names, so components don't change. New values:
  - light: paper background (about `#f7f5f0`), surfaces a step lighter, warm-neutral lines, ink text;
  - dark: deep ink background;
  - one ink-blue `--primary`; `--series` stays a data blue.

  `warn`, `good` and `bad` keep their meaning, re-tuned to AA on the new backgrounds.
- **Type:** `@fontsource-variable/newsreader` as `--font-display` for page titles, chapter titles and the wordmark.
  Fira Sans and Fira Code stay for UI text and data (tabular numerals).
- **Layout (`Layout.tsx`):** a serif wordmark; "How it works" as a distinct first nav entry; refined active state; the
  footer disclaimer is unchanged in content.
- **Primitives (`ui.tsx`):** `PageHeader` uses the display face plus an optional small-caps eyebrow. `Card` gets lighter
  chrome (hairline border, refined header) with the same props. Badges and chips are restyled with the same text and
  test ids.
- **Charts:** Recharts colors read from the CSS tokens so both themes match.
- **Pages:** restyled only inside their existing structure. No content, ordering or test-id changes.

## 3. Build and verification

- New files: `src/story/HowItWorks.tsx`, one component per chapter in `src/story/`, `src/story/useChapterProgress.ts`,
  `tests/story.spec.ts`. Modified files: `App.tsx` (lazy route), `Layout.tsx`, `ui.tsx`, `index.css`, page files where
  needed for styling, `package.json`.
- Dependencies: `motion`, `@fontsource-variable/newsreader`.
- Test-first: write `tests/story.spec.ts` before the story code. It checks:
  - every chapter heading renders;
  - the shown course count, topic count, report counts and S_comp equal the API values;
  - Google shows an insufficient state, not a score;
  - the CTA navigates to the Overview;
  - with emulated `reducedMotion: "reduce"`, no sticky stages and final values are shown;
  - at 360 px, `scrollWidth <= clientWidth`;
  - the theme toggle works on the story;
  - the nav entry reaches `/how-it-works`.
- Gates: `npm run build`, `npm run lint`, all existing Playwright suites (`dashboard`, `worst-case`, `study-report`),
  `python -m pytest evaluation -q` (backend untouched; run to confirm). Then a manual browser pass over every route:
  theme switch, company selection, Topic explorer filters and sorting, charts, study links, PDF download, mobile width.
- Finish: an Impeccable critique pass; refresh screenshots; update `CLAUDE.md` with the changes, decisions and test
  results.

## Risks

- **Scroll jank on the projector laptop:** mitigated by animating only transform/opacity and drawing scenes once.
- **Sticky positioning breaking inside overflow containers:** the story route sits outside `Layout`, with no ancestor
  overflow.
- **Font change shifting layouts that tests measure:** the existing worst-case suite at 360 px guards overflow.
