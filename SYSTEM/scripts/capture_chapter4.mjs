import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { mkdir } from 'node:fs/promises'

const output = '/Users/sotatek/Desktop/Do An/BAO CAO/Hinhve/Chuong4'
await mkdir(output, { recursive: true })

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
})
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 })
const page = await context.newPage()

async function capture(name, path, wait = 900) {
  await page.goto(`http://127.0.0.1:8080${path}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(wait)
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false })
}

await page.goto('http://127.0.0.1:8080/login', { waitUntil: 'networkidle' })
await page.getByLabel('Email').fill('manager@example.com')
await page.getByLabel('Mật khẩu').fill('demo1234')
await page.getByRole('button', { name: 'Đăng nhập' }).click()
await page.waitForURL('**/dashboard')

await capture('4_01_tong_quan', '/dashboard')
await page.getByText('Biến thiên theo thời gian và khu vực', { exact: true }).click()
await page.waitForTimeout(800)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/4_13_bien_thien_theo_thoi_gian_khu_vuc.png`, fullPage: false })
await capture('4_02_danh_sach_khach_hang', '/customers')

await page.getByPlaceholder('Tìm theo mã, tên hoặc số điện thoại').fill('CUS-DEMO-001')
await page.getByPlaceholder('Tìm theo mã, tên hoặc số điện thoại').press('Enter')
await page.waitForTimeout(400)
await page.getByRole('button', { name: 'Hồ sơ' }).click()
await page.waitForTimeout(500)
await page.screenshot({ path: `${output}/4_03_ho_so_lich_su_mua_hang.png`, fullPage: false })

await capture('4_04_danh_muc_san_pham', '/products')
await capture('4_05_lich_su_mua_hang', '/orders')
await capture('4_06_diem_cham', '/touchpoints')
await capture('4_07_theo_doi_hanh_trinh', '/visits', 1300)
await capture('4_08_phan_bo_bieu_cam', '/reports', 1200)

await page.getByText('Thay đổi giữa điểm chạm', { exact: true }).click()
await page.waitForTimeout(900)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/4_09_thay_doi_bieu_cam.png`, fullPage: false })

await page.getByText('Chất lượng dữ liệu', { exact: true }).click()
await page.waitForTimeout(700)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/4_10_chat_luong_du_lieu.png`, fullPage: false })

await page.goto('http://127.0.0.1:8000/docs', { waitUntil: 'networkidle' })
await page.waitForTimeout(500)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/4_11_tai_lieu_api.png`, fullPage: false })

await page.goto('http://127.0.0.1:8002/docs', { waitUntil: 'networkidle' })
await page.waitForTimeout(500)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/4_12_dich_vu_mo_phong.png`, fullPage: false })

await browser.close()
console.log(`Đã lưu ảnh Chương 4 tại ${output}`)
