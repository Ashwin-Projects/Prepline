# UI Redesign + "How PREPLINE Works" Scroll Story: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the PREPLINE dashboard in an editorial-academic design system and add a scroll-driven `/how-it-works` story built from live API data, without changing any feature, value or workflow.

**Architecture:**
- Design tokens keep their names, and only their values change in `src/index.css`. Every component therefore restyles
  without changing its API.
- The story is a lazy-loaded route outside `Layout`. It has five pinned chapters, each driven by a shared
  `useChapterProgress` hook on top of Motion's `useScroll`.
- All story numbers come from pure derivation functions in `src/story/data.ts`, applied to the existing `/results` and
  `/comparison` responses.

**Tech Stack:** Vite 8, React 19, TypeScript 6, Tailwind v4, Recharts, KaTeX, `motion` (new), `@fontsource-variable/newsreader` (new), Playwright.

**Spec:** `docs/superpowers/specs/2026-10-24-ui-redesign-scroll-story-design.md`

## Global Constraints

- Only `dashboard/web/` changes, plus `CLAUDE.md` and `dashboard/README.md` at the end. No changes to `backend/`,
  `pipeline/`, `config/`, `data/`, `results/`, the API, the taxonomy or the scoring.
- Never hard-code, invent or round away displayed values. Every number in the story comes from `/api/v1/results/{target}`
  or `/api/v1/comparison`.
- Keep every existing `data-testid`, visible label and text that the tests or users rely on: "Download report (PDF)",
  "Provisional", "similar scores are not a ranking", the confidence-badge text, the nav labels and the footer disclaimer.
- Animate only `transform` and `opacity`. With `prefers-reduced-motion: reduce`, nothing is pinned, scrubbed or counted
  up.
- Fonts are bundled locally (offline projector). There are no CDN or paid calls, and no 21st.dev.
- Every page has no horizontal overflow at 360 px. Text meets WCAG AA contrast in both themes.
- Use the existing Playwright helper patterns (`noHorizontalOverflow`, the `beforeEach` seeding of theme and target).
- Skills (owner-mandated, no others for design):
  - `ui-ux-pro-max` and `design-taste-frontend` before Task 1 (tokens, type scale) and Task 6;
  - `emil-design-eng` before Tasks 3–5 (motion curves and durations);
  - `impeccable` in Task 6.

  `scroll-site-generator` is followed through its code-native chapter path (no Higgsfield calls).
- Commits: the project owner commits only on request, so each "Checkpoint" step commits only if the owner approved
  commits for this run. Otherwise leave the changes uncommitted.

## Review Focus

1. **Switching company while partway down the story:** the chapters re-render with the new target's numbers and the
   page doesn't jump to the top. Pinned in Task 4.
2. **API down on `/how-it-works`:** the existing `ErrorState` shows, and the opening and CTA still render. Pinned in
   Task 3.
3. **Insufficient-data target (Google) in §4/§5:** the insufficient state shows, with no S_comp and no gap bars.
   Pinned in Task 5.
4. **Dark theme on the story:** the toggle persists across story ↔ dashboard navigation (same `prepline-theme` key).
   Pinned in Task 2/3.
5. **Deep link or reload on `/how-it-works`:** works with the Vite dev server's history fallback and lands on the story.
   Pinned in Task 3.

---

## File structure

| File | Responsibility |
|---|---|
| `src/index.css` | Tokens (paper/ink values), `--font-display`, reduced-motion rules |
| `src/components/ThemeToggle.tsx` (new) | `useTheme()` + `<ThemeToggle compact?>`, moved out of `Layout.tsx` and shared by Layout and the story header |
| `src/components/Layout.tsx` | Serif wordmark, "How it works" nav entry, restyle |
| `src/components/ui.tsx` | `PageHeader` (display face, optional `eyebrow`), lighter `Card`, restyled chips. Same props and test ids |
| `src/story/data.ts` (new) | Pure derivations: `courseCodes`, `topicBreakdown`, `evidenceRows` |
| `src/story/useChapterProgress.ts` (new) | Scroll progress 0→1 for one chapter, plus a reduced-motion flag |
| `src/story/Chapter.tsx` (new) | Tall section + sticky stage, or plain flow under reduced motion; numbered heading |
| `src/story/HowItWorks.tsx` (new) | Route page: header, data loading, opening, chapters, hand-off CTA |
| `src/story/chapters/{Syllabus,Taxonomy,Evidence,Scoring,Gaps}.tsx` (new) | One visual scene each |
| `src/App.tsx` | Lazy `/how-it-works` route outside `Layout` |
| `src/pages/*.tsx` | Styling-only adjustments to use the new primitives |
| `tests/story.spec.ts` (new) | Story behaviour and data fidelity |
| `tests/design.spec.ts` (new) | Design-system assertions (display font, nav entry, eyebrows) |

