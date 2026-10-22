# PREPLINE dashboard (Phase 15)

A read-only dashboard over the saved PREPLINE results: how well the VIT CSE 2024-25 core syllabus covers the topics
four companies ask about in interviews. Topic alignment is diagnostic, not a hiring guarantee.

## Start it

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_demo.ps1
```

This opens two windows (API on http://127.0.0.1:8000, dashboard on http://localhost:5173) and the dashboard in the
browser. First run installs the npm packages. Needs Python with `requirements.txt` installed and Node.js 20+.
`-NoBrowser` skips opening the browser; `-Python <path>` picks another interpreter.

Manual start:

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000      # repo root
cd dashboard/web; npm install; npx vite --port 5173                  # second terminal
```

## Pages

| Page | Shows |
|---|---|
| Overview | Company/role selector, provisional S_comp with a confidence badge, known mapping limitations, data card (reports collected → usable, density gate, taxonomy/config versions, date), ranked priority gaps, coverage by domain |
| Compare | All targets side by side with provisional scores and a note that scoring universes differ; Google SWE-L3 shows an insufficient-data state (8 of 15 reports) instead of a score |
| Topic explorer | All 83 topics: domain, importance, coverage, depth, measured/fallback, coverage source (direct/inherited); search, domain filter, sorting |
| Confidence | The three indicators with live counts: insufficient data, fallback depth (a present topic at D = 1 counts 42.9 % covered with γ = 0.5), unmapped terms |
| Benchmark | Matcher table (thresholds from dev, test macro-F1), test-F1 chart, label agreement (κ = 0.812), limitations |
| Methodology | Formulas (KaTeX), pipeline diagram, versioning |

Light and dark themes (sidebar toggle, remembered per browser). Laid out for a 1366×768 laptop or projector; it also
reflows down to phone width.

## Data

The dashboard only reads saved files through the API; it never runs the pipeline.

| Endpoint | Source |
|---|---|
| `GET /api/v1/targets` | `config/targets.json` + each target's results file |
| `GET /api/v1/results/{target_id}` | `results/<id>_v1.2_course_syllabi.json` + `results/topics/<id>_v1.2_topics.json` |
| `GET /api/v1/comparison` | the same results files, one summary row per target |
| `GET /api/v1/benchmark` | `results/benchmark/benchmark_v1.0.json` (without per-item predictions) |

Paths are set in `config/api.json` (`dashboard`); only configured target ids are served. The browser origin
`http://localhost:5173` is in the CORS allowlist there. Topic tables come from `python evaluation/export_topic_tables.py`,
which recomputes coverage and importance from the same inputs and refuses to write if S_comp differs from the saved
result (it matched for every scored target). A new target appears after `run_all_targets.py` and the export.

## Tests and screenshots

```powershell
cd dashboard/web
npx playwright install chromium   # once
npx playwright test               # starts or reuses both servers
```

`tests/dashboard.spec.ts` covers every page, the Google insufficient state, navigation, the theme toggle, the API-down
error and reduced motion; `tests/worst-case.spec.ts` feeds realistic worst-case data through route mocks (long names,
1,284 reports, one report, S_comp 0 and 100, no gaps, missing results and topic tables, 360 px width). Each run saves
page screenshots to `dashboard/screenshots/` (worst-case ones in `screenshots/worst-case/`). The backend endpoints are
tested in `evaluation/test_dashboard_api.py`.

## Stack and design

Vite, React 19, TypeScript, Tailwind CSS v4, Recharts, KaTeX, lucide icons, Fira Sans/Fira Code bundled locally (works
offline). Design tokens live in `web/src/index.css` (light and dark, contrast-checked to WCAG AA for text). Motion is
limited to transform/opacity CSS transitions (button press, page fade, gap bars) and is removed under
`prefers-reduced-motion`; charts do not animate.
