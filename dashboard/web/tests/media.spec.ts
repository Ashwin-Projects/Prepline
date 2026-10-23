import { expect, test, type Page } from "@playwright/test";

// Pilot media (docs/pilot/img/*.png and docs/pilot/demo.webm). Not part of the regular suite:
//   $env:MEDIA = "1"; npx playwright test tests/media.spec.ts
test.skip(!process.env.MEDIA, "media capture runs only with MEDIA=1");
test.describe.configure({ timeout: 180_000 });

const IMG = "../../docs/pilot/img";

interface Note {
  testId: string;
  text: string;
}

// Numbered markers on the page plus a legend banner at the top of <main>, so each screenshot explains itself.
async function annotate(page: Page, title: string, notes: Note[]) {
  await page.evaluate(
    ({ title, notes }) => {
      const css = "position:absolute;z-index:50;display:flex;align-items:center;justify-content:center;width:26px;height:26px;"
        + "border-radius:999px;background:#c2410c;color:#fff;font:600 13px/1 system-ui;box-shadow:0 1px 3px rgba(0,0,0,.35)";
      const main = document.querySelector("main")!;
      const legend = document.createElement("div");
      legend.style.cssText = "margin:0 0 16px;padding:12px 14px;border:2px solid #c2410c;border-radius:8px;background:#fff7ed;"
        + "color:#431407;font:13px/1.45 system-ui";
      legend.innerHTML = `<p style="font-weight:600;font-size:14px;margin:0 0 6px">${title}</p>`
        + notes.map((n, i) => `<p style="margin:2px 0"><b style="color:#c2410c">${i + 1}</b>&nbsp; ${n.text}</p>`).join("");
      main.prepend(legend);
      notes.forEach((n, i) => {
        const el = document.querySelector(`[data-testid="${n.testId}"]`) as HTMLElement | null;
        if (!el) throw new Error(`no element ${n.testId}`);
        const r = el.getBoundingClientRect();
        const marker = document.createElement("div");
        marker.textContent = String(i + 1);
        marker.style.cssText = `${css};left:${r.left + window.scrollX - 10}px;top:${r.top + window.scrollY - 10}px`;
        document.body.appendChild(marker);
        el.style.outline = "2px solid #c2410c";
        el.style.outlineOffset = "3px";
      });
    },
    { title, notes },
  );
}

async function seed(page: Page, target: string) {
  await page.addInitScript((t) => {
    localStorage.setItem("prepline-theme", "light");
    localStorage.setItem("prepline-target", t);
  }, target);
  await page.emulateMedia({ reducedMotion: "reduce" });
}

for (const [target, company] of [["amazon_sde1", "Amazon"], ["microsoft_sde1", "Microsoft"], ["flipkart_sde1", "Flipkart"]]) {
  test(`annotated overview: ${company}`, async ({ page }) => {
    await seed(page, target);
    await page.goto("/");
    await expect(page.getByTestId("study-item").first()).toBeVisible();
    await annotate(page, `PREPLINE Overview — ${company} SDE-1 (for pilot Q2)`, [
      { testId: "score-card", text: "Provisional alignment score S_comp with its confidence badge; not a ranking across companies." },
      { testId: "data-card", text: "Data behind it: interview reports, density gate (15), taxonomy and config versions." },
      { testId: "gaps-card", text: `The top priority gaps — exactly the rows you rate in Q2 for ${company}.` },
      { testId: "study-next", text: "What to study next: VIT modules to revise and two practice pages per gap." },
      { testId: "mapping-limitations", text: "Known matcher errors that affect every score shown." },
    ]);
    await page.screenshot({ path: `${IMG}/overview-${company.toLowerCase()}.png`, fullPage: true });
  });
}

test("annotated compare", async ({ page }) => {
  await seed(page, "amazon_sde1");
  await page.goto("/compare");
  await expect(page.getByTestId("compare-amazon_sde1")).toBeVisible();
  await annotate(page, "PREPLINE Compare — all configured companies side by side", [
    { testId: "compare-amazon_sde1", text: "One column per company: score, report count, density gate, scoring universe and top gaps." },
    { testId: "compare-google_swe_l3", text: "Google is below the 15-report gate, so it has no score and is not in the pilot." },
  ]);
  await page.screenshot({ path: `${IMG}/compare.png`, fullPage: true });
});

test("annotated confidence", async ({ page }) => {
  await seed(page, "microsoft_sde1");
  await page.goto("/confidence");
  await expect(page.getByTestId("indicator-gate")).toBeVisible();
  await annotate(page, "PREPLINE Confidence — how far to trust a company's result (Microsoft SDE-1)", [
    { testId: "indicator-gate", text: "Report margin above the 15-report density gate (Microsoft has 15 usable: no margin)." },
    { testId: "indicator-fallback", text: "Covered topics whose depth fell back to the minimum (no depth signal in the syllabus)." },
    { testId: "indicator-unmapped", text: "Interview terms that matched no taxonomy topic, so they never enter a score." },
  ]);
  await page.screenshot({ path: `${IMG}/confidence.png`, fullPage: true });
});

test("demo walkthrough video", async ({ browser }) => {
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    recordVideo: { dir: "test-results/demo-video", size: { width: 1366, height: 768 } },
  });
  await context.addInitScript(() => {
    localStorage.setItem("prepline-theme", "light");
    localStorage.setItem("prepline-target", "amazon_sde1");
  });
  const page = await context.newPage();
  const pause = (ms: number) => page.waitForTimeout(ms);
  const glide = async (testId: string) => {
    await page.getByTestId(testId).evaluate((el) => el.scrollIntoView({ behavior: "smooth", block: "start" }));
    await pause(2600);
  };
  const t0 = Date.now();

  await page.goto("/");
  await expect(page.getByTestId("s-comp")).toBeVisible();
  await pause(5000);                                  // score, confidence badge, provisional chip
  await glide("gaps-card");                           // priority gaps
  await pause(3000);
  await glide("study-next");                          // what to study next
  await pause(3500);
  await page.getByTestId("study-item").nth(3).scrollIntoViewIfNeeded();
  await pause(3000);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  await pause(1500);
  for (const company of [/Microsoft/, /Flipkart/, /Google/]) {
    await page.getByTestId("target-select").getByRole("radio", { name: company }).click();
    await pause(3500);
  }
  await page.getByTestId("target-select").getByRole("radio", { name: /Amazon/ }).click();
  await pause(1500);
  await page.getByRole("link", { name: "Download report (PDF)" }).hover();
  await pause(2500);
  await page.getByRole("link", { name: "Compare" }).click();
  await pause(6000);
  await page.getByRole("link", { name: "Confidence" }).click();
  await pause(6000);
  await page.getByRole("link", { name: "Topic explorer" }).click();
  await pause(3000);
  await page.getByRole("searchbox").first().fill("tree");
  await pause(4000);
  await page.getByRole("link", { name: "Methodology" }).click();
  await pause(5000);
  await glide("pilot");
  await pause(4000);
  await page.getByRole("link", { name: "Overview" }).click();
  await pause(4000);

  const seconds = (Date.now() - t0) / 1000;
  expect(seconds).toBeGreaterThanOrEqual(60);
  expect(seconds).toBeLessThanOrEqual(90);
  const video = page.video()!;
  await context.close();
  await video.saveAs("../../docs/pilot/demo.webm");
});