---

### Task 1: Dependencies, tokens and display font

**Files:**
- Modify: `package.json` (via npm), `src/index.css`
- Test: `tests/design.spec.ts`

**Interfaces:**
- Produces: the CSS variable `--font-display` and the Tailwind utility `font-display`. Token names are unchanged.

- [ ] **Step 1: Write the failing test** in `tests/design.spec.ts` (use the same `beforeEach` seeding as `dashboard.spec.ts`).

```ts
test("page titles use the Newsreader display face", async ({ page }) => {
  await page.goto("/");
  const family = await page.getByRole("heading", { level: 1 }).evaluate((el) => getComputedStyle(el).fontFamily);
  expect(family).toContain("Newsreader");
});
```

- [ ] **Step 2: Run it.** `cd dashboard/web; npx playwright test tests/design.spec.ts` → FAIL (family is Fira Sans).
- [ ] **Step 3: Install the dependencies.** `npm i motion @fontsource-variable/newsreader`. Expect both in `dependencies`.
- [ ] **Step 4: Update `src/index.css`:**
  - Import `@fontsource-variable/newsreader`.
  - Add `--font-display: "Newsreader Variable", Georgia, serif;` to `@theme`.
  - Light values: `--bg #f7f5f0`, `--surface #fdfcf9`, `--surface-2 #efece4`, `--ink #17171c`, `--ink-2 #4a4a55`,
    `--ink-3 #63636e`, `--line #e2ddd2`, `--primary #23408e`, `--primary-soft #e4e8f4`, `--track #ebe7de`.
  - Dark values: `--bg #0e0f13`, `--surface #15171c`, `--surface-2 #1d2027`, `--ink #ecebe6`, `--ink-2 #b9b8b1`,
    `--ink-3 #8f8e88`, `--line #2a2c33`, `--primary #a9bcff`, `--primary-soft #1c2440`, `--track #23262d`.
  - Keep `--series`, `warn`, `good` and `bad`, adjusting them only if the contrast check in Task 6 fails.
  - Add `h1, .font-display { font-family: var(--font-display); }`.
- [ ] **Step 5: Run the test and the existing suites.** `npx playwright test tests/design.spec.ts tests/dashboard.spec.ts tests/worst-case.spec.ts tests/study-report.spec.ts` → all PASS.
- [ ] **Step 6: Checkpoint.** Commit `package.json`, `package-lock.json`, `src/index.css` and `tests/design.spec.ts` with the message "Dashboard design tokens: paper/ink palette and Newsreader display face".

### Task 2: Shared theme toggle, Layout restyle and nav entry

**Files:**
- Create: `src/components/ThemeToggle.tsx`
- Modify: `src/components/Layout.tsx`, `src/components/ui.tsx`
- Test: `tests/design.spec.ts`

**Interfaces:**
- Produces:
  - `useTheme(): readonly [boolean, (dark: boolean) => void]` (logic moved verbatim from `Layout.tsx`, same
    `prepline-theme` key);
  - `ThemeToggle({ compact?: boolean })` (keeps `data-testid="theme-toggle"` and the aria-labels);
  - `PageHeader({ title, lede?, actions?, eyebrow?: string })`, where the eyebrow renders with
    `data-testid="page-eyebrow"`.

- [ ] **Step 1: Write the failing tests:**

