import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'

const root = '/Users/sotatek/Desktop/Do An'
const sourceRunId = process.env.SOURCE_RUN_ID
if (!sourceRunId) throw new Error('Thiếu SOURCE_RUN_ID')
const output = `${root}/SYSTEM/artifacts/experiment-runs/${sourceRunId}`
const updateReport = process.env.UPDATE_REPORT === 'true'
await mkdir(`${output}/screenshots`, { recursive: true })
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
const page = await browser.newPage({ viewport: { width: 1600, height: 1100 }, deviceScaleFactor: 1 })
const errors = []
page.on('pageerror', error => errors.push(String(error)))
await page.goto('http://127.0.0.1:8080/login', { waitUntil: 'networkidle' })
await page.getByLabel('Email').fill(process.env.DEMO_USER_EMAIL ?? 'manager@example.com')
await page.getByLabel('Mật khẩu').fill(process.env.DEMO_USER_PASSWORD ?? 'demo1234')
await page.getByRole('button', { name: 'Đăng nhập' }).click()
await page.waitForURL('**/dashboard')
await page.goto('http://127.0.0.1:8080/reports', { waitUntil: 'networkidle' })
await page.getByRole('tab', { name: 'Điểm hành trình', exact: true }).click()
await page.locator('.journey-scoring-settings').waitFor()
await page.getByLabel('Điểm Happy', { exact: true }).waitFor()
// Exercise the real configuration form and then score the source through its own workflow.
const weightInputs = page.getByRole('spinbutton', { name: /^Trọng số / })
for (let index = 0; index < await weightInputs.count(); index += 1) await weightInputs.nth(index).fill('0')
if (!(await page.getByRole('button', { name: 'Lưu cấu hình điểm', exact: true }).isDisabled())) throw new Error('Giao diện cho phép lưu tổng trọng số bằng 0')
await page.getByRole('button', { name: 'Khôi phục cấu hình đã lưu', exact: true }).click()
const saveResponse = page.waitForResponse(response => response.url().endsWith('/journey-scoring-settings') && response.request().method() === 'PUT')
await page.getByRole('button', { name: 'Lưu cấu hình điểm', exact: true }).click()
if (!(await saveResponse).ok()) throw new Error('Không lưu được cấu hình bằng giao diện')
await page.getByLabel('Mã lần phát dữ liệu Camera', { exact: true }).fill(sourceRunId)
const scoreResponse = page.waitForResponse(response => response.url().endsWith('/journey-scoring-runs') && response.request().method() === 'POST')
await page.getByRole('button', { name: 'Tính điểm hành trình', exact: true }).click()
const response = await scoreResponse
if (!response.ok()) throw new Error(await response.text())
const run = await response.json()
if (run.source_run_id !== sourceRunId || run.scoring_summary.journey_count < 1) throw new Error('Lần tính điểm không khớp dữ liệu nguồn')
await page.locator('.journey-score-results').waitFor()
await page.getByText(`Trung bình có trọng số · cấu hình ${run.scoring_config.revision}`, { exact: true }).waitFor()
const scores = await page.evaluate(async id => {
  const items = []
  for (let page = 1; ; page += 1) {
    const response = await fetch(`/api/v1/journey-scoring-runs/${id}/scores?page=${page}&page_size=200`)
    if (!response.ok) throw new Error('Không đọc được điểm từ API')
    const data = await response.json()
    items.push(...data.items)
    if (items.length >= data.total) return { items, total: data.total }
  }
}, run.id)
if (scores.items.some(item => 'coverage' in item || 'status' in item)) throw new Error('API vẫn trả về chỉ số hoặc trạng thái bao phủ')
if ('complete_count' in run.scoring_summary || 'partial_count' in run.scoring_summary) throw new Error('API vẫn phân nhóm theo độ bao phủ')
const scored = scores.items.filter(item => item.score != null)
const expectedMean = scored.reduce((sum, item) => sum + item.score, 0) / scored.length
if (Math.abs(expectedMean - run.scoring_summary.mean) > 1e-12) throw new Error('Điểm trung bình chưa tính trên toàn bộ các chuỗi có điểm')
if ((await page.locator('.journey-score-results').innerText()).includes('bao phủ')) throw new Error('Giao diện vẫn hiển thị độ bao phủ')
await writeFile(`${output}/journey-scoring/run.json`, JSON.stringify({ captured_at: new Date().toISOString(), result: run }, null, 2))
await writeFile(`${output}/journey-scoring/scores.json`, JSON.stringify(scores, null, 2))
try {
  const endToEnd = JSON.parse(await readFile(`${output}/end_to_end_summary.json`, 'utf8'))
  await writeFile(`${output}/end_to_end_summary.json`, JSON.stringify({ ...endToEnd, scoring_summary: run.scoring_summary, scoring_config: run.scoring_config }, null, 2))
} catch (error) {
  if (error.code !== 'ENOENT') throw error
}
await page.waitForFunction(() => document.querySelectorAll('.ant-message-notice').length === 0)

async function capture(locator, name, reportName, chapter4Name) {
  const path = `${output}/screenshots/${name}`
  await locator.screenshot({ path })
  if (updateReport) {
    await copyFile(path, `${root}/BAO CAO/Hinhve/Chuong5/${reportName}`)
    if (chapter4Name) await copyFile(path, `${root}/BAO CAO/Hinhve/Chuong4/${chapter4Name}`)
  }
}
await capture(page.locator('.journey-scoring-settings'), 'E13_scoring_configuration.png', '5_29_cau_hinh_diem_hanh_trinh.png', '4_30_cau_hinh_diem_hanh_trinh.png')
await capture(page.locator('.journey-score-results'), 'E14_journey_scores.png', '5_30_diem_tung_hanh_trinh.png', '4_31_diem_hanh_trinh.png')
await page.locator('.journey-score-results .ant-table-row-expand-icon').first().click()
await capture(page.locator('.journey-score-results .ant-table-expanded-row').first(), 'E15_journey_score_breakdown.png', '5_32_chi_tiet_diem_hanh_trinh.png')

const layouts = []
for (const width of [390, 768, 1600]) {
  await page.setViewportSize({ width, height: 1050 })
  await page.locator('.journey-scoring-settings').scrollIntoViewIfNeeded()
  await page.screenshot({ path: `${output}/screenshots/scoring_layout_${width}.png`, fullPage: true })
  layouts.push(await page.evaluate(() => ({ width: innerWidth, documentWidth: document.documentElement.scrollWidth })))
}
if (errors.length) throw new Error(errors.join('\n'))
await page.locator('.journey-score-results .ant-table-tbody > tr.ant-table-row .ant-btn-link').first().click()
await page.waitForURL(`**/visits?visit_id=${scores.items[0].visit_id}`)
await writeFile(`${output}/screenshots/scoring_browser_verification.json`, JSON.stringify({ runId: run.id, sourceRunId, savedRevision: run.scoring_config.revision, scoreCount: scores.total, meanAcrossAllScores: expectedMean, coverageRemoved: true, zeroWeightsBlocked: true, traceVisitId: scores.items[0].visit_id, layouts, errors }, null, 2))
await browser.close()
console.log(`Đã kiểm tra cấu hình và tính điểm độc lập cho ${scores.total} hành trình trên giao diện`)
