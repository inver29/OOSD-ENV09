import { test, expect, type Page } from "@playwright/test";

async function login(page: Page, username: string) {
  await page.goto("/");
  await page.getByLabel("Tên đăng nhập", { exact: true }).fill(username);
  await page
    .getByLabel("Mật khẩu", { exact: true })
    .fill(process.env.DEMO_PASSWORD!);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.locator("h1")).toContainText("Chào");
}

test("Ảnh hiện ngay, quản lý thêm tự duyệt, duyệt mượn ẩn tài sản và từ chối phiếu còn lại", async ({
  page,
  browser,
}) => {
  const name = "Máy chiếu kiểm thử một lượt mượn";
  await login(page, "ql.hn");
  await page.goto("/owned");
  await page
    .getByRole("button", { name: "Đăng ký tài sản", exact: true })
    .click();
  const form = page.getByRole("dialog", {
    name: "Đăng ký tài sản",
    exact: true,
  });
  await expect(
    form.getByLabel("Người phụ trách", { exact: true }),
  ).toHaveAttribute("readonly", "");
  const currentUser = (await (await page.request.get("/api/auth/me")).json())
    .user;
  await expect(form.getByLabel("Người phụ trách", { exact: true })).toHaveValue(
    currentUser.name,
  );
  await form.getByLabel("Tên tài sản *").fill(name);
  await form
    .getByLabel("Loại tài sản *")
    .selectOption({ label: "Thiết bị trình chiếu" });
  await form.getByLabel("Địa điểm *").selectOption({ label: "Kho thiết bị" });
  await form
    .getByLabel("Tình trạng hiện tại *")
    .fill("Tốt, đủ phụ kiện và dây nguồn.");
  await form.locator('input[type="file"]').setInputFiles({
    name: "tai-san.png",
    mimeType: "image/png",
    buffer: Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGMUj3nKgA0wYRUdtBIAEFkBaJkr7HsAAAAASUVORK5CYII=",
      "base64",
    ),
  });
  await expect(form.getByAltText("Ảnh đã chọn")).toBeVisible();
  await expect
    .poll(() =>
      form
        .getByAltText("Ảnh đã chọn")
        .evaluate((n) => (n as HTMLImageElement).naturalWidth),
    )
    .toBeGreaterThan(0);
  await form
    .getByRole("button", { name: "Xem tệp đã đính kèm", exact: true })
    .click();
  const viewer = page.getByRole("dialog", { name: "Xem ảnh", exact: true });
  await expect(viewer).toBeVisible();
  await expect(viewer.locator("img")).toBeVisible();
  expect(page.context().pages()).toHaveLength(1);
  await page.keyboard.press("Escape");
  await expect(viewer).toHaveCount(0);
  await expect(form).toBeVisible();
  await expect(form.getByLabel("Tên tài sản *")).toHaveValue(name);
  expect(await page.evaluate(() => document.body.style.overflow)).toBe(
    "hidden",
  );
  await form.getByRole("button", { name: "Thêm", exact: true }).click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Đang chia sẻ");
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe(
    "hidden",
  );
  const assetId = page.url().split("/").pop();
  const firstContext = await browser.newContext(),
    secondContext = await browser.newContext();
  const first = await firstContext.newPage(),
    second = await secondContext.newPage();
  await login(first, "an");
  await login(second, "binh");
  async function book(member: Page) {
    await member.goto(`/assets/${assetId}`);
    await member
      .getByRole("button", { name: "Đặt mượn tài sản", exact: true })
      .click();
    await member
      .getByLabel("Mục đích sử dụng *")
      .fill("Dùng cho buổi đào tạo nhân viên tại chi nhánh.");
    await member
      .getByRole("button", { name: "Gửi yêu cầu", exact: true })
      .click();
    await expect(
      member.getByRole("heading", { name: "Thông tin yêu cầu", exact: true }),
    ).toBeVisible();
    return member.url();
  }
  const firstUrl = await book(first),
    secondUrl = await book(second);
  await page.goto(firstUrl);
  await page.getByRole("button", { name: "Duyệt", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Duyệt", exact: true })
    .click();
  await expect(
    page.locator(".badge").filter({ hasText: "Chờ bàn giao" }).first(),
  ).toBeVisible();
  await expect(page.locator(".loan-progress .done")).toHaveCount(2);
  await page.goto("/review?status=CHO_BAN_GIAO");
  await expect(page.locator(".status-tabs .active")).toHaveText("Chờ bàn giao");
  await expect(
    page.getByLabel("Lọc trạng thái").locator("option:checked"),
  ).toHaveText("Chờ bàn giao");
  await expect(
    page.getByRole("row").filter({ hasText: name }).locator(".badge"),
  ).toHaveText("Chờ bàn giao");
  await page.screenshot({
    path: "test-results/status-waiting-handover.png",
    fullPage: true,
  });
  await page.getByLabel("Lọc trạng thái").selectOption("CHO_DUYET");
  await expect(page).toHaveURL(/status=CHO_DUYET/);
  await expect(page.locator(".status-tabs .active")).toHaveText("Chờ duyệt");
  await page.getByRole("button", { name: "Chờ bàn giao", exact: true }).click();
  await expect(page).toHaveURL(/status=CHO_BAN_GIAO/);
  await expect(
    page.getByLabel("Lọc trạng thái").locator("option:checked"),
  ).toHaveText("Chờ bàn giao");
  await second.goto(secondUrl);
  await expect(
    second.locator(".badge").filter({ hasText: "Từ chối" }).first(),
  ).toBeVisible();
  await expect(
    second.getByText("Đã có người khác mượn tài sản này", { exact: true }),
  ).toBeVisible();
  await page.goto(`/owned/${assetId}`);
  await expect(page.locator(".page-heading .badge")).toHaveText("Chờ bàn giao");
  await first.goto("/assets");
  await first.getByLabel("Tìm tài sản", { exact: true }).fill(name);
  await expect(
    first.getByText("Chưa có tài sản phù hợp với bộ lọc.", { exact: true }),
  ).toBeVisible();
  await first.goto(firstUrl);
  await first.getByRole("button", { name: "Hủy phiếu", exact: true }).click();
  await first.getByLabel("Lý do *").fill("Đổi kế hoạch đào tạo tại đơn vị.");
  await first
    .getByRole("dialog")
    .getByRole("button", { name: "Hủy phiếu", exact: true })
    .click();
  await expect(
    first.locator(".badge").filter({ hasText: "Đã hủy" }).first(),
  ).toBeVisible();
  await expect(first.locator(".loan-progress .done")).toHaveCount(2);
  await first.goto("/assets");
  await first.getByLabel("Tìm tài sản", { exact: true }).fill(name);
  await expect(first.locator(".asset-card")).toHaveCount(1);
  await page.goto(`/owned/${assetId}`);
  await expect(page.locator(".page-heading .badge")).toHaveText("Đang chia sẻ");
  await second.goto(secondUrl);
  await expect(
    second.locator(".badge").filter({ hasText: "Từ chối" }).first(),
  ).toBeVisible();
  await firstContext.close();
  await secondContext.close();
});
