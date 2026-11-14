import { test, expect, type Page } from "@playwright/test";
const password = process.env.DEMO_PASSWORD!;
async function login(page: Page, username: string, entry = "/") {
  await page.goto(entry);
  await page.getByLabel("Tên đăng nhập", { exact: true }).fill(username);
  await page.getByLabel("Mật khẩu", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: username === "admin" ? "Tài khoản & cấu hình" : /Chào /,
    }),
  ).toBeVisible();
}

test("Đăng nhập vào đúng trang vai trò và menu được thu gọn", async ({
  page,
  browser,
}) => {
  await login(page, "an", "/assets/1");
  await expect(page).toHaveURL(/:\d+\/$/);
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(4);
  const context = await browser.newContext(),
    admin = await context.newPage();
  await login(admin, "admin", "/loans/1");
  await expect(admin).toHaveURL(/\/admin$/);
  await admin.goto("/assets");
  await expect(admin).toHaveURL(/\/admin$/);
  await expect(admin.getByRole("navigation").getByRole("link")).toHaveCount(1);
  await admin.screenshot({
    path: "test-results/admin-desktop.png",
    fullPage: true,
  });
  await context.close();
});

test("Đặt mượn và ghi nhu cầu cùng lần gửi, xét duyệt nhanh từ danh sách", async ({
  page,
  browser,
}) => {
  await login(page, "an");
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "Khám phá tài sản", exact: true })
    .click();
  await page
    .getByRole("link")
    .filter({
      has: page.getByRole("heading", { name: "Máy chiếu Epson EB-X49" }),
    })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByLabel("Mục đích sử dụng *")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Đặt mượn tài sản", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Đặt mượn tài sản", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Mục đích sử dụng *")
    .fill("Phục vụ buổi chia sẻ kiến thức nội bộ.");
  await expect(
    page.getByLabel("Ghi nhận nhu cầu sử dụng", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Nếu không mượn được, đơn vị sẽ…").locator("option"),
  ).toHaveText(["Mua mới", "Hoãn nhu cầu sử dụng"]);
  await expect(page.getByLabel("Nếu không mượn được, đơn vị sẽ…")).toHaveValue(
    "MUA_MOI",
  );
  await expect(
    page.getByRole("dialog").locator('input[type="file"]'),
  ).toHaveCount(0);
  await page
    .getByLabel("Nếu không mượn được, đơn vị sẽ…")
    .selectOption("MUA_MOI");
  await page.screenshot({ path: "test-results/booking-popup.png" });
  await page.getByRole("button", { name: "Gửi yêu cầu", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Thông tin yêu cầu" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Nhu cầu & kết quả sử dụng" }),
  ).toHaveCount(0);
  const loanId = page.url().split("/").pop();
  const context = await browser.newContext(),
    manager = await context.newPage();
  await login(manager, "ql.hn");
  await manager
    .getByRole("navigation")
    .getByRole("link", { name: "Xử lý mượn–trả", exact: true })
    .click();
  await expect(manager.getByRole("navigation").getByRole("link")).toHaveCount(
    6,
  );
  await manager.getByRole("button", { name: "Chờ duyệt", exact: true }).click();
  const row = manager.getByRole("row").filter({
    has: manager.getByRole("link", {
      name: `Xem phiếu ${loanId}`,
      exact: true,
    }),
  });
  await row.getByRole("button", { name: "Xét duyệt", exact: true }).click();
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Duyệt", exact: true })
    .click();
  await expect(manager.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  await expect(
    page.locator(".badge").filter({ hasText: "Chờ bàn giao" }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Hủy phiếu", exact: true }).click();
  await page
    .getByLabel("Lý do *")
    .fill("Buổi chia sẻ được đổi sang lịch khác.");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Hủy phiếu", exact: true })
    .click();
  await expect(
    page.locator(".badge").filter({ hasText: "Đã hủy" }).first(),
  ).toBeVisible();
  await page.goto("/loans?tab=needs");
  await expect(
    page.getByRole("button", { name: "Ghi nhận nhu cầu", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", {
      name: "Phục vụ buổi chia sẻ kiến thức nội bộ.",
      exact: true,
    }),
  ).toHaveCount(0);
  await context.close();
});

test("Bàn giao và trả hư hỏng mỗi bên một lần xác nhận", async ({
  page,
  browser,
}) => {
  await login(page, "ql.hn");
  await page.getByRole("link", { name: "Xử lý mượn–trả", exact: true }).click();
  await page
    .getByRole("link", { name: "Màn hình Dell 24 inch", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Bàn giao tài sản", exact: true })
    .click();
  await page
    .getByLabel("Nội dung kiểm tra / Phụ kiện *")
    .fill("Màn hình hoạt động tốt, đủ dây nguồn và dây HDMI.");
  let releaseUpload!: () => void;
  const uploadGate = new Promise<void>((resolve) => {
    releaseUpload = resolve;
  });
  await page.route("**/api/files", async (route) => {
    await uploadGate;
    await route.continue();
  });
  await page
    .getByRole("dialog")
    .locator('input[type="file"]')
    .setInputFiles({
      name: "hien-trang.png",
      mimeType: "image/png",
      buffer: Buffer.from(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAFElEQVR4nGMUj3nKgA0wYRUdtBIAEFkBaJkr7HsAAAAASUVORK5CYII=",
        "base64",
      ),
    });
  await expect(
    page.getByRole("button", { name: "Xác nhận bàn giao", exact: true }),
  ).toBeDisabled();
  releaseUpload();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Xem tệp đã đính kèm", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Xác nhận bàn giao", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator(".signature-grid .signed")).toHaveCount(1);
  const currentUrl = page.url();
  await page
    .getByRole("button", { name: "Xem ảnh / Chứng từ", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Xem ảnh", exact: true }).locator("img"),
  ).toBeVisible();
  expect(page.context().pages()).toHaveLength(1);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(page.url()).toBe(currentUrl);
  const context = await browser.newContext(),
    member = await context.newPage();
  await login(member, "an");
  await member.goto(page.url());
  await member
    .getByRole("button", { name: "Đã nhận tài sản", exact: true })
    .click();
  await expect(
    member.locator(".badge").filter({ hasText: "Đang mượn" }).first(),
  ).toBeVisible();
  await expect(member.getByRole("dialog")).toHaveCount(0);
  await member
    .getByRole("button", { name: "Trả tài sản", exact: true })
    .click();
  await member.getByLabel("Tình trạng hiện vật *").selectOption("Hư hỏng");
  await member
    .getByLabel("Nội dung kiểm tra / Phụ kiện *")
    .fill("Màn hình có vệt sọc, cần kiểm tra bộ phận hiển thị.");
  await member
    .getByRole("button", { name: "Xác nhận trả tài sản", exact: true })
    .click();
  await expect(member.getByRole("dialog")).toHaveCount(0);
  await expect(
    member.locator(".badge").filter({ hasText: "Chờ xác nhận trả" }).first(),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: "Xác nhận đã nhận trả", exact: true })
    .click();
  await expect(
    page.locator(".badge").filter({ hasText: "Đã hoàn trả" }).first(),
  ).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.screenshot({
    path: "test-results/loan-return-desktop.png",
    fullPage: true,
  });
  await member.reload();
  await expect(
    member.locator(".badge").filter({ hasText: "Đã hoàn trả" }).first(),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Xem hồ sơ tài sản", exact: true })
    .click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Bảo trì");
  await page
    .getByRole("button", { name: "Xử lý & đánh giá vòng đời", exact: true })
    .click();
  await page
    .getByLabel("Nội dung *", { exact: true })
    .fill("Đã thay bộ phận hiển thị và kiểm tra hoạt động.");
  await expect(page.getByLabel("Căn cứ đánh giá *")).toHaveCount(0);
  await page
    .getByLabel("Tình trạng sau kiểm tra")
    .fill("Tốt, màn hình hiển thị bình thường.");
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Đang chia sẻ");
  await context.close();
});

test("Quản trị thêm, sửa, xóa danh mục và cấp tài khoản", async ({ page }) => {
  await login(page, "admin");
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("navigation").getByRole("link")).toHaveCount(1);
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await expect(page.locator("tbody")).not.toContainText("@");
  await expect(
    page.getByRole("navigation").getByText("Tổng quan", { exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("link", { name: "Quản trị hệ thống", exact: true })
    .click();
  await page.getByRole("button", { name: "Loại tài sản", exact: true }).click();
  await page
    .getByRole("button", { name: "Thêm loại tài sản", exact: true })
    .click();
  await page
    .getByLabel("Tên *", { exact: true })
    .fill("Thiết bị thử nghiệm giao diện");
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await expect(
    page.getByText("Thiết bị thử nghiệm giao diện", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: "Sửa Thiết bị thử nghiệm giao diện",
      exact: true,
    })
    .click();
  await page
    .getByLabel("Tên *", { exact: true })
    .fill("Thiết bị thử nghiệm đã đổi tên");
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await page
    .getByRole("button", {
      name: "Xóa Thiết bị thử nghiệm đã đổi tên",
      exact: true,
    })
    .click();
  await page.getByRole("button", { name: "Xóa mục này", exact: true }).click();
  await expect(
    page.getByText("Thiết bị thử nghiệm đã đổi tên", { exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Tài khoản", exact: true }).click();
  await page
    .getByRole("button", { name: "Tạo tài khoản", exact: true })
    .click();
  await page.getByLabel("Họ tên *").fill("Tài khoản trình duyệt");
  await page.getByLabel("Tên đăng nhập *").fill("ui.member");
  await page.getByLabel("Email *").fill("ui.member@env09.example");
  await page
    .getByLabel("Đơn vị *")
    .selectOption({ label: "Chi nhánh Đà Nẵng" });
  await page.getByLabel("Mật khẩu *", { exact: true }).fill("UiMember!123");
  const role = page.getByRole("combobox", { name: "Vai trò *", exact: true });
  await expect(role).toHaveValue("THANH_VIEN");
  await role.selectOption("QUAN_LY");
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await expect(
    page
      .getByRole("row")
      .filter({ hasText: "ui.member" })
      .locator(".role-chips"),
  ).toHaveText("Quản lý tài sản");
  await page.getByRole("button", { name: "Đơn vị", exact: true }).click();
  await page
    .getByRole("button", { name: "Sửa Chi nhánh Hà Nội", exact: true })
    .click();
  await page.getByLabel("Địa chỉ cụ thể *").fill("120 Trần Duy Hưng, Hà Nội");
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "120 Trần Duy Hưng, Hà Nội", exact: true }),
  ).toBeVisible();
});

test("Kết quả nằm ngay trên phiếu và quản lý xác minh trong Hiệu quả sử dụng", async ({
  page,
  browser,
}) => {
  await login(page, "chi");
  await page.goto("/needs/1");
  await expect(
    page.getByRole("button", { name: "Xem căn cứ nhu cầu", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Xem căn cứ xác minh", exact: true }),
  ).toHaveCount(0);
  await page.locator(".table-title").first().click();
  await expect(
    page.getByRole("heading", { name: "Nhu cầu & kết quả sử dụng" }),
  ).toBeVisible();
  await page
    .getByLabel("Đơn vị có mua mới cho nhu cầu này không?")
    .selectOption("true");
  await page.getByRole("button", { name: "Lưu kết quả", exact: true }).click();
  await expect(
    page.locator(".badge").filter({ hasText: "Chờ xác minh" }),
  ).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const context = await browser.newContext(),
    manager = await context.newPage();
  await login(manager, "ql.hn");
  await manager
    .getByRole("link", { name: "Hiệu quả sử dụng", exact: true })
    .click();
  await expect(
    manager.getByRole("heading", { name: "Xác minh nhu cầu", exact: true }),
  ).toBeVisible();
  await manager
    .getByRole("link", {
      name: "Trang bị máy tính cho đợt đào tạo số 1.",
      exact: true,
    })
    .click();
  await manager
    .getByRole("button", { name: "Xác minh kết quả", exact: true })
    .click();
  await expect(
    manager.getByLabel("Việc mượn đã đáp ứng mục đích sử dụng"),
  ).not.toBeChecked();
  await manager.getByLabel("Xác nhận dự định mua mới ban đầu").check();
  await manager.getByLabel("Việc mượn đã đáp ứng mục đích sử dụng").check();
  await manager
    .getByLabel("Kết luận đối chiếu *")
    .fill("Đã đối chiếu kết quả sử dụng. Đơn vị vẫn mua mới.");
  await manager
    .getByRole("dialog")
    .getByRole("button", { name: "Xác nhận", exact: true })
    .click();
  await expect(manager.locator(".page-heading .badge")).toHaveText(
    "Đã xác minh",
  );
  await manager
    .getByRole("link", { name: "Danh sách nhu cầu", exact: true })
    .click();
  await manager
    .getByRole("button", { name: "Chỉ số tránh mua mới", exact: true })
    .click();
  await expect(manager.locator("h1")).toHaveText("Chỉ số tránh mua mới");
  await expect(manager.getByRole("alert")).toHaveCount(0);
  await manager.screenshot({
    path: "test-results/effectiveness-desktop.png",
    fullPage: true,
  });
  await context.close();
});
test("Trang quản lý và điện thoại hiển thị đủ nội dung, không tràn ngang", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page, "ql.hn");
  for (const route of [
    "/",
    "/assets",
    "/owned",
    "/review",
    "/verification",
    "/indicator",
    "/assets/1",
    "/loans/1",
  ]) {
    await page.goto(route);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator(".spin")).toHaveCount(0);
    await expect(page.locator(".error-box")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.goto("/");
  await page.screenshot({
    path: "test-results/dashboard-desktop.png",
    fullPage: true,
  });
  await page.goto("/assets");
  await expect(page.locator(".asset-card").first()).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator(".asset-card img")
        .evaluateAll(
          (images) =>
            images.length > 0 &&
            images.every(
              (i) =>
                (i as HTMLImageElement).complete &&
                (i as HTMLImageElement).naturalWidth > 0,
            ),
        ),
    )
    .toBeTruthy();
  await page.screenshot({
    path: "test-results/catalog-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of [
    "/",
    "/assets",
    "/owned",
    "/review",
    "/indicator",
    "/loans/1",
  ]) {
    await page.goto(route);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator(".spin")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  await page.goto("/assets");
  await expect(page.locator(".asset-card").first()).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator(".asset-card img")
        .evaluateAll(
          (images) =>
            images.length > 0 &&
            images.every(
              (i) =>
                (i as HTMLImageElement).complete &&
                (i as HTMLImageElement).naturalWidth > 0,
            ),
        ),
    )
    .toBeTruthy();
  await page.screenshot({
    path: "test-results/catalog-mobile.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("Tìm kiếm, dropdown và lọc ngày tự cập nhật không cần bấm Tìm", async ({
  page,
  browser,
}) => {
  await login(page, "an");
  await page.goto("/assets");
  await expect(page.locator(".asset-card").first()).toBeVisible();
  await expect(page.getByRole("button", { name: /^Tìm( kiếm)?$/ })).toHaveCount(
    0,
  );
  await page.getByLabel("Tìm tài sản", { exact: true }).fill("Epson");
  await expect(page.locator(".asset-card")).toHaveCount(1);
  await expect(page.locator(".asset-card h2")).toHaveText(
    "Máy chiếu Epson EB-X49",
  );
  await page.getByLabel("Tìm tài sản", { exact: true }).fill("");
  await expect
    .poll(() => page.locator(".asset-card").count())
    .toBeGreaterThan(1);
  await page
    .getByLabel("Lọc đơn vị")
    .selectOption({ label: "Chi nhánh Hà Nội" });
  await expect
    .poll(() => page.locator(".asset-card-footer").allTextContents())
    .toEqual(expect.arrayContaining([expect.stringContaining("Hà Nội")]));
  await expect
    .poll(async () => {
      const names = await page.locator(".asset-card-footer").allTextContents();
      return names.length > 0 && names.every((n) => n.includes("Hà Nội"));
    })
    .toBeTruthy();
  await page
    .getByRole("button", { name: "Lọc theo lịch", exact: true })
    .click();
  const local = (d: Date) =>
    new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  const from = local(new Date(Date.now() + 10 * 86400000)),
    until = local(new Date(Date.now() + 11 * 86400000));
  const calendarResponse = page.waitForResponse((r) => {
    const u = new URL(r.url());
    return (
      u.pathname === "/api/assets" &&
      !!u.searchParams.get("start") &&
      !!u.searchParams.get("end")
    );
  });
  await page.getByLabel("Lọc lịch từ").fill(from);
  await page.getByLabel("Lọc lịch đến").fill(until);
  expect((await calendarResponse).status()).toBe(200);
  await expect(
    page.getByRole("button", { name: "Tìm lịch trống", exact: true }),
  ).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);

  await page.goto("/loans");
  await page.getByLabel("Tìm phiếu mượn", { exact: true }).fill("Epson");
  await page.getByLabel("Lọc trạng thái").selectOption("TU_CHOI");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("Epson");
  await page.getByLabel("Lọc trạng thái").selectOption("CHO_DUYET");
  await expect(
    page.getByText("Chưa có phiếu mượn phù hợp.", { exact: true }),
  ).toBeVisible();
  await page.goto("/loans?tab=needs");
  await page.getByLabel("Tìm nhu cầu", { exact: true }).fill("zzzz-khong-co");
  await expect(
    page.getByText("Chưa có nhu cầu phù hợp.", { exact: true }),
  ).toBeVisible();
  const needContext = await browser.newContext(),
    needsPage = await needContext.newPage();
  await login(needsPage, "chi");
  await needsPage.goto("/loans?tab=needs");
  await needsPage
    .getByLabel("Tìm nhu cầu", { exact: true })
    .fill("đào tạo số 1");
  await expect(needsPage.locator("tbody tr")).toHaveCount(1);
  await needsPage.getByLabel("Trạng thái nhu cầu").selectOption("TU_CHOI");
  await expect(
    needsPage.getByText("Chưa có nhu cầu phù hợp.", { exact: true }),
  ).toBeVisible();
  await needContext.close();

  const context = await browser.newContext({
      timezoneId: "America/Los_Angeles",
    }),
    manager = await context.newPage();
  await login(manager, "ql.hn");
  await manager.goto("/effectiveness?tab=indicator");
  const response = manager.waitForResponse((r) => {
    const u = new URL(r.url());
    return (
      u.pathname === "/api/reports/avoidance" &&
      !!u.searchParams.get("category_id")
    );
  });
  await manager
    .getByLabel("Loại tài sản", { exact: true })
    .selectOption({ label: "Thiết bị văn phòng" });
  expect((await response).status()).toBe(200);
  await expect(
    manager.getByRole("button", { name: "Xem kết quả", exact: true }),
  ).toHaveCount(0);
  const dateResponse = manager.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/api/reports/avoidance" &&
      new URL(r.url()).searchParams.get("start") ===
        "2020-01-01T00:00:00+07:00",
  );
  await manager.getByLabel("Từ ngày", { exact: true }).fill("2020-01-01");
  expect((await dateResponse).status()).toBe(200);
  await expect(manager.getByRole("alert")).toHaveCount(0);
  await context.close();
});

test("Quá hạn là cảnh báo đi kèm bước chờ xác nhận trả và tiến độ không bị mất", async ({
  page,
}) => {
  await login(page, "ql.hn");
  await page.goto("/review?status=OVERDUE");
  const row = page.getByRole("row").filter({
    has: page.getByRole("link", { name: "Xem phiếu 4", exact: true }),
  });
  await expect(row.locator(".badge")).toHaveText([
    "Chờ xác nhận trả",
    "Quá hạn trả",
  ]);
  await row.getByRole("link", { name: "Xem phiếu 4", exact: true }).click();
  await expect(
    page.locator(".detail-main > .detail-panel").first().locator(".badge"),
  ).toHaveText(["Chờ xác nhận trả", "Quá hạn trả"]);
  await expect(page.locator(".loan-progress strong")).toHaveText([
    "Chờ duyệt",
    "Chờ bàn giao",
    "Đang mượn",
    "Chờ xác nhận trả",
    "Đã hoàn trả",
  ]);
  await expect(page.locator(".loan-progress .done")).toHaveCount(4);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "test-results/status-overdue-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
  await page.goto("/loans/1");
  await expect(
    page.locator(".badge").filter({ hasText: "Từ chối" }).first(),
  ).toBeVisible();
  await expect(page.locator(".loan-progress .done")).toHaveCount(1);
});
