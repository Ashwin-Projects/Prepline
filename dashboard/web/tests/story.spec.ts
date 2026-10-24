import { expect, test, type Page } from "@playwright/test";

// "How PREPLINE works" scroll story (/how-it-works): structure, data fidelity against the API, motion fallbacks.

async function noHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
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
  await expect(page.getByTestId("chapter-gaps")).toBeAttached();
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

const API = "http://127.0.0.1:8000/api/v1";

test("§1–§3 show the API's numbers", async ({ page, request }) => {
  const res = await (await request.get(`${API}/results/amazon_sde1`)).json();
  const cmp = await (await request.get(`${API}/comparison`)).json();
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-file-count")).toHaveText(String(res.result.syllabus_files.length));
  await expect(page.getByTestId("story-course-count")).toHaveText("26");
  await expect(page.getByTestId("story-topic-count")).toHaveText(String(res.topics.length));
  const hl = res.topics.filter((t: { type: string }) => t.type === "high_level_concept").length;
  await expect(page.getByTestId("story-high-level")).toHaveText(String(hl));
  await expect(page.getByTestId("story-granular")).toHaveText(String(res.topics.length - hl));
  for (const row of cmp.targets) {
    const el = page.getByTestId(`evidence-row-${row.target_id}`);
    await expect(el).toContainText(String(row.raw_report_count));
    if (row.report_count !== null) await expect(el).toContainText(String(row.report_count));
  }
});

test("switching company mid-story updates numbers without jumping to top", async ({ page }) => {
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-topic-count")).toHaveText("83");
  await page.getByTestId("chapter-evidence").scrollIntoViewIfNeeded();
  const before = await page.evaluate(() => scrollY);
  const microsoft = page.getByTestId("target-select").getByRole("radio", { name: /Microsoft/ });
  await microsoft.click();
  await expect(microsoft).toHaveAttribute("aria-checked", "true");
  await expect(page.getByTestId("story-topic-count")).toHaveText("83");
  expect(Math.abs((await page.evaluate(() => scrollY)) - before)).toBeLessThan(50);
});

test("§4–§5 show S_comp, gaps and confidence from the API", async ({ page, request }) => {
  const res = await (await request.get(`${API}/results/amazon_sde1`)).json();
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-s-comp")).toHaveText(res.result.S_comp.toFixed(1));
  await expect(page.getByTestId("story-universe")).toHaveText(String(res.result.scoring_universe_size));
  await expect(page.getByTestId("story-gaps").getByTestId("gap-list").locator("li")).toHaveCount(
    Math.min(5, res.result.top_priority_gaps.length),
  );
  await expect(page.getByTestId("chapter-gaps").getByTestId("confidence-badge")).toContainText("Medium confidence");
  await expect(page.getByTestId("chapter-gaps").getByTestId("provisional")).toHaveText("Provisional");
  await expect(page.getByTestId("story-limitations")).toBeVisible();
});

test("insufficient-data target shows no score in the story", async ({ page }) => {
  await page.goto("/how-it-works");
  const google = page.getByTestId("target-select").getByRole("radio", { name: /Google/ });
  await google.click();
  await expect(google).toHaveAttribute("aria-checked", "true");
  await expect(page.getByTestId("chapter-scoring").getByTestId("insufficient-state")).toBeVisible();
  await expect(page.getByTestId("story-s-comp")).toHaveCount(0);
  await expect(page.getByTestId("story-gaps")).toHaveCount(0);
});

test("reduced motion shows final S_comp immediately", async ({ page, request }) => {
  const res = await (await request.get(`${API}/results/amazon_sde1`)).json();
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-s-comp")).toHaveText(res.result.S_comp.toFixed(1));
});

// Final review fixes ---------------------------------------------------------------------------------------------

test("phone: a scene is still animating when it first scrolls into view", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 740 });
  await page.goto("/how-it-works");
  const card = page.getByTestId("chapter-syllabus").locator("[data-scene] > div").first();
  await expect(card).toBeAttached();
  // put the scene's top edge 15% above the bottom of the viewport
  await page.evaluate(() => {
    const scene = document.querySelector('[data-testid="chapter-syllabus"] [data-scene]')!;
    scrollTo(0, scene.getBoundingClientRect().top + scrollY - innerHeight * 0.85);
  });
  await page.waitForTimeout(400);
  const angle = await card.evaluate((el) => {
    const m = new DOMMatrix(getComputedStyle(el).transform);
    return Math.abs(Math.atan2(m.b, m.a));
  });
  expect(angle).toBeGreaterThan(0.01); // still rotated: not yet filed into the grid
});

