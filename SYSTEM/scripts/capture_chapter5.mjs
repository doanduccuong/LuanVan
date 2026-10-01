import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { mkdir } from 'node:fs/promises'

const output = '/Users/sotatek/Desktop/Do An/BAO CAO/Hinhve/Chuong5'
await mkdir(output, { recursive: true })

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
})
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 })
const page = await context.newPage()

async function open(path, wait = 900) {
  await page.goto(`http://127.0.0.1:8080${path}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(wait)
}

await open('/login', 200)
await page.getByLabel('Email').fill('manager@example.com')
await page.getByLabel('Mật khẩu').fill('demo1234')
await page.getByRole('button', { name: 'Đăng nhập' }).click()
await page.waitForURL('**/dashboard')
await page.waitForTimeout(1800)
await page.screenshot({ path: `${output}/5_06_tong_quan_ket_qua.png`, fullPage: false })

await open('/customers', 1200)
await page.screenshot({ path: `${output}/5_04_du_lieu_khuon_mat.png`, fullPage: false })

await open('/visits', 1300)
const completeVisit = await page.evaluate(async () => {
  const visits = await fetch('/api/v1/visits').then(response => response.json())
  for (let index = 0; index < visits.length; index += 1) {
    const visit = visits[index]
    const [detail, analysis] = await Promise.all([
      fetch(`/api/v1/visits/${visit.id}`).then(response => response.json()),
      fetch(`/api/v1/visits/${visit.id}/analysis`).then(response => response.json())
    ])
    if (detail.observations.length >= 4 && analysis.missing_touchpoints.length === 0) return { index }
  }
  return null
})
if (!completeVisit) throw new Error('Không tìm thấy lần mua sắm đủ bốn khu vực')
const visitPage = Math.floor(completeVisit.index / 8) + 1
const rowOnPage = completeVisit.index % 8
for (let currentPage = 1; currentPage < visitPage; currentPage += 1) {
  await page.locator('.ant-pagination-next').click()
}
await page.locator('.ant-table-row').nth(rowOnPage).click()
await page.waitForTimeout(700)
await page.screenshot({ path: `${output}/5_07_hanh_trinh_bon_khu_vuc.png`, fullPage: false })

await page.getByText(/Chưa xác định khách hàng \(/).click()
await page.waitForTimeout(500)
await page.screenshot({ path: `${output}/5_05_quan_sat_chua_xac_dinh.png`, fullPage: false })

await open('/reports', 1200)
await page.getByText('Chất lượng dữ liệu', { exact: true }).click()
await page.waitForTimeout(700)
await page.evaluate(() => window.scrollTo(0, 0))
await page.screenshot({ path: `${output}/5_08_chat_luong_du_lieu.png`, fullPage: false })

await browser.close()
console.log(`Đã lưu ảnh Chương 5 tại ${output}`)
