import { defineConfig } from "@playwright/test";
if (!process.env.DEMO_PASSWORD) {
  throw new Error("Set DEMO_PASSWORD to the password used to seed the test database.");
}

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 10000 },
  reporter: "list",
  use: {
    baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8001",
    channel: "msedge",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