```ts
test("sidebar has a How it works entry before Overview", async ({ page }) => {
  await page.goto("/");
  const links = page.getByRole("navigation", { name: "Pages" }).getByRole("link");
  await expect(links.first()).toHaveText(/How it works/);
  await expect(links.first()).toHaveAttribute("href", "/how-it-works");
});
test("theme persists from dashboard to story", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("theme-toggle").click();
  await page.goto("/how-it-works");
  await expect(page.locator("html")).toHaveClass(/dark/);
});
```

- [ ] **Step 2: Run** `npx playwright test tests/design.spec.ts` → the nav test FAILS. The theme test needs Task 3's route, so mark it `test.fixme` until Task 3.
- [ ] **Step 3: Implement.**
  - Move `useTheme` into `ThemeToggle.tsx`.
  - In `Layout.tsx`, add the NAV item `{ to: "/how-it-works", label: "How it works", icon: Sparkles }` first, visually
    separated from the six pages by a hairline.
  - Use a serif wordmark (`font-display`) and keep the subtitle.
  - Restyle the active state as an ink-blue left rule plus ink text, not a filled pill.
  - In `ui.tsx`: `Card` gets a hairline border and a refined title row (same props). `PageHeader` renders the optional
    `eyebrow` as a small-caps label above the serif `h1`. Keep every chip's text and test id.
- [ ] **Step 4: Run** `npx playwright test tests/design.spec.ts tests/dashboard.spec.ts` → PASS (except the fixme test).
- [ ] **Step 5: Checkpoint:** commit "Dashboard layout: shared theme toggle, serif wordmark, How it works nav entry".

### Task 3: Story shell: route, chapter mechanics, opening and hand-off

**Files:**
- Create: `src/story/useChapterProgress.ts`, `src/story/Chapter.tsx`, `src/story/HowItWorks.tsx`
- Modify: `src/App.tsx`, `tests/design.spec.ts` (remove the fixme)
- Test: `tests/story.spec.ts`

**Interfaces:**
- Consumes: `useTheme`/`ThemeToggle` (Task 2), `TargetSelect`, `useApi`, `ErrorState`.
- Produces:
  - `useChapterProgress(ref: RefObject<HTMLElement | null>): { progress: MotionValue<number>; reduced: boolean }`.
    It uses `useScroll({ target: ref, offset: ["start start", "end end"] })` and `useReducedMotion()`. When reduced, it
    returns a constant `motionValue(1)`.
  - `Chapter({ index: number; id: string; title: string; lede: ReactNode; facts?: ReactNode; children: (progress: MotionValue<number>, reduced: boolean) => ReactNode })`.
    It renders `<section id={id} data-testid={"chapter-" + id}>` with "§ 0{index}" and an `h2`. Height:
    `h-[240vh] max-[900px]:h-[160vh]` with an inner `sticky top-0 h-screen` stage (`data-testid="chapter-stage"`).
    When reduced, it uses normal flow with no `sticky` class.
  - `StoryData = { results: ResultsResponse; comparison: ComparisonRow[] }`, which `HowItWorks` loads and passes to each
    chapter scene as the `data` prop.

- [ ] **Step 1: Write the failing tests** in `tests/story.spec.ts` (same seeding `beforeEach` and `noHorizontalOverflow` helper as `dashboard.spec.ts`):

```ts
test("story renders opening, five chapters and hands off to the dashboard", async ({ page }) => {
  await page.goto("/how-it-works");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  for (const id of ["syllabus", "taxonomy", "evidence", "scoring", "gaps"])
    await expect(page.getByTestId(`chapter-${id}`)).toBeAttached();
  await page.getByRole("link", { name: "Open the dashboard" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("s-comp")).toBeVisible();
});
test("reduced motion: no pinned stages", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/how-it-works");
  await expect(page.getByTestId("chapter-syllabus")).toBeAttached();
  expect(await page.locator('[data-testid="chapter-stage"].sticky').count()).toBe(0);
});
test("story fits 360px without horizontal scroll", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/how-it-works");
  await noHorizontalOverflow(page);
});
test("story shows the API error state and still offers the dashboard", async ({ page }) => {
  await page.route("**/api/v1/**", (r) => r.abort());
  await page.goto("/how-it-works");
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open the dashboard" })).toBeVisible();
});
test("deep link reload lands on the story", async ({ page }) => {
  await page.goto("/how-it-works");
  await page.reload();
  await expect(page.getByTestId("chapter-syllabus")).toBeAttached();
});
```

