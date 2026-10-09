import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { copyFile, mkdir, writeFile } from 'node:fs/promises'

const sourceRunId = process.env.SOURCE_RUN_ID ?? 'KDEF-KAGGLE-20261008-LIVE'
const baseUrl = process.env.WEB_URL ?? 'http://127.0.0.1:8080'
const projectRoot = '/Users/sotatek/Desktop/Do An'
const artifactOutput = `${projectRoot}/SYSTEM/artifacts/experiment-runs/${sourceRunId}/screenshots`
const chapter4Output = `${projectRoot}/BAO CAO/Hinhve/Chuong4`
const chapter5Output = `${projectRoot}/BAO CAO/Hinhve/Chuong5`
await Promise.all([
  mkdir(artifactOutput, { recursive: true }),
  mkdir(chapter4Output, { recursive: true }),
  mkdir(chapter5Output, { recursive: true })
])

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
})
const context = await browser.newContext({ viewport: { width: 1600, height: 1100 }, deviceScaleFactor: 1 })
const page = await context.newPage()

async function capture(artifactName, chapter4Name, chapter5Name) {
  const artifactPath = `${artifactOutput}/${artifactName}`
  await page.screenshot({ path: artifactPath, fullPage: false })
  if (chapter4Name) await copyFile(artifactPath, `${chapter4Output}/${chapter4Name}`)
  if (chapter5Name) await copyFile(artifactPath, `${chapter5Output}/${chapter5Name}`)
}

await page.goto(`${baseUrl}/login`, { waitUntil: 'networkidle' })
await page.getByLabel('Email').fill(process.env.DEMO_USER_EMAIL ?? 'manager@example.com')
await page.getByLabel('Mật khẩu').fill(process.env.DEMO_USER_PASSWORD ?? 'demo1234')
await page.getByRole('button', { name: 'Đăng nhập' }).click()
await page.waitForURL('**/dashboard')

const verified = await page.evaluate(async requestedRun => {
  const [customersResponse, visitsResponse, observationsResponse, analysesResponse] = await Promise.all([
    fetch('/api/v1/customers?page_size=100&search=CUS-KDEF'),
    fetch('/api/v1/visits'),
    fetch(`/api/v1/observations?experiment_run_id=${encodeURIComponent(requestedRun)}&page_size=100`),
    fetch('/api/v1/sequence-analyses?source_type=CAMERA')
  ])
  if (![customersResponse, visitsResponse, observationsResponse, analysesResponse].every(response => response.ok)) {
    throw new Error('Không đọc được dữ liệu KDEF từ API đang chạy')
  }
  const customers = await customersResponse.json()
  const visits = await visitsResponse.json()
  const observations = await observationsResponse.json()
  const analyses = await analysesResponse.json()
  const run = analyses.find(item => item.source_run_id === requestedRun && item.status === 'COMPLETED')
  if (customers.total !== 5) throw new Error(`Yêu cầu 5 khách KDEF, API trả ${customers.total}`)
  if (observations.total !== 100) throw new Error(`Yêu cầu 100 quan sát CAMERA, API trả ${observations.total}`)
  if (!run || run.used_visit_count !== 22 || run.selected_k !== 5) {
    throw new Error('Kết quả phân tích chuỗi không khớp run KDEF đã kiểm chứng')
  }
  for (const customer of customers.items) {
    if (!customer.profile_image_url?.startsWith('/demo/customers/CUS-KDEF-')) {
      throw new Error(`Khách ${customer.customer_code} không có ảnh KDEF`)
    }
  }
  let targetVisit = null
  for (const visit of visits) {
    if (!visit.customer?.customer_code?.startsWith('CUS-KDEF-')) continue
    const detailResponse = await fetch(`/api/v1/visits/${visit.id}`)
    const detail = await detailResponse.json()
    const runObservations = detail.observations.filter(item => item.experiment_run_id === requestedRun)
    if (runObservations.length === 4 && runObservations.every(item => item.source_type === 'CAMERA')) {
      targetVisit = { id: visit.id, customerCode: visit.customer.customer_code }
      break
    }
  }
  if (!targetVisit) throw new Error('Không tìm thấy hành trình KDEF đủ bốn điểm chạm CAMERA')
  return {
    customerCount: customers.total,
    observationCount: observations.total,
    receivedVisitCount: run.received_visit_count,
    usedVisitCount: run.used_visit_count,
    excludedVisitCount: run.excluded_visit_count,
    selectedK: run.selected_k,
    analysisRunId: run.id,
    targetVisit
  }
}, sourceRunId)

await page.goto(`${baseUrl}/customers`, { waitUntil: 'networkidle' })
const search = page.getByPlaceholder('Tìm theo mã, tên hoặc số điện thoại')
await search.fill('CUS-KDEF')
await search.press('Enter')
await page.waitForFunction(() => {
  const images = [...document.querySelectorAll('.ant-table img')]
  return images.length === 5 && images.every(image => image.complete && image.naturalWidth > 0)
})
await capture('K01_kdef_customer_list.png', '4_25_danh_sach_khach_kdef.png', '5_16_du_lieu_khach_kdef.png')

await page.getByRole('button', { name: 'Hồ sơ' }).first().click()
await page.locator('.ant-drawer-content-wrapper').waitFor({ state: 'visible' })
await page.locator('.ant-drawer .customer-profile img').waitFor({ state: 'visible' })
await page.waitForTimeout(250)
await capture('K02_kdef_customer_profile.png', '4_26_ho_so_khach_kdef.png', '5_17_ho_so_khach_kdef.png')

await page.goto(`${baseUrl}/visits?visit_id=${verified.targetVisit.id}`, { waitUntil: 'networkidle' })
await page.getByText('Chi tiết theo thời gian', { exact: true }).waitFor()
await page.getByText('Quan sát trong lần đang xem', { exact: true }).waitFor()
await page.waitForFunction(() => document.body.innerText.includes('Quan sát trong lần đang xem') && document.body.innerText.includes('4'))
await capture('K03_kdef_four_touchpoint_journey.png', '4_27_hanh_trinh_kdef_bon_diem_cham.png', '5_18_hanh_trinh_kdef_bon_diem_cham.png')

await page.getByText('Chi tiết theo thời gian', { exact: true }).scrollIntoViewIfNeeded()
await page.waitForTimeout(300)
await capture('K04_kdef_camera_timeline.png', '4_28_chuoi_camera_kdef.png', '5_19_chuoi_camera_kdef.png')

const manifestPath = `${artifactOutput}/kdef_live_capture_manifest.json`
await writeFile(
  manifestPath,
  JSON.stringify({
    capturedAt: new Date().toISOString(),
    sourceRunId,
    sourceType: 'CAMERA',
    verified,
    screenshots: [
      'K01_kdef_customer_list.png',
      'K02_kdef_customer_profile.png',
      'K03_kdef_four_touchpoint_journey.png',
      'K04_kdef_camera_timeline.png'
    ]
  }, null, 2),
  'utf8'
)

await browser.close()
console.log(`Đã chụp luồng KDEF thật ${sourceRunId} vào ${artifactOutput}`)
