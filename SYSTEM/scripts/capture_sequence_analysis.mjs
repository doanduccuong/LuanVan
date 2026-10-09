import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { copyFile, mkdir, writeFile } from 'node:fs/promises'

const baseUrl = process.env.WEB_URL ?? 'http://127.0.0.1:8080'
const apiDocsUrl = process.env.API_DOCS_URL ?? 'http://127.0.0.1:8000/docs'
const sourceRunId = process.env.SOURCE_RUN_ID
const sourceType = process.env.SOURCE_TYPE ?? 'SIMULATOR'
const expectedVisits = Number(process.env.EXPECTED_USED_VISITS ?? 125)
const expectedK = process.env.EXPECTED_K ? Number(process.env.EXPECTED_K) : null
if (!sourceRunId) throw new Error('Thiếu SOURCE_RUN_ID')

// Keep the controlled-simulation evidence and the real-camera evidence in
// separate report files. Re-running one experiment must not overwrite the
// screenshots of the other experiment.
const reportFiles = sourceType === 'CAMERA'
  ? {
      overview: '5_22_kdef_tong_quan_phan_cum.png',
      medoids: '5_23_kdef_cum_medoid.png',
      assignments: '5_24_kdef_gan_cum.png',
      trace: '5_25_kdef_truy_vet.png'
    }
  : {
      overview: '5_12_tong_quan_phan_cum_chuoi.png',
      medoids: '5_13_cum_va_medoid.png',
      assignments: '5_14_danh_sach_gan_cum.png',
      trace: '5_15_truy_vet_cum_ve_hanh_trinh.png'
    }

const projectRoot = '/Users/sotatek/Desktop/Do An'
const artifactOutput = `${projectRoot}/SYSTEM/artifacts/experiment-runs/${sourceRunId}/screenshots`
const reportOutput = `${projectRoot}/BAO CAO/Hinhve/Chuong5`
const implementationOutput = `${projectRoot}/BAO CAO/Hinhve/Chuong4`
await mkdir(artifactOutput, { recursive: true })
await mkdir(reportOutput, { recursive: true })
await mkdir(implementationOutput, { recursive: true })

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
})
const context = await browser.newContext({ viewport: { width: 1600, height: 1100 }, deviceScaleFactor: 1 })
const page = await context.newPage()

async function saveScreenshot(artifactName, reportName, implementationName = null) {
  const artifactPath = `${artifactOutput}/${artifactName}`
  await page.screenshot({ path: artifactPath, fullPage: false })
  await copyFile(artifactPath, `${reportOutput}/${reportName}`)
  if (implementationName) await copyFile(artifactPath, `${implementationOutput}/${implementationName}`)
}

async function saveElementScreenshot(locator, artifactName, reportName, implementationName = null) {
  const artifactPath = `${artifactOutput}/${artifactName}`
  await locator.screenshot({ path: artifactPath })
  await copyFile(artifactPath, `${reportOutput}/${reportName}`)
  if (implementationName) await copyFile(artifactPath, `${implementationOutput}/${implementationName}`)
}

await page.goto(`${baseUrl}/login`, { waitUntil: 'networkidle' })
await page.getByLabel('Email').fill(process.env.DEMO_USER_EMAIL ?? 'manager@example.com')
await page.getByLabel('Mật khẩu').fill(process.env.DEMO_USER_PASSWORD ?? 'demo1234')
await page.getByRole('button', { name: 'Đăng nhập' }).click()
await page.waitForURL('**/dashboard')

const target = await page.evaluate(async ({ requestedRun, requestedType }) => {
  const response = await fetch('/api/v1/sequence-analyses')
  if (!response.ok) throw new Error(`Không đọc được sequence analyses: ${response.status}`)
  const runs = await response.json()
  return runs.find(item => item.source_run_id === requestedRun && item.source_type === requestedType && item.status === 'COMPLETED') ?? null
}, { requestedRun: sourceRunId, requestedType: sourceType })
if (!target) throw new Error(`Không tìm thấy run hoàn tất ${sourceType}/${sourceRunId}`)
if (target.used_visit_count !== expectedVisits) {
  throw new Error(`Run dùng ${target.used_visit_count} visit, yêu cầu ${expectedVisits}`)
}
if (expectedK !== null && target.selected_k !== expectedK) {
  throw new Error(`Run chọn K=${target.selected_k}, yêu cầu K=${expectedK}`)
}