- [ ] **Step 2: Run** `npx playwright test tests/story.spec.ts` → FAIL (no route).
- [ ] **Step 3: Implement the hook, `Chapter` and `HowItWorks`.**
  - The header holds the serif wordmark linking to `/`, `TargetSelect`, `ThemeToggle compact` and a "Dashboard →" link.
  - Opening: an `h1` "Does the syllabus prepare you for the interview?", a one-line lede, and a scroll cue that is
    hidden under reduced motion.
  - Chapters 1–5 render with their titles, and their scenes return `null` until Tasks 4–5. Under an API error, the
    chapters are replaced by `ErrorState`, while the opening and hand-off stay.
  - Closing hand-off section: a serif line, a primary link "Open the dashboard" → `/`, and secondary links to
    `/confidence` and `/methodology`.
  - In `App.tsx`, add `const HowItWorks = lazy(() => import("./story/HowItWorks"))` as a sibling
    `<Route path="how-it-works" element={page(HowItWorks)} />` outside the `Layout` route.
  - Remove the Task 2 `test.fixme`.
- [ ] **Step 4: Run** `npx playwright test tests/story.spec.ts tests/design.spec.ts` → PASS.
- [ ] **Step 5: Run** `npm run build` → succeeds, with `motion` absent from the entry chunk. The check `grep -c "useScroll\|useReducedMotion" dist/assets/index-*.js` must report 0 for the entry file.
- [ ] **Step 6: Checkpoint:** commit "How it works: route, pinned chapter mechanics, opening and hand-off".

### Task 4: Chapters §1–§3: syllabus, taxonomy, interview evidence

**Files:**
- Create: `src/story/data.ts`, `src/story/chapters/Syllabus.tsx`, `src/story/chapters/Taxonomy.tsx`, `src/story/chapters/Evidence.tsx`
- Modify: `src/story/HowItWorks.tsx`
- Test: `tests/story.spec.ts`

**Interfaces:**
- Consumes: `StoryData`, `Chapter`, `useChapterProgress` (Task 3), `domainName` (`lib/format.ts`), `GateChip`.
- Produces (in `data.ts`):
  - `courseCodes(files: string[]): string[]`: unique matches of `/^(B[A-Z]{3}\d{3}[A-Z])/` on each basename, sorted
    (real data: 28 files → 26 codes).
  - `topicBreakdown(topics: Topic[]): { total: number; byDomain: { domain: string; name: string; count: number }[]; highLevel: number; granular: number }`:
    the order is by count descending, then by domain id.
  - `evidenceRows(rows: ComparisonRow[]): { id: string; label: string; raw: number; usable: number | null; min: number; passed: boolean }[]`.
- Visible-fact test ids: `story-file-count`, `story-course-count`, `story-topic-count`, `story-high-level`, `story-granular`, `evidence-row-<target_id>` (text includes the raw and usable counts).

- [ ] **Step 1: Write the failing tests.** Compare against the API, not literals. Read `backend/dashboard.py::get_comparison` for the response key holding the rows, and use it in place of `ROWS_KEY`.

