export const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' })
  if (!response.ok) {
    let message = `Yêu cầu thất bại (${response.status})`
    try {
      const payload = await response.json()
      message = payload.detail ?? payload.error?.message ?? message
    } catch {
      // Keep the HTTP fallback message.
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export type Page<T> = { items: T[]; page: number; page_size: number; total: number }

export type Customer = {
  id: string
  customer_code: string
  full_name: string
  phone?: string
  email?: string
  profile_image_url?: string
  status: 'ACTIVE' | 'INACTIVE'
  face_consent: boolean
}

export async function runSimulation(seed = 20260923) {
  const response = await fetch('/simulator/api/v1/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_count: 100, seed })
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail ?? `Không tạo được dữ liệu mô phỏng (${response.status})`)
  }
  return response.json()
}

export type Category = { id: string; category_code: string; name: string; active: boolean }

export type Product = {
  id: string
  sku: string
  name: string
  category_id: string
  current_price: number
  status: 'ACTIVE' | 'INACTIVE'
  category?: Category
}

export type OrderItem = {
  id: string
  product_code_snapshot: string
  product_name_snapshot: string
  quantity: number
  unit_price: number
  line_total: number
}

export type Order = {
  id: string
  external_code: string
  customer_id: string
  ordered_at: string
  total_amount: number
  status: string
  items: OrderItem[]
  customer?: Customer
}

export type Touchpoint = {
  id: string
  touchpoint_code: string
  name: string
  sequence_order: number
  active: boolean
}

export type SequenceCandidateMetric = {
  k: number
  asw: number
  min_cluster_size: number
  max_cluster_size: number
  required_min_cluster_size: number
  accepted: boolean
  rejection_reason?: string | null
}

export type SequenceAnalysisRun = {
  id: string
  source_type: 'CAMERA' | 'SIMULATOR'
  source_run_id: string
  status: 'RUNNING' | 'COMPLETED' | 'FAILED'
  preprocessing_version: string
  algorithm_version: string
  parameters: Record<string, unknown>
  candidate_metrics: SequenceCandidateMetric[]
  warnings: string[]
  received_visit_count: number
  used_visit_count: number
  excluded_visit_count: number
  selected_k?: number | null
  average_silhouette_width?: number | null
  distance_matrix_sha256?: string | null
  error_detail?: string | null
  created_at: string
  completed_at?: string | null
}

export type SequenceCluster = {
  id: string
  run_id: string
  cluster_id: number
  medoid_visit_id: string
  medoid_sequence: string[]
  size: number
  proportion: number
  mean_silhouette: number
  median_distance: number
  display_name?: string | null
}

export type SequenceAssignment = {
  id: string
  run_id: string
  visit_id: string
  cluster_id: number
  sequence: string[]
  sequence_metadata: Array<Record<string, unknown>>
  distance_to_medoid: number
  silhouette: number
  visit_started_at?: string | null
  customer?: Pick<Customer, 'id' | 'customer_code' | 'full_name'> | null
}
