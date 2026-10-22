import { expect, test, type Page, type Route } from "@playwright/test";

// break-ui: realistic worst-case data injected at the API boundary (route mocks), never by editing markup.
const SHOTS = "../screenshots/worst-case";

const LONG_COMPANY = "Hindustan Aeronautics Limited (HAL)";
const LONG_ROLE = "Software Development Engineer I (Backend Platform)";

const targets = [
  { id: "hal", company: LONG_COMPANY, role: LONG_ROLE, results_available: true, status: "SUCCESS", S_comp: 100 },
  { id: "one", company: "Zoho", role: "MTS", results_available: true, status: "INSUFFICIENT_DATA", S_comp: null },
  { id: "zero", company: "Tata Consultancy Services", role: "Ninja", results_available: true, status: "SUCCESS", S_comp: 0 },
  { id: "a", company: "Atlassian", role: "Graduate Software Engineer", results_available: true, status: "SUCCESS", S_comp: 77.5 },
  { id: "b", company: "Goldman Sachs", role: "Analyst, Engineering", results_available: false, status: null, S_comp: null },
  { id: "c", company: "Juspay", role: "SDE", results_available: true, status: "SUCCESS", S_comp: 64.1 },
];

const result = (over: Record<string, unknown>) => ({
  status: "SUCCESS",
  S_comp: 100,
  report_count: 1284,
  taxonomy_version: "v1.0",
  scoring_config_version: "v1.2",
  scoring_config: { gamma: 0.5, similarity_threshold: 0.5 },
  generated_at: "2026-10-22T09:00:00+00:00",
  syllabus_id: "VIT_CSE_2024_25_courses_with_a_very_long_syllabus_identifier_v2",
  syllabus_files: Array.from({ length: 27 }, (_, i) => `f${i}.pdf`),
  interview_filter: { questions_total: 12840, questions_included: 9999, questions_excluded: 2841 },
  scoring_universe_size: 1,
  topics_present: 83,
  topics_in_taxonomy: 83,
  depth_counts: { all_topics: { measured: 83 }, present_topics: { measured: 83 } },
  top_priority_gaps: [],
  unmapped_terms_summary: { distinct_terms: 123456, total_occurrences: 999999, distinct_terms_by_source_type: { syllabus: 123000, interview: 456 } },
  top_unmapped_terms: [
    { term: "load-balancer-health-check-with-exponential-backoff-and-jitter", source_type: "interview", occurrences: 1 },
  ],
  ...over,
});

async function mockApi(page: Page) {
  await page.route("**/api/v1/targets", (r: Route) => r.fulfill({ json: { targets } }));
  await page.route("**/api/v1/results/hal", (r: Route) =>
    r.fulfill({ json: { target: { id: "hal", company: LONG_COMPANY, role: LONG_ROLE }, result: result({}), raw_report_count: 1284, min_reports: 15, topics: [] } }),
  );
  await page.route("**/api/v1/results/one", (r: Route) =>
    r.fulfill({ json: { target: { id: "one", company: "Zoho", role: "MTS" }, result: { ...result({ status: "INSUFFICIENT_DATA", S_comp: null, report_count: 1 }), top_priority_gaps: undefined, scoring_universe_size: undefined, depth_counts: undefined, unmapped_terms_summary: undefined, top_unmapped_terms: undefined }, raw_report_count: 1, min_reports: 15, topics: [] } }),
  );
  await page.route("**/api/v1/comparison", (r: Route) =>
    r.fulfill({
      json: {
        min_reports: 15,
        targets: targets.map((t, i) => ({
          target_id: t.id, company: t.company, role: t.role, results_available: t.results_available, status: t.status,
          S_comp: t.S_comp, raw_report_count: i === 0 ? 1284 : 1, report_count: t.status === "SUCCESS" ? 1284 : t.results_available ? 1 : null,
          min_reports: 15, density_gate_passed: t.status === "SUCCESS", scoring_universe_size: 1, fallback_topics: 0,
          topics_in_taxonomy: 83, unmapped_distinct_terms: 123456,
          top_priority_gaps: i === 3 ? [{ rank: 1, topic_id: "system_design.load_balancing.algorithms", topic_name: "Load Balancing Algorithms & Consistent Hashing", importance: 1, coverage: 0, priority_gap: 1 }] : [],
          generated_at: null,
        })),
      },
    }),
  );
}

async function noHorizontalOverflow(page: Page) {
  const offenders = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    if (document.documentElement.scrollWidth <= vw) return [];
    return [...document.querySelectorAll("body *")]
      .filter((el) => el.getBoundingClientRect().right > vw + 1)
      .slice(0, 3)
      .map((el) => `${el.tagName}.${(el.getAttribute("class") ?? "").slice(0, 60)} "${(el.textContent ?? "").slice(0, 40)}"`);
  });
  expect(offenders, `elements past the viewport on ${page.url()}`).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("prepline-theme", "light");
    localStorage.setItem("prepline-target", "hal");
  });
  await mockApi(page);
});

test("overview: long names, huge counts, S_comp 100, no gaps, no topic table", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("s-comp")).toContainText("100.0");
  await expect(page.getByTestId("data-card")).toContainText("1284 → 1284");
  await expect(page.getByTestId("gaps-card")).toContainText("No priority gaps");
  await expect(page.getByTestId("domain-card")).toContainText("No topic table");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/overview.png`, fullPage: true });
});

test("overview: one usable report reads in the singular", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("target-select").getByRole("radio", { name: /Zoho/ }).click();
  await expect(page.getByTestId("insufficient-state")).toContainText("1 usable interview report (1 collected)");
});

test("compare: six targets, missing results, empty and single gaps", async ({ page }) => {
  await page.goto("/compare");
  await expect(page.getByTestId("compare-hal")).toContainText(LONG_ROLE);
  await expect(page.getByTestId("compare-zero")).toContainText("0.0");
  await expect(page.getByTestId("compare-b")).toContainText("No saved results");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/compare.png`, fullPage: true });
});

test("topic explorer: empty topic table explains itself", async ({ page }) => {
  await page.goto("/topics");
  await expect(page.getByText("No topic table has been exported for this target")).toBeVisible();
  await expect(page.getByText(/No topics match/)).toHaveCount(0);
});

test("320px-wide window keeps the page inside the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  for (const path of ["/", "/compare", "/topics"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await noHorizontalOverflow(page);
  }
});