```ts
test("§1–§3 show the API's numbers", async ({ page, request }) => {
  const res = await (await request.get("http://127.0.0.1:8000/api/v1/results/amazon_sde1")).json();
  const cmp = await (await request.get("http://127.0.0.1:8000/api/v1/comparison")).json();
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-file-count")).toHaveText(String(res.result.syllabus_files.length));
  await expect(page.getByTestId("story-course-count")).toHaveText("26");
  await expect(page.getByTestId("story-topic-count")).toHaveText(String(res.topics.length));
  const hl = res.topics.filter((t: { type: string }) => t.type === "high_level_concept").length;
  await expect(page.getByTestId("story-high-level")).toHaveText(String(hl));
  await expect(page.getByTestId("story-granular")).toHaveText(String(res.topics.length - hl));
  for (const row of cmp.ROWS_KEY) {
    const el = page.getByTestId(`evidence-row-${row.target_id}`);
    await expect(el).toContainText(String(row.raw_report_count));
    if (row.report_count !== null) await expect(el).toContainText(String(row.report_count));
  }
});
test("switching company mid-story updates numbers without jumping to top", async ({ page }) => {
  await page.goto("/how-it-works");
  await page.getByTestId("chapter-evidence").scrollIntoViewIfNeeded();
  const before = await page.evaluate(() => scrollY);
  await page.getByTestId("target-select").getByRole("radio", { name: /Microsoft/ }).click();
  await expect(page.getByTestId("target-select").getByRole("radio", { name: /Microsoft/ })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByTestId("story-topic-count")).toHaveText("83");
  expect(Math.abs((await page.evaluate(() => scrollY)) - before)).toBeLessThan(50);
});
```

  The header containing `TargetSelect` must stay reachable at the scrolled position: make it `sticky top-0`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement `data.ts` and the three scenes.**
  - **Syllabus:** the course codes as small mono index cards spread on an arc. Driven by `progress` (`useTransform`),
    they translate and stack into one column labelled "One combined syllabus".
  - **Taxonomy:** one dot per topic, starting in a deterministic scattered grid. The dots move into five domain
    clusters (labels with counts), then separate into an inner ring of high-level concepts and an outer ring of granular
    skills.
  - **Evidence:** one row per target, with one tick per collected report. Ticks beyond `usable` fade to 30 % opacity. A
    dashed gate line sits at `min`, and each row has a `GateChip`.
  - Keep the previous target's data rendered while the new target loads, so the layout height never collapses (this
    pins the no-jump test).
  - Visual SVGs are `aria-hidden`; the facts are visible text with the test ids above. Under reduced motion, each scene
    renders its end state.
- [ ] **Step 4: Run** `npx playwright test tests/story.spec.ts` → PASS.
- [ ] **Step 5: Checkpoint:** commit "How it works §1–§3: syllabus, taxonomy and interview-evidence scenes from live data".

### Task 5: Chapters §4–§5: alignment and scoring, gaps and next steps

**Files:**
- Create: `src/story/chapters/Scoring.tsx`, `src/story/chapters/Gaps.tsx`
- Modify: `src/story/HowItWorks.tsx`
- Test: `tests/story.spec.ts`

**Interfaces:**
- Consumes: `StoryData`, `Chapter`, `confidenceOf`, `ConfidenceBadge`, `ProvisionalChip`, `InsufficientState`, `GapBars`, `Tex`.
- Visible-fact test ids: `story-s-comp` (S_comp `toFixed(1)`, as on the Overview), `story-universe`, `story-gaps` (wraps `GapBars`, so its inner `gap-list` exists), `story-limitations`.

- [ ] **Step 1: Write the failing tests:**

