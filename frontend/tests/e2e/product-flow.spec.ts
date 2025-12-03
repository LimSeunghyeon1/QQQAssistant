import { expect, test, type Page } from "@playwright/test";

const uniqueProductUrl = `https://example.com/item/e2e-${Date.now()}`;

async function importProduct(page: Page): Promise<void> {
  await page.goto("/products/import");
  await page.getByLabel("Source URL").fill(uniqueProductUrl);
  await page.getByLabel("Source Site").fill("TAOBAO");
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.getByText("Imported and queued for localization")).toBeVisible();
}

test("import, list, and export products", async ({ page }) => {
  await importProduct(page);

  await page.getByRole("link", { name: "Products" }).click();
  await expect(page.getByText(uniqueProductUrl)).toBeVisible();
  await expect(page.getByText("Dummy Taobao Product")).toBeVisible();

  await page.getByRole("link", { name: "SmartStore Export" }).click();
  const checkbox = page.getByLabel(uniqueProductUrl);
  await checkbox.check();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Export selected" }).click()
  ]);

  expect(download.suggestedFilename()).toContain("smartstore_products");
  const downloadPath = await download.path();
  expect(downloadPath).not.toBeNull();
});
