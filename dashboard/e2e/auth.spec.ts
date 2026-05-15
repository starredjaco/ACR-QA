import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("login page loads with ACR-QA title", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "ACR-QA" })).toBeVisible();
  });

  test("shows sign-in form with email and password fields", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("shows error on invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("bad@example.com");
    await page.getByLabel("Password").fill("wrongpass");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("Invalid email or password")).toBeVisible({ timeout: 5000 });
  });

  test("unauthenticated access to / redirects to /login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });

  test("unauthenticated access to /supply-chain redirects to /login", async ({ page }) => {
    await page.goto("/supply-chain");
    await expect(page).toHaveURL(/\/login/);
  });
});
