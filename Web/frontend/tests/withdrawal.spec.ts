import { test, expect, type Page } from "@playwright/test";

async function login(page: Page, username: string) {
  await page.goto("/");
  await page.getByLabel("Tên đăng nhập", { exact: true }).fill(username);
  await page
    .getByLabel("Mật khẩu", { exact: true })
    .fill(process.env.DEMO_PASSWORD!);
  await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Chào / })).toBeVisible();
}

async function post(page: Page, path: string, body: unknown) {
  return page.evaluate(
    async ({ path, body }) => {
      const session = await (await fetch("/api/auth/me")).json();
      const response = await fetch(`/api${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": session.csrf_token,
        },
        body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(result));
      return result;
    },
    { path, body },
  );
}

test("Thu hồi chờ nhận trả; nhu cầu chỉ xuất hiện sau hoàn trả và không có nút thêm", async ({
  page,
  browser,
}) => {
  await login(page, "ql.hn");
  const lookup = await page.evaluate(async () =>
    (await fetch("/api/lookups")).json(),
  );
  const session = await page.evaluate(async () =>
    (await fetch("/api/auth/me")).json(),
  );
  const category = lookup.categories.find((c: { active: boolean }) => c.active);
  const location = lookup.locations.find(
    (l: { unit_id: number; active: boolean }) =>
      l.active && l.unit_id === session.user.unit_id,
  );
  const asset = await post(page, "/assets", {
    name: "Thiết bị kiểm thử thu hồi sau trả",
    category_id: category.id,
    location_id: location.id,
    condition: "Hoạt động tốt, đầy đủ phụ kiện.",
  });
  const context = await browser.newContext(),
    member = await context.newPage();
  await login(member, "an");
  const start = new Date(Date.now() + 2000).toISOString(),
    end = new Date(Date.now() + 3600000).toISOString();
  const purpose = "Mượn thiết bị cho buổi thực hành thu hồi sau trả.";
  const loan = await post(member, "/loans", {
    asset_id: asset.id,
    start_at: start,
    end_at: end,
    purpose,
    request_id: crypto.randomUUID(),
    new_need: {
      category_id: category.id,
      start_at: start,
      end_at: end,
      purpose,
      alternative: "HOAN_NHU_CAU",
    },
  });
  await member.goto("/loans?tab=needs");
  await expect(
    member.getByRole("button", { name: "Ghi nhận nhu cầu", exact: true }),
  ).toHaveCount(0);
  await expect(
    member.getByRole("link", { name: purpose, exact: true }),
  ).toHaveCount(0);
  await post(page, `/loans/${loan.id}/decision`, { approve: true });
  await page.waitForTimeout(2100);
  await page.goto(`/loans/${loan.id}`);
  await page
    .getByRole("button", { name: "Bàn giao tài sản", exact: true })
    .click();
  await page
    .getByLabel("Nội dung kiểm tra / Phụ kiện *")
    .fill("Thiết bị hoạt động tốt và đầy đủ phụ kiện.");
  await page
    .getByRole("button", { name: "Xác nhận bàn giao", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await member.goto(`/loans/${loan.id}`);
  await member
    .getByRole("button", { name: "Đã nhận tài sản", exact: true })
    .click();
  await page.goto(`/owned/${asset.id}`);
  await expect(
    page.getByRole("button", {
      name: "Xử lý & đánh giá vòng đời",
      exact: true,
    }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Tạm ngừng chia sẻ", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Thu hồi tài sản", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Thu hồi tài sản", exact: true })
    .click();
  await expect(page.locator(".page-heading .badge")).toHaveText("Chờ thu hồi");
  await page.screenshot({
    path: "test-results/withdrawal-waiting.png",
    animations: "disabled",
  });
  await member.reload();
  await member
    .getByRole("button", { name: "Trả tài sản", exact: true })
    .click();
  await member
    .getByLabel("Nội dung kiểm tra / Phụ kiện *")
    .fill("Trả đầy đủ thiết bị và phụ kiện, hoạt động tốt.");
  await member
    .getByRole("button", { name: "Xác nhận trả tài sản", exact: true })
    .click();
  await expect(member.getByRole("dialog")).toHaveCount(0);
  await page.goto(`/loans/${loan.id}`);
  await page
    .getByRole("button", { name: "Xác nhận đã nhận trả", exact: true })
    .click();
  await expect(page.locator(".loan-progress")).toContainText("Đã hoàn trả");
  await expect(
    page.getByRole("link", { name: "Xem hồ sơ tài sản", exact: true }),
  ).toHaveCount(0);
  await page.goto("/owned");
  await expect(
    page.getByRole("heading", { name: asset.name, exact: true }),
  ).toHaveCount(0);
  await member.goto("/loans?tab=needs");
  await expect(
    member.getByRole("link", { name: purpose, exact: true }),
  ).toBeVisible();
  await expect(
    member.getByRole("cell", { name: "Hoãn nhu cầu sử dụng", exact: true }),
  ).toBeVisible();
  await member.screenshot({
    path: "test-results/needs-after-return.png",
    animations: "disabled",
  });
  await context.close();
});

test("Người mượn xem lý do thu hồi sau khi phiếu chờ bị xóa", async ({
  page,
  browser,
}) => {
  await login(page, "ql.hn");
  const lookup = await (await page.request.get("/api/lookups")).json();
  const session = await (await page.request.get("/api/auth/me")).json();
  const location = lookup.locations.find(
    (item: { unit_id: number }) => item.unit_id === session.user.unit_id,
  );
  const asset = await post(page, "/assets", {
    name: "Máy chiếu thông báo thu hồi",
    category_id: lookup.categories.find(
      (item: { active: boolean }) => item.active,
    ).id,
    location_id: location.id,
    condition: "Hoạt động tốt, đầy đủ phụ kiện.",
  });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  try {
    const member = await context.newPage();
    await login(member, "an");
    const loan = await post(member, "/loans", {
      asset_id: asset.id,
      start_at: new Date(Date.now() + 60000).toISOString(),
      end_at: new Date(Date.now() + 3600000).toISOString(),
      purpose: "Dùng cho buổi trình bày tại chi nhánh.",
      request_id: crypto.randomUUID(),
    });
    await page.goto(`/owned/${asset.id}`);
    await page
      .getByRole("button", { name: "Thu hồi tài sản", exact: true })
      .click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Thu hồi tài sản", exact: true })
      .click();
    await expect(page).toHaveURL(/\/owned$/);
    expect((await member.request.get(`/api/loans/${loan.id}`)).status()).toBe(
      404,
    );
    const bell = member.getByRole("button", { name: "Thông báo", exact: true });
    await bell.click();
    const dialog = member.getByRole("dialog", {
      name: "Thông báo",
      exact: true,
    });
    const notice = dialog.getByRole("listitem").filter({ hasText: asset.name });
    await expect(notice).toContainText(
      `PM-${String(loan.id).padStart(4, "0")}`,
    );
    await expect(notice).toContainText("Người phụ trách đã thu hồi tài sản");
    await notice.getByRole("button", { name: "Đánh dấu đã đọc" }).click();
    await expect(
      notice.getByRole("button", { name: "Đánh dấu đã đọc" }),
    ).toHaveCount(0);
    await member.reload();
    await bell.click();
    await expect(notice).toBeVisible();
    await expect(
      notice.getByRole("button", { name: "Đánh dấu đã đọc" }),
    ).toHaveCount(0);
    expect(
      await member.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  } finally {
    await context.close();
  }
});
