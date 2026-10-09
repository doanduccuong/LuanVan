import { execFileSync } from 'node:child_process'
import { mkdir, writeFile, copyFile } from 'node:fs/promises'
import { chromium } from '/Users/sotatek/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'

const projectRoot = '/Users/sotatek/Desktop/Do An'
const runId = process.env.SOURCE_RUN_ID ?? 'KDEF-KAGGLE-20261008-LIVE'
const outputDir = `${projectRoot}/SYSTEM/artifacts/experiment-runs/${runId}/screenshots`
const screenshotPath = `${outputDir}/K05_system_runtime_status.png`
const manifestPath = `${outputDir}/system_runtime_status.json`
const reportPath = `${projectRoot}/BAO CAO/Hinhve/Chuong4/4_29_trang_thai_he_thong_docker.png`
await mkdir(outputDir, { recursive: true })

const rawCompose = execFileSync(
  'docker',
  ['compose', 'ps', '--all', '--format', 'json'],
  { cwd: `${projectRoot}/SYSTEM`, encoding: 'utf8' }
).trim()
const containers = rawCompose
  .split('\n')
  .filter(Boolean)
  .map(line => JSON.parse(line))
  .map(item => ({
    service: item.Service,
    name: item.Name,
    image: item.Image,
    state: item.State,
    health: item.Health || (item.Service === 'migrate' && item.ExitCode === 0 ? 'completed' : '—'),
    ports: item.Ports || '—',
    exitCode: item.ExitCode
  }))
  .sort((a, b) => ['postgres', 'vision', 'migrate', 'api', 'simulator', 'web'].indexOf(a.service) - ['postgres', 'vision', 'migrate', 'api', 'simulator', 'web'].indexOf(b.service))

const endpointSpecs = [
  ['API', 'http://127.0.0.1:8000/health/ready'],
  ['Vision', 'http://127.0.0.1:8001/health/ready'],
  ['Simulator', 'http://127.0.0.1:8002/health/ready'],
  ['Web', 'http://127.0.0.1:8080/']
]
const endpoints = []
for (const [name, url] of endpointSpecs) {
  const startedAt = Date.now()
  try {
    const response = await fetch(url)
    const body = await response.text()
    endpoints.push({ name, url, status: response.status, ok: response.ok, elapsedMs: Date.now() - startedAt, body: body.slice(0, 180) })
  } catch (error) {
    endpoints.push({ name, url, status: null, ok: false, elapsedMs: Date.now() - startedAt, body: String(error) })
  }
}

const capturedAt = new Date().toISOString()
const allRuntimeChecksPass = containers.every(item =>
  item.service === 'migrate' ? item.exitCode === 0 : item.state === 'running'
) && endpoints.every(item => item.ok)

const escapeHtml = value => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')

const containerRows = containers.map(item => `
  <tr>
    <td><strong>${escapeHtml(item.service)}</strong><div class="muted">${escapeHtml(item.name)}</div></td>
    <td>${escapeHtml(item.image)}</td>
    <td><span class="pill ${item.state === 'running' || item.health === 'completed' ? 'ok' : 'bad'}">${escapeHtml(item.state)}</span></td>
    <td>${escapeHtml(item.health)}</td>
    <td class="mono">${escapeHtml(item.ports)}</td>
  </tr>`).join('')

const endpointRows = endpoints.map(item => `
  <tr>
    <td><strong>${escapeHtml(item.name)}</strong></td>
    <td class="mono">${escapeHtml(item.url)}</td>
    <td><span class="pill ${item.ok ? 'ok' : 'bad'}">${item.status ?? 'ERROR'}</span></td>
    <td>${item.elapsedMs} ms</td>
    <td class="mono small">${escapeHtml(item.body)}</td>
  </tr>`).join('')

const html = `<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><style>
  * { box-sizing: border-box; } body { margin: 0; padding: 42px; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7f8; color: #14213d; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
  h1 { margin: 0 0 9px; font-size: 30px; } h2 { margin: 0 0 14px; font-size: 20px; }
  .muted { color: #64748b; font-size: 13px; margin-top: 4px; } .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; } .small { max-width: 390px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .summary { padding: 14px 18px; border-radius: 12px; background: ${allRuntimeChecksPass ? '#dcfce7' : '#fee2e2'}; color: ${allRuntimeChecksPass ? '#166534' : '#991b1b'}; font-weight: 700; }
  .card { background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin-bottom: 22px; box-shadow: 0 8px 22px rgba(15, 23, 42, .05); }
  table { width: 100%; border-collapse: collapse; } th { text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .04em; background: #f8fafc; }
  th, td { padding: 12px 11px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
  tr:last-child td { border-bottom: none; } .pill { display: inline-block; padding: 4px 9px; border-radius: 999px; font-size: 12px; font-weight: 700; } .pill.ok { background: #dcfce7; color: #166534; } .pill.bad { background: #fee2e2; color: #991b1b; }
  .footer { color: #64748b; font-size: 12px; }
</style></head><body>
  <div class="header"><div><h1>Trạng thái hệ thống tại thời điểm kiểm chứng</h1><div class="muted">Run dữ liệu: ${escapeHtml(runId)} · ${escapeHtml(capturedAt)}</div></div><div class="summary">${allRuntimeChecksPass ? 'ĐẠT — các dịch vụ đang hoạt động' : 'KHÔNG ĐẠT — có kiểm tra thất bại'}</div></div>
  <div class="card"><h2>Docker Compose</h2><table><thead><tr><th>Dịch vụ</th><th>Image</th><th>Trạng thái</th><th>Health</th><th>Cổng</th></tr></thead><tbody>${containerRows}</tbody></table></div>
  <div class="card"><h2>Kiểm tra HTTP trực tiếp</h2><table><thead><tr><th>Dịch vụ</th><th>Địa chỉ</th><th>HTTP</th><th>Thời gian</th><th>Phản hồi</th></tr></thead><tbody>${endpointRows}</tbody></table></div>
  <div class="footer">Ảnh này do scripts/capture_system_status.mjs sinh trực tiếp từ docker compose ps --all và các endpoint đang chạy; dữ liệu chi tiết được lưu trong system_runtime_status.json.</div>
</body></html>`

const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
const page = await browser.newPage({ viewport: { width: 1700, height: 1050 }, deviceScaleFactor: 1 })
await page.setContent(html, { waitUntil: 'load' })
await page.screenshot({ path: screenshotPath, fullPage: true })
await browser.close()
await copyFile(screenshotPath, reportPath)
await writeFile(manifestPath, JSON.stringify({ capturedAt, runId, allRuntimeChecksPass, containers, endpoints, screenshotPath, reportPath }, null, 2), 'utf8')

if (!allRuntimeChecksPass) throw new Error('Có dịch vụ hoặc endpoint không hoạt động; xem system_runtime_status.json')
console.log(`Đã lưu bằng chứng trạng thái hệ thống tại ${screenshotPath}`)
