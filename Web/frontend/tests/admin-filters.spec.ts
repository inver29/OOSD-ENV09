import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Tên đăng nhập", { exact: true }).fill("admin");
  await page
    .getByLabel("Mật khẩu", { exact: true })
    .fill(process.env.DEMO_PASSWORD!);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Tài khoản & cấu hình", exact: true }),
  ).toBeVisible();
}

test("Quản trị tìm không dấu, kết hợp dropdown, đổi tab và cập nhật dữ liệu đang lọc", async ({
  page,
}) => {
  await login(page);
  const session = await (await page.request.get("/api/auth/me")).json();
  const lookup = await (await page.request.get("/api/lookups")).json();
  const unit = lookup.units.find(
    (u: { name: string }) => u.name === "Chi nhánh Hà Nội",
  );
  async function post(path: string, data: unknown) {
    const r = await page.request.post(`/api${path}`, {
      data,
      headers: { "X-CSRF-Token": session.csrf_token },
    });
    expect(r.ok(), await r.text()).toBeTruthy();
    return r.json();
  }
  await post("/admin/users", {
    name: "Tài khoản lọc đã khóa",
    username: "filter.locked",
    email: "filter.locked@env09.example",
    unit_id: unit.id,
    roles: ["THANH_VIEN"],
    active: false,
    password: "FilterTest!2026",
  });
  await post("/admin/catalog/units", {
    name: "Đơn vị lọc thử",
    address: "99 Đường Nội Bộ, Hà Nội",
    active: false,
  });
  const category = await post("/admin/catalog/categories", {
    name: "Loại lọc thử",
    active: false,
  });
  const policy = { max_days: 14, buffer_hours: 2, pickup_hours: 24 };
  await post("/admin/policies", {
    ...policy,
    name: "Chính sách lọc đã thay thế",
    effective_from: new Date(Date.now() - 730 * 86400000).toISOString(),
  });
  await post("/admin/policies", {
    ...policy,
    name: "Chính sách lọc sắp áp dụng",
    effective_from: new Date(Date.now() + 7 * 86400000).toISOString(),
  });
  await page.reload();
  const search = page.getByRole("searchbox", {
    name: "Tìm kiếm quản trị",
    exact: true,
  });
  await search.fill("TAI KHOAN LOC");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("filter.locked");
  await page.getByLabel("Lọc trạng thái quản trị").selectOption("false");
  await page.getByLabel("Lọc đơn vị quản trị").selectOption(String(unit.id));
  await page.getByLabel("Lọc vai trò quản trị").selectOption("THANH_VIEN");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page.getByLabel("Lọc vai trò quản trị").selectOption("QUAN_TRI");
  await expect(
    page.getByText("Không có kết quả phù hợp.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Xóa bộ lọc", exact: true }).click();
  await expect(search).toHaveValue("");
  await expect(page.getByLabel("Lọc vai trò quản trị")).toHaveValue("");
  await page.getByLabel("Lọc vai trò quản trị").selectOption("QUAN_LY");
  await page
    .getByLabel("Lọc đơn vị quản trị")
    .selectOption({ label: "Chi nhánh TP. Hồ Chí Minh" });
  await search.fill("linh");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("ql.hcm");
  await page.screenshot({
    path: "test-results/admin-filters-desktop.png",
    animations: "disabled",
  });

  await page.getByRole("button", { name: "Đơn vị", exact: true }).click();
  await expect(search).toHaveValue("");
  await expect(page.getByLabel("Lọc đơn vị quản trị")).toHaveCount(0);
  await search.fill("tran duy hung");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("Chi nhánh Hà Nội");
  await search.fill("");
  await page.getByLabel("Lọc trạng thái quản trị").selectOption("false");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("Đơn vị lọc thử");

  await page.getByRole("button", { name: "Loại tài sản", exact: true }).click();
  await expect(page.getByLabel("Lọc trạng thái quản trị")).toHaveValue("");
  await search.fill("loai loc");
  await page.getByLabel("Lọc trạng thái quản trị").selectOption("false");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page
    .getByRole("button", { name: `Sửa ${category.name}`, exact: true })
    .click();
  await page
    .getByRole("checkbox", { name: "Đang hoạt động", exact: true })
    .check();
  await page.getByRole("button", { name: "Lưu thay đổi", exact: true }).click();
  await expect(
    page.getByText("Không có kết quả phù hợp.", { exact: true }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Địa điểm", exact: true }).click();
  await page
    .getByLabel("Lọc đơn vị quản trị")
    .selectOption({ label: "Chi nhánh TP. Hồ Chí Minh" });
  await search.fill("kho thiet bi");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText(
    "Chi nhánh TP. Hồ Chí Minh",
  );

  await page
    .getByRole("button", { name: "Chính sách mượn", exact: true })
    .click();
  await expect(page.getByLabel("Lọc trạng thái quản trị")).toHaveCount(0);
  await search.fill("chinh sach loc");
  await page.getByLabel("Lọc hiệu lực chính sách").selectOption("scheduled");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText(
    "Chính sách lọc sắp áp dụng",
  );
  await page.getByLabel("Lọc hiệu lực chính sách").selectOption("replaced");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText(
    "Chính sách lọc đã thay thế",
  );
  await search.fill("");
  await page.getByLabel("Lọc hiệu lực chính sách").selectOption("current");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText(lookup.policy.name);
  await expect(
    page.getByRole("button", { name: /^Tìm( kiếm)?$/, exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: "test-results/admin-policy-filter.png",
    animations: "disabled",
  });
});

test("Bộ lọc quản trị ở điện thoại không tràn ngang và đổi tab không giữ lọc cũ", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  for (const name of [
    "Tài khoản",
    "Đơn vị",
    "Loại tài sản",
    "Địa điểm",
    "Chính sách mượn",
  ]) {
    await page.getByRole("button", { name, exact: true }).click();
    const search = page.getByRole("searchbox", {
      name: "Tìm kiếm quản trị",
      exact: true,
    });
    await expect(search).toHaveValue("");
    for (const control of await page
      .locator(".admin-filters input, .admin-filters select")
      .all()) {
      const bounds = await control.boundingBox();
      expect(bounds).not.toBeNull();
      expect(bounds!.x).toBeGreaterThanOrEqual(0);
      expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(391);
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await search.fill("zzzz-khong-co");
    await expect(
      page.getByText("Không có kết quả phù hợp.", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Xóa bộ lọc", exact: true }).click();
    await expect(search).toHaveValue("");
  }
  await page.getByRole("button", { name: "Tài khoản", exact: true }).click();
  await page.screenshot({
    path: "test-results/admin-filters-mobile.png",
    animations: "disabled",
    fullPage: true,
  });
});
