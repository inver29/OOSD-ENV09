import { test, expect, type Page } from "@playwright/test";

async function login(page: Page, username: string) {
  await page.goto("/");
  await page.getByLabel("Tên đăng nhập", { exact: true }).fill(username);
  await page
    .getByLabel("Mật khẩu", { exact: true })
    .fill(process.env.DEMO_PASSWORD!);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.locator("main h1")).toContainText("Chào");
}

test("Thêm chờ duyệt, từ chối, gửi lại, duyệt và thu hồi qua hai tài khoản", async ({
  page,
  browser,
}) => {
  const name = "Tài sản kiểm thử xét duyệt giao diện";
  await login(page, "an");
  await page.getByRole("link", { name: "Tài sản đơn vị", exact: true }).click();
  await page
    .getByRole("button", { name: "Đăng ký tài sản", exact: true })
    .click();
  await page.getByLabel("Tên tài sản *").fill(name);
  await page
    .getByLabel("Loại tài sản *")
    .selectOption({ label: "Thiết bị văn phòng" });
  await page.getByLabel("Địa điểm *").selectOption({ label: "Kho thiết bị" });
  await page
    .getByLabel("Tình trạng hiện tại *")
    .fill("Tốt, hoạt động bình thường.");
  await expect(
    page.getByRole("button", { name: "Tạo hồ sơ nháp", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Thêm", exact: true }).click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Chờ duyệt");
  await expect(
    page.getByRole("button", { name: "Duyệt tài sản", exact: true }),
  ).toHaveCount(0);
  const assetUrl = page.url();

  const context = await browser.newContext(),
    manager = await context.newPage();
  await login(manager, "ql.hcm");
  await manager.goto(assetUrl);
  await expect(
    manager.getByRole("button", { name: "Sửa hồ sơ", exact: true }),
  ).toHaveCount(0);
  await expect(
    manager.getByRole("button", { name: "Thu hồi tài sản", exact: true }),
  ).toHaveCount(0);
  await manager.getByRole("button", { name: "Từ chối", exact: true }).click();
  await expect(
    manager.getByRole("dialog", { name: "Xác nhận từ chối", exact: true }),
  ).toBeVisible();
  await expect(manager.locator(".page-heading .badge")).toHaveText("Chờ duyệt");
  await manager
    .getByLabel("Lý do từ chối *")
    .fill("Cần ghi rõ các phụ kiện đi kèm.");
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Từ chối", exact: true })
    .click();
  await expect(manager.locator(".page-heading .badge")).toHaveText("Từ chối");
  await page.reload();
  await page.getByRole("button", { name: "Sửa hồ sơ", exact: true }).click();
  await page
    .getByLabel("Đặc tính / Phụ kiện")
    .fill("Có đủ dây nguồn và phụ kiện.");
  await page
    .getByRole("button", { name: "Gửi lại duyệt", exact: true })
    .click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Chờ duyệt");
  await manager.reload();
  await manager.getByRole("button", { name: "Duyệt", exact: true }).click();
  await expect(
    manager.getByRole("dialog", { name: "Xác nhận duyệt", exact: true }),
  ).toBeVisible();
  await manager.screenshot({ path: "test-results/approval-popup.png" });
  await expect(manager.locator(".page-heading .badge")).toHaveText("Chờ duyệt");
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Đóng", exact: true })
    .click();
  await expect(manager.locator(".page-heading .badge")).toHaveText("Chờ duyệt");
  await manager.goto("/owned");
  await manager
    .locator(".asset-card")
    .filter({ has: manager.getByRole("heading", { name, exact: true }) })
    .getByRole("button", { name: "Xét duyệt tài sản", exact: true })
    .click();
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Từ chối", exact: true })
    .click();
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Đóng", exact: true })
    .click();
  await expect(manager.getByRole("dialog")).toHaveCount(0);
  await manager
    .locator(".asset-card")
    .filter({ has: manager.getByRole("heading", { name, exact: true }) })
    .getByRole("button", { name: "Xét duyệt tài sản", exact: true })
    .click();
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Duyệt", exact: true })
    .click();
  await expect(manager.getByRole("dialog")).toHaveCount(0);
  await manager.goto(assetUrl);
  await expect(manager.locator(".page-heading .badge")).toHaveText(
    "Đang chia sẻ",
  );
  await expect(
    manager.getByRole("button", {
      name: "Xử lý & đánh giá vòng đời",
      exact: true,
    }),
  ).toBeVisible();

  await page.reload();
  await page.getByRole("button", { name: "Sửa hồ sơ", exact: true }).click();
  await page
    .getByLabel("Đặc tính / Phụ kiện")
    .fill("Người phụ trách cập nhật hồ sơ đang chia sẻ.");
  await page.getByRole("button", { name: "Lưu hồ sơ", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Thu hồi tài sản", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Thu hồi tài sản", exact: true })
    .click();
  await expect(page).toHaveURL(/\/owned$/);
  await expect(page.locator(".spin")).toHaveCount(0);
  await expect(page.getByRole("heading", { name, exact: true })).toHaveCount(0);
  await manager.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(manager.getByRole("alert")).toContainText(
    "Không tìm thấy tài sản",
  );
  await expect(manager.getByRole("heading", { name, exact: true })).toHaveCount(
    0,
  );
  await expect(
    manager.getByRole("button", {
      name: "Xử lý & đánh giá vòng đời",
      exact: true,
    }),
  ).toHaveCount(0);
  await context.close();
});