test("company switch shows the new company's numbers", async ({ page, request }) => {
  const ms = await (await request.get(`${API}/results/microsoft_sde1`)).json();
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-topic-count")).toHaveText("83");
  await page.getByTestId("target-select").getByRole("radio", { name: /Microsoft/ }).click();
  await expect(page.getByTestId("story-questions-included")).toHaveText(String(ms.result.interview_filter.questions_included));
  await expect(page.getByTestId("story-s-comp")).toHaveText(ms.result.S_comp.toFixed(1));
  await expect(page.getByTestId("story-universe")).toHaveText(String(ms.result.scoring_universe_size));
});

test("while results load, scenes show skeleton placeholders", async ({ page }) => {
  await page.route("**/api/v1/results/**", async (route) => {
    await new Promise((r) => setTimeout(r, 4000));
    await route.continue();
  });
  await page.goto("/how-it-works");
  await expect(page.getByTestId("chapter-syllabus").getByTestId("scene-skeleton")).toBeAttached();
});

test("short or medium-width screens do not pin chapters under the header", async ({ page }) => {
  for (const [w, h] of [[1024, 600], [960, 800]]) {
    await page.setViewportSize({ width: w, height: h });
    await page.goto("/how-it-works");
    await expect(page.getByTestId("chapter-scoring")).toBeAttached();
    const pinned = await page.locator('[data-testid="chapter-stage"]').evaluateAll((els) =>
      els.filter((el) => getComputedStyle(el).position === "sticky").length,
    );
    const headerSticky = await page.locator("header").first().evaluate((el) => getComputedStyle(el).position === "sticky");
    // pinning is fine only when the sticky header cannot wrap over the stage and the stage fits the viewport
    if (h < 700) expect(pinned).toBe(0);
    if (w < 1000) expect(headerSticky && pinned > 0).toBe(false);
  }
});

// Deferred-review fixes (#1, #2, #3, #5, #6) ---------------------------------------------------------------------

test("header at exactly 700px uses the narrow layout (no breakpoint gap)", async ({ page }) => {
  const widthOf = async (w: number) => {
    await page.setViewportSize({ width: w, height: 800 });
    await page.goto("/how-it-works");
    await expect(page.getByTestId("target-select")).toBeVisible();
    return page.getByTestId("target-select").locator("xpath=..").evaluate((el) => {
      const row = el.parentElement!.getBoundingClientRect().width;
      const pad = parseFloat(getComputedStyle(el.parentElement!).paddingLeft) * 2;
      return Math.round(el.getBoundingClientRect().width - (row - pad));
    });
  };
  expect(await widthOf(699)).toBe(0); // selector wrapper spans the full header row
  expect(await widthOf(700)).toBe(0);
});

test("story scenes do not keep will-change GPU layers at rest", async ({ page }) => {
  await page.goto("/how-it-works");
  await expect(page.getByTestId("story-s-comp")).toBeAttached();
  const layered = await page.locator("main *").evaluateAll((els) =>
    els.filter((el) => getComputedStyle(el).willChange.includes("transform")).length,
  );
  expect(layered).toBe(0);
});

test("§3 states the interview filter as the parser applies it", async ({ page }) => {
  await page.goto("/how-it-works");
  const evidence = page.getByTestId("chapter-evidence");
  await expect(evidence).toContainText("behavioural rounds, rows flagged for review, and rows without question text or a report id");
  await expect(evidence).not.toContainText("link-only");
});

test("reduced motion keeps the scroll hint visible without animation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/how-it-works");
  const cue = page.getByText("Scroll through the five steps");
  await expect(cue).toBeVisible();
  const animation = await cue.locator("svg").evaluate((el) => getComputedStyle(el).animationName);
  expect(animation).toBe("none");
});

test("§4 topic labels: dark text on the unfilled track, white only on the filled part", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" }); // final fill state
  await page.goto("/how-it-works");
  const scene = page.getByTestId("chapter-scoring");
  const base = scene.locator('[data-label-layer="base"]');
  const onFill = scene.locator('[data-label-layer="fill"]');
  await expect(base.first()).toBeAttached();
  expect(await base.count()).toBe(await onFill.count());
  const baseColor = await base.first().evaluate((el) => getComputedStyle(el).color);
  expect(baseColor).not.toBe("rgb(255, 255, 255)");
  const clip = await onFill.first().evaluate((el) => getComputedStyle(el).clipPath);
  expect(clip).toMatch(/inset\(/);
});