const trace = await page.evaluate(async runId => {
  const [clustersResponse, assignmentsResponse] = await Promise.all([
    fetch(`/api/v1/sequence-analyses/${runId}/clusters`),
    fetch(`/api/v1/sequence-analyses/${runId}/assignments?page_size=200`)
  ])
  if (!clustersResponse.ok || !assignmentsResponse.ok) throw new Error('Không đọc được cluster/assignment')
  const clusters = await clustersResponse.json()
  const assignments = await assignmentsResponse.json()
  if (!clusters.length || assignments.total === 0) throw new Error('Run không có cluster hoặc assignment')
  const assignment = assignments.items[0]
  const visitResponse = await fetch(`/api/v1/visits/${assignment.visit_id}`)
  if (!visitResponse.ok) throw new Error('Không truy vết được assignment về visit')
  const visit = await visitResponse.json()
  if (visit.observations.length < 4) throw new Error('Visit truy vết không đủ bốn observation')
  return { clusterCount: clusters.length, assignmentCount: assignments.total, assignment, observationCount: visit.observations.length }
}, target.id)

await page.goto(`${baseUrl}/reports`, { waitUntil: 'networkidle' })
await page.getByText('Phân cụm chuỗi', { exact: true }).click()
await page.locator('.sequence-run-select').click()
await page.locator('.ant-select-item-option').filter({ hasText: sourceRunId }).filter({ hasText: 'COMPLETED' }).click()
await page.getByText(`Nguồn: ${sourceType} / ${sourceRunId}`, { exact: true }).waitFor()
await page.getByText(`K=${target.selected_k}`, { exact: true }).waitFor()
await page.keyboard.press('Escape')

await page.evaluate(() => window.scrollTo(0, 620))
await page.waitForTimeout(250)
await saveScreenshot(
  'E07_E08_sequence_run_overview.png',
  reportFiles.overview,
  '4_20_tong_quan_phan_cum_chuoi.png'
)

await page.getByText('Cụm và chuỗi đại diện (medoid)', { exact: true }).scrollIntoViewIfNeeded()
await page.waitForTimeout(300)
await saveElementScreenshot(
  page.locator('.cluster-summary-section'),
  'E09_cluster_medoids.png',
  reportFiles.medoids,
  '4_21_cum_va_medoid.png'
)

await page.getByText('Các lượt mua sắm trong cụm', { exact: true }).scrollIntoViewIfNeeded()
await page.waitForTimeout(300)
await saveScreenshot(
  'E10_cluster_assignments.png',
  reportFiles.assignments,
  '4_22_danh_sach_gan_cum.png'
)

await page.getByRole('button', { name: 'Xem hành trình' }).first().click()
await page.waitForURL('**/visits?visit_id=*')
await page.getByText('Chi tiết theo thời gian', { exact: true }).waitFor()
await page.getByText('Chi tiết theo thời gian', { exact: true }).scrollIntoViewIfNeeded()
await page.waitForTimeout(400)
await saveScreenshot(
  'E11_assignment_visit_trace.png',
  reportFiles.trace,
  '4_23_truy_vet_cum_ve_hanh_trinh.png'
)

const docsPage = await context.newPage()
await docsPage.goto(apiDocsUrl, { waitUntil: 'networkidle' })
const sequencePath = docsPage.getByText('/api/v1/sequence-analyses', { exact: true }).first()
await sequencePath.scrollIntoViewIfNeeded()
await docsPage.waitForTimeout(300)
const apiArtifactPath = `${artifactOutput}/E12_sequence_api_docs.png`
await docsPage.screenshot({ path: apiArtifactPath, fullPage: false })
await copyFile(apiArtifactPath, `${implementationOutput}/4_24_tai_lieu_api_phan_cum_chuoi.png`)

await writeFile(
  `${artifactOutput}/capture_manifest.json`,
  JSON.stringify({
    capturedAt: new Date().toISOString(),
    baseUrl,
    sourceRunId,
    sourceType,
    analysisRunId: target.id,
    selectedK: target.selected_k,
    averageSilhouetteWidth: target.average_silhouette_width,
    usedVisitCount: target.used_visit_count,
    trace,
    screenshots: [
      'E07_E08_sequence_run_overview.png',
      'E09_cluster_medoids.png',
      'E10_cluster_assignments.png',
      'E11_assignment_visit_trace.png',
      'E12_sequence_api_docs.png'
    ]
  }, null, 2),
  'utf8'
)

await browser.close()
console.log(`Đã chụp run ${target.id} vào ${artifactOutput}`)