```ts
test("§4–§5 show S_comp, gaps and confidence from the API", async ({ page, request }) => {
  const res = await (await request.get("http://127.0.0.1:8000/api/v1/results/amazon_sde1")).json();
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-s-comp")).toHaveText(res.result.S_comp.toFixed(1));
  await expect(page.getByTestId("story-universe")).toHaveText(String(res.result.scoring_universe_size));
  await expect(page.getByTestId("story-gaps").getByTestId("gap-list").locator("li"))
    .toHaveCount(Math.min(5, res.result.top_priority_gaps.length));
  await expect(page.getByTestId("chapter-gaps").getByTestId("confidence-badge")).toContainText("Medium confidence");
  await expect(page.getByTestId("chapter-gaps").getByTestId("provisional")).toHaveText("Provisional");
  await expect(page.getByTestId("story-limitations")).toBeVisible();
});
test("insufficient-data target shows no score in the story", async ({ page }) => {
  await page.goto("/how-it-works");
  await page.getByTestId("target-select").getByRole("radio", { name: /Google/ }).click();
  await expect(page.getByTestId("chapter-scoring").getByTestId("insufficient-state")).toBeVisible();
  await expect(page.getByTestId("story-s-comp")).toHaveCount(0);
  await expect(page.getByTestId("story-gaps")).toHaveCount(0);
});
test("reduced motion shows final S_comp immediately", async ({ page, request }) => {
  const res = await (await request.get("http://127.0.0.1:8000/api/v1/results/amazon_sde1")).json();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-s-comp")).toHaveText(res.result.S_comp.toFixed(1));
});
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement both scenes.**
  - **Scoring:** a three-column connector scene (syllabus | topics | interviews) whose SVG paths draw in via
    `pathLength` from `progress`, plus a coverage arc.
    - The count-up animates only an `aria-hidden` display number.
    - The `story-s-comp` element always holds the exact final `toFixed(1)` value, so tests and screen readers never see
      intermediate numbers.
    - Show the composite formula with `Tex block`, and τ and γ from `result.scoring_config`.
    - For an insufficient-data target, render `InsufficientState` in place of the number and arc.
  - **Gaps:** `GapBars gaps={top_priority_gaps} limit={5}` inside `story-gaps`, the confidence badge with its reasons,
    `ProvisionalChip`, and a limitations note (`story-limitations`) linking to `/confidence`.
    - Add a line pointing to "What to study next" on the Overview.
    - Insufficient data: show `InsufficientState` and no `story-gaps`.
- [ ] **Step 4: Run** `npx playwright test tests/story.spec.ts` → PASS.
- [ ] **Step 5: Checkpoint:** commit "How it works §4–§5: scoring and gaps scenes with confidence and limitations".

### Task 6: Restyle the six pages and do the critique pass

**Files:**
- Modify: `src/pages/{Overview,Compare,Topics,Confidence,Benchmark,Methodology}.tsx`, `src/components/{GapBars,TargetSelect,StudyNext,MappingLimitations,ValidationCard,PilotCard}.tsx` (styling only)
- Test: the existing suites plus `tests/design.spec.ts`

- [ ] **Step 1: Write the failing test:**

```ts
test("every page has a section eyebrow above its serif title", async ({ page }) => {
  for (const path of ["/", "/compare", "/topics", "/confidence", "/benchmark", "/methodology"]) {
    await page.goto(path);
    await expect(page.getByTestId("page-eyebrow")).toBeVisible();
  }
});
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Restyle the pages.**
  - Pass `eyebrow` to each `PageHeader`: "Dashboard · 01" through "Dashboard · 06" in nav order.
  - Score numerals stay sans and tabular.
  - Where a `Card` only wraps a single table, lighten it to a hairline-ruled section.
  - `TargetSelect` uses an ink-blue active segment.
  - Make no copy, order or test-id changes.
- [ ] **Step 4: Critique pass.** Run the `impeccable` skill's critique on the six pages and the story, in both themes,
  at 1366×768 and 360 px. Fix findings that stay within the global constraints. Check every text token pair against
  WCAG AA, and adjust `warn`/`good`/`bad` if needed.
- [ ] **Step 5: Run** `npx playwright test tests/dashboard.spec.ts tests/worst-case.spec.ts tests/study-report.spec.ts tests/design.spec.ts tests/story.spec.ts` → all PASS. `npm run lint` → 0 errors. `npm run build` → succeeds.
- [ ] **Step 6: Checkpoint:** commit "Dashboard pages: editorial restyle and critique fixes".

### Task 7: Full verification and documentation

**Files:**
- Modify: `CLAUDE.md`, `dashboard/README.md` (Pages table gains the story row), `dashboard/screenshots/*` (refreshed by the test run)

- [ ] **Step 1: Run the full checks.**
  - `python -m pytest evaluation -q` → all pass (backend untouched).
  - `cd dashboard/web; npm run lint; npm run build; npx playwright test` → all pass.
  - Record the counts.
- [ ] **Step 2: Manual browser pass** on the real servers:
  - every route in both themes;
  - company switching on the Overview and the story;
  - Topic explorer search, domain filter and sort;
  - chart tooltips;
  - study links;
  - the PDF download returning `application/pdf`;
  - 768 px and 360 px widths;
  - a full scroll through the story with and without reduced motion.

  Fix any regression, then re-run Step 1.
- [ ] **Step 3: Update `CLAUDE.md`:** add a "Dashboard UI" section covering:
  - the editorial design system (tokens, display face);
  - the story route and its live-data-only rule;
  - the Motion lazy-load rule;
  - the reduced-motion behaviour;
  - the final test results with counts and date.
- [ ] **Step 4: Checkpoint:** commit "Dashboard redesign: docs, screenshots and verification results".
