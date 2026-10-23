import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem("seeded")) {
      localStorage.setItem("prepline-theme", "light");
      localStorage.setItem("prepline-target", "amazon_sde1");
      sessionStorage.setItem("seeded", "1");
    }
  });
});

test("overview: what to study next lists modules and two verified practice links per gap", async ({ page }) => {
  await page.goto("/");
  const card = page.getByTestId("study-next");
  await expect(card).toContainText("What to study next");
  const items = card.getByTestId("study-item");
  await expect(items).toHaveCount(9);
  const first = items.first();
  await expect(first).toContainText("Linked List Manipulation & Cycle Detection");
  await expect(first).toContainText("BCSE202L");
  const links = first.getByRole("link");
  await expect(links).toHaveCount(2);
  for (const link of await links.all()) {
    await expect(link).toHaveAttribute("href", /^https:\/\/www\.geeksforgeeks\.org\//);
    await expect(link).toHaveAttribute("target", "_blank");
    await expect(link).toHaveAttribute("rel", /noopener/);
  }
  await expect(card).toContainText("Links checked 2026-10-23");
});

test("overview: a gap outside the core curriculum says so", async ({ page }) => {
  await page.route("**/api/v1/study/amazon_sde1", (r) =>
    r.fulfill({
      json: {
        target: { id: "amazon_sde1", company: "Amazon", role: "SDE-1" }, status: "SUCCESS", links_verified_on: "2026-10-23",
        items: [{
          rank: 1, topic_id: "x.y", topic_name: "Some Topic", coverage: 0, priority_gap: 0.2, in_core_curriculum: false,
          modules: [], note: "Not covered in core curriculum", practice: [],
        }],
      },
    }),
  );
  await page.goto("/");
  await expect(page.getByTestId("study-item")).toHaveCount(1);
  await expect(page.getByTestId("study-item")).toContainText("Not covered in core curriculum");
});

test("overview: download report (PDF) for the selected company", async ({ page }) => {
  await page.goto("/");
  const button = page.getByRole("link", { name: "Download report (PDF)" });
  await expect(button).toHaveAttribute("href", /\/api\/v1\/report\/amazon_sde1$/);
  const [download] = await Promise.all([page.waitForEvent("download"), button.click()]);
  expect(download.suggestedFilename()).toBe("prepline_amazon_sde1_v1.2.pdf");
});

test("overview: Google has no study list but its report still downloads", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("target-select").getByRole("radio", { name: /Google/ }).click();
  await expect(page.getByTestId("study-next")).toContainText("below the density gate");
  await expect(page.getByTestId("study-item")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Download report (PDF)" })).toHaveAttribute("href", /google_swe_l3$/);
});
