import { expect, test, type Page } from "@playwright/test";

const SHOTS = "../screenshots";

async function noHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function selectTarget(page: Page, label: RegExp) {
  await page.getByTestId("target-select").getByRole("radio", { name: label }).click();
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem("seeded")) {
      localStorage.setItem("prepline-theme", "light");
      localStorage.setItem("prepline-target", "amazon_sde1");
      sessionStorage.setItem("seeded", "1");
    }
  });
});

test("overview: S_comp, confidence badge, data card, gaps and domain coverage", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("s-comp")).toContainText("88.8");
  await expect(page.getByTestId("confidence-badge")).toContainText("Medium confidence");
  await expect(page.getByTestId("data-card")).toContainText("21 → 18");
  await expect(page.getByTestId("data-card")).toContainText("Gate passed · 18/15");
  await expect(page.getByTestId("gap-list").locator("li")).toHaveCount(9);
  await expect(page.getByTestId("domain-card").locator(".recharts-bar-rectangle")).toHaveCount(5);
  await expect(page.getByTestId("disclaimer")).toContainText("not a hiring guarantee");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/1-overview.png` });
});

test("overview: Google shows an insufficient-data state, not an error", async ({ page }) => {
  await page.goto("/");
  await selectTarget(page, /Google/);
  await expect(page.getByTestId("insufficient-state")).toContainText("8 usable interview reports (16 collected)");
  await expect(page.getByTestId("s-comp")).toHaveText("n/a");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByTestId("gaps-card")).toContainText("below the density gate");
  await page.screenshot({ path: `${SHOTS}/1b-overview-google-insufficient.png` });
});

test("compare: four targets side by side, Google insufficient", async ({ page }) => {
  await page.goto("/compare");
  for (const id of ["amazon_sde1", "microsoft_sde1", "google_swe_l3", "flipkart_sde1"]) {
    await expect(page.getByTestId(`compare-${id}`)).toBeVisible();
  }
  await expect(page.getByTestId("compare-flipkart_sde1")).toContainText("89.7");
  await expect(page.getByTestId("compare-google_swe_l3").getByTestId("insufficient-state")).toBeVisible();
  await expect(page.getByTestId("compare-google_swe_l3")).toContainText("Gate not met · 8/15");
  await expect(page.getByTestId("compare-amazon_sde1").getByTestId("gap-list").locator("li")).toHaveCount(5);
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/2-compare.png` });
});

test("topic explorer: search, domain filter and columns", async ({ page }) => {
  await page.goto("/topics");
  await expect(page.getByTestId("topic-count")).toHaveText("83 of 83 topics");
  for (const header of ["Topic", "Domain", "Importance", "Coverage", "Depth D(t)", "Depth status", "Coverage source"]) {
    await expect(page.getByRole("columnheader", { name: header, exact: true })).toBeVisible();
  }
  await expect(page.getByRole("cell", { name: /inherited/ }).first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/3-topic-explorer.png` });
  await page.getByTestId("topic-search").fill("sql");
  await expect(page.getByTestId("topic-count")).toHaveText(/^\d+ of 83 topics$/);
  await expect(page.getByRole("cell", { name: /SQL Joins/ })).toBeVisible();
  await page.getByTestId("topic-search").fill("zzzz");
  await expect(page.getByText("No topics match")).toBeVisible();
  await page.getByTestId("topic-search").fill("");
  await page.getByLabel("Domain").selectOption("os");
  await expect(page.getByTestId("topic-count")).toHaveText("14 of 83 topics");
  await noHorizontalOverflow(page);
});

test("topic explorer: Google has no importance but still shows coverage", async ({ page }) => {
  await page.goto("/topics");
  await selectTarget(page, /Google/);
  await expect(page.getByText("Importance and priority gap are not computed for Google SWE-L3")).toBeVisible();
  await expect(page.getByTestId("topic-count")).toHaveText("83 of 83 topics");
});

test("confidence: three indicators with live counts", async ({ page }) => {
  await page.goto("/confidence");
  await expect(page.getByTestId("indicator-gate")).toContainText("Gate not met · 8/15");
  await expect(page.getByTestId("fallback-coverage")).toHaveText("42.9%");
  await expect(page.getByTestId("indicator-fallback")).toContainText("3 of 83 topics");
  await expect(page.getByTestId("unmapped-list").locator("li")).toHaveCount(10);
  await expect(page.getByTestId("indicator-unmapped")).toContainText("1305 distinct terms");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/4-confidence.png` });
});

test("benchmark: method table, kappa, F1 chart, limitations", async ({ page }) => {
  await page.goto("/benchmark");
  await expect(page.getByTestId("method-table").locator("tbody tr")).toHaveCount(4);
  await expect(page.getByTestId("method-table")).toContainText("0.213");
  await expect(page.getByTestId("kappa")).toHaveText("0.812");
  await expect(page.getByTestId("f1-chart").locator(".recharts-bar-rectangle")).toHaveCount(4);
  await expect(page.getByTestId("recommendation")).toContainText("Keep the production matcher");
  await expect(page.getByTestId("limitations").locator("li")).toHaveCount(6);
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/5-benchmark.png` });
});

test("methodology: KaTeX formulas, pipeline and versioning", async ({ page }) => {
  await page.goto("/methodology");
  await expect(page.getByTestId("formulas").locator(".katex-display")).toHaveCount(5);
  await expect(page.getByTestId("pipeline")).toContainText("S_comp + priority gaps");
  await expect(page.getByTestId("versioning")).toContainText("MIN_REPORTS = 15");
  await noHorizontalOverflow(page);
  await page.screenshot({ path: `${SHOTS}/6-methodology.png` });
});

test("dark theme toggles and persists", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("theme-toggle").click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.getByTestId("s-comp")).toContainText("88.8");
  await page.screenshot({ path: `${SHOTS}/7-overview-dark.png` });
  await page.reload();
  await expect(page.locator("html")).toHaveClass(/dark/);
});

test("navigation reaches every page from the sidebar", async ({ page }) => {
  await page.goto("/");
  for (const [label, heading] of [
    ["Compare", "Compare"],
    ["Topic explorer", "Topic explorer"],
    ["Confidence", "Confidence"],
    ["Benchmark", "Benchmark"],
    ["Methodology", "Methodology"],
    ["Overview", "Overview"],
  ]) {
    await page.getByRole("navigation", { name: "Pages" }).getByRole("link", { name: label }).click();
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  }
});

test("API down shows a clear error state", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Could not load data from the API");
});

test("reduced motion: pages render fully without movement", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByTestId("s-comp")).toContainText("88.8");
  const transition = await page.locator(".bar-grow").first().evaluate((el) => getComputedStyle(el).transitionDuration);
  expect(transition).toBe("0s");
});
