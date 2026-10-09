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
await page.screenshot({ path: `${output}/4_00_dang_nhap.png`, fullPage: false })
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

await page.getByPlaceholder('Tìm theo mã, tên hoặc số điện thoại').fill('CUS-EXP-001')
await page.getByPlaceholder('Tìm theo mã, tên hoặc số điện thoại').press('Enter')
await page.waitForTimeout(400)
await page.getByRole('button', { name: 'Hồ sơ' }).click()
await page.waitForTimeout(500)
await page.screenshot({ path: `${output}/4_03_ho_so_lich_su_mua_hang.png`, fullPage: false })

await capture('4_14_du_lieu_khuon_mat', '/faces')
await capture('4_04_danh_muc_san_pham', '/products')
await capture('4_05_lich_su_mua_hang', '/orders')
await capture('4_06_khu_vuc', '/touchpoints')
await page.goto('http://127.0.0.1:8080/visits', { waitUntil: 'networkidle' })
await page.waitForTimeout(1300)
const completeVisit = await page.evaluate(async () => {
  const visits = await fetch('/api/v1/visits').then(response => response.json())
  for (let index = 0; index < visits.length; index += 1) {
    const visit = visits[index]
    const [detail, analysis] = await Promise.all([
      fetch(`/api/v1/visits/${visit.id}`).then(response => response.json()),
      fetch(`/api/v1/visits/${visit.id}/analysis`).then(response => response.json())
    ])
    if (detail.observations.length >= 4 && analysis.missing_touchpoints.length === 0) {
      return {
        index,
        customerName: visit.customer.full_name,
        date: new Date(visit.started_at).toLocaleDateString('vi-VN')
      }
    }
  }
  return null
})
if (!completeVisit) throw new Error('Không tìm thấy lần mua sắm có đủ các khu vực để chụp minh họa')
const visitPage = Math.floor(completeVisit.index / 8) + 1
const rowOnPage = completeVisit.index % 8
if (visitPage > 1) {
  for (let currentPage = 1; currentPage < visitPage; currentPage += 1) {
    await page.locator('.ant-pagination-next').click()
  }
  await page.waitForTimeout(300)
}
await page.locator('.ant-table-row').nth(rowOnPage).click()
await page.waitForTimeout(600)
await page.screenshot({ path: `${output}/4_07_theo_doi_mua_sam.png`, fullPage: false })
await page.locator('.observation-card').first().click()
await page.waitForTimeout(500)
await page.setViewportSize({ width: 1600, height: 1250 })
await page.screenshot({ path: `${output}/4_16_chi_tiet_quan_sat.png`, fullPage: false })
await page.getByRole('button', { name: 'Close' }).click()
await capture('4_08_phan_bo_bieu_cam', '/reports', 1200)

await page.getByText('Thay đổi giữa các khu vực', { exact: true }).click()
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

await page.goto('file:///Users/sotatek/Desktop/Do%20An/SYSTEM/evidence/chapter4_evidence.html', { waitUntil: 'load' })
await page.screenshot({ path: `${output}/4_17_trang_thai_trien_khai.png`, fullPage: false })
await page.locator('.tests').screenshot({ path: `${output}/4_18_ket_qua_kiem_thu.png` })
await page.locator('.limits').screenshot({ path: `${output}/4_19_gioi_han_phien_ban.png` })

await browser.close()
console.log(`Đã lưu ảnh Chương 4 tại ${output}`)
