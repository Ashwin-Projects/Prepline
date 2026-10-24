import { expect, test } from "@playwright/test";

// Design-system checks: display face, navigation entry and page eyebrows.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem("seeded")) {
      localStorage.setItem("prepline-theme", "light");
      localStorage.setItem("prepline-target", "amazon_sde1");
      sessionStorage.setItem("seeded", "1");
    }
  });
});

test("page titles use the Newsreader display face", async ({ page }) => {
  await page.goto("/");
  const family = await page.getByRole("heading", { level: 1 }).evaluate((el) => getComputedStyle(el).fontFamily);
  expect(family).toContain("Newsreader");
});

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

test("every page has a section eyebrow above its serif title", async ({ page }) => {
  for (const path of ["/", "/compare", "/topics", "/confidence", "/benchmark", "/methodology"]) {
    await page.goto(path);
    await expect(page.getByTestId("page-eyebrow")).toBeVisible();
  }
});

test("confidence: company names in the gate list are not truncated at 1366px", async ({ page }) => {
  await page.goto("/confidence");
  const names = page.getByTestId("indicator-gate").locator("li > span:first-child");
  await expect(names).toHaveCount(4);
  const clipped = await names.evaluateAll((els) => els.filter((el) => el.scrollWidth > el.clientWidth).map((el) => el.textContent));
  expect(clipped).toEqual([]);
});
