import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Alert, App, Button, Card, Col, Descriptions, Form, Input, InputNumber, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd'
import { api } from './api'
import type { JourneyScore, JourneyScoringConfig, JourneyScoringRun, Page } from './api'

const labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
const format = (value: number | null | undefined) => value == null ? '—' : value.toFixed(4)

export function JourneyScoringSettings() {
  const [form] = Form.useForm()
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['journey-scoring-settings'], queryFn: () => api<JourneyScoringConfig>('/journey-scoring-settings') })
  const weights = Form.useWatch('touchpoint_weights', form) as Record<string, number> | undefined
  const totalWeight = Object.values(weights ?? {}).reduce((sum, value) => sum + (Number(value) || 0), 0)
  useEffect(() => {
    if (query.data) form.setFieldsValue({
      expression_values: query.data.expression_values,
      touchpoint_weights: Object.fromEntries(query.data.touchpoints.map(point => [point.id, point.weight])),
      revision: query.data.revision,
    })
  }, [query.data, form])
  const save = useMutation({
    mutationFn: (values: { expression_values: Record<string, number>; touchpoint_weights: Record<string, number> }) =>
      api<JourneyScoringConfig>('/journey-scoring-settings', {
        method: 'PUT', body: JSON.stringify({ ...values, revision: query.data?.revision ?? 0 }),
      }),
    onSuccess: result => {
      queryClient.setQueryData(['journey-scoring-settings'], result)
      message.success(`Đã lưu cấu hình điểm hành trình — phiên bản ${result.revision}`)
    },
    onError: (error: Error) => message.error(error.message),
  })
  return <Card title="Cấu hình điểm hành trình" className="journey-scoring-settings" loading={query.isLoading}>
    {query.isError && <Alert type="error" showIcon message="Không tải được cấu hình" description={(query.error as Error).message} action={<Button onClick={() => query.refetch()}>Thử lại</Button>} />}
    {query.data && <Form form={form} layout="vertical" onFinish={save.mutate}>
      <Typography.Paragraph type="secondary">Thiết lập điểm quy đổi biểu cảm từ 0 đến 1 và trọng số cho từng điểm chạm. Mỗi lần tính điểm lưu lại cấu hình được sử dụng.</Typography.Paragraph>
      {!query.data.complete && <Alert type="warning" showIcon message="Điểm chạm đã thay đổi. Nhập đầy đủ trọng số rồi lưu lại." />}
      <Typography.Title level={5}>Điểm quy đổi biểu cảm</Typography.Title>
      <Row gutter={16}>
        {labels.map(label => <Col xs={12} sm={8} lg={3} key={label}>
          <Form.Item name={['expression_values', label]} label={label} rules={[{ required: true, message: 'Nhập điểm từ 0 đến 1' }]}>
            <InputNumber aria-label={`Điểm ${label}`} min={0} max={1} step={0.05} precision={4} className="full-width" />
          </Form.Item>
        </Col>)}
      </Row>
      <Typography.Title level={5}>Trọng số theo điểm chạm</Typography.Title>
      <Row gutter={16}>
        {query.data.touchpoints.map(point => <Col xs={24} sm={12} lg={6} key={point.id}>
          <Form.Item name={['touchpoint_weights', point.id]} label={`${point.sequence_order}. ${point.name}`} rules={[{ required: true, message: 'Nhập trọng số không âm' }]}>
            <InputNumber aria-label={`Trọng số ${point.name}`} min={0} step={0.05} precision={4} className="full-width" />
          </Form.Item>
          <Typography.Paragraph type="secondary">Tỷ trọng chuẩn hóa: {totalWeight > 0 ? `${(((weights?.[point.id] ?? 0) / totalWeight) * 100).toFixed(1)}%` : '—'}</Typography.Paragraph>
        </Col>)}
      </Row>
      <Space wrap>
        <Typography.Text>Tổng trọng số: {totalWeight.toFixed(4)}</Typography.Text>
        <Button type="primary" htmlType="submit" loading={save.isPending} disabled={totalWeight <= 0 || query.data.touchpoints.length === 0}>Lưu cấu hình điểm</Button>
        <Button onClick={() => form.setFieldsValue({ expression_values: query.data?.expression_values, touchpoint_weights: Object.fromEntries(query.data!.touchpoints.map(point => [point.id, point.weight])) })}>Khôi phục cấu hình đã lưu</Button>
      </Space>
      {totalWeight <= 0 && <Typography.Paragraph type="danger" role="alert">Tổng trọng số phải lớn hơn 0.</Typography.Paragraph>}
    </Form>}
  </Card>
}

export function JourneyScoreResults({ run }: { run: JourneyScoringRun }) {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  useEffect(() => setPage(1), [run.id])
  const rows = useQuery({ queryKey: ['journey-scores', run.id, page], queryFn: () => api<Page<JourneyScore>>(`/journey-scoring-runs/${run.id}/scores?page=${page}&page_size=10`) })
  const config = run.scoring_config
  const summary = run.scoring_summary
  if (!config || !summary) return null
  const totalWeight = config.touchpoints.reduce((sum, point) => sum + (point.weight ?? 0), 0)
  return <section className="journey-score-results">
    <Card title="Điểm tổng hợp từng hành trình">
      <Tag style={{ whiteSpace: 'normal', marginBottom: 16 }}>Trung bình có trọng số · cấu hình {config.revision}</Tag>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12}><Statistic title="Số chuỗi được xử lý" value={summary.journey_count} /></Col>
        <Col xs={24} sm={12}><Statistic title="Điểm hành trình trung bình" value={summary.mean ?? '—'} precision={4} suffix="/ 1" /></Col>
      </Row>
      <Typography.Paragraph className="result-alert">Điểm hành trình = tổng (trọng số × điểm biểu cảm) / tổng trọng số tại các điểm chạm có dữ liệu.</Typography.Paragraph>
      {summary.unscored_count > 0 && <Alert type="warning" showIcon message={`${summary.unscored_count} chuỗi chưa tính được điểm do tổng trọng số tại các điểm chạm có dữ liệu bằng 0.`} />}
      <Descriptions bordered size="small" column={1} items={[
        { key: 'values', label: 'Bảng điểm đã dùng', children: labels.map(label => `${label}: ${config.expression_values[label].toFixed(2)}`).join(' · ') },
        { key: 'weights', label: 'Trọng số đã dùng', children: config.touchpoints.map(point => `${point.name}: ${(((point.weight ?? 0) / totalWeight) * 100).toFixed(0)}%`).join(' · ') },
      ]} />
      {rows.isError && <Alert type="error" message="Không tải được điểm hành trình" description={(rows.error as Error).message} />}
      <Table<JourneyScore>
        className="table-card" size="small" rowKey="id" loading={rows.isLoading} dataSource={rows.data?.items}
        scroll={{ x: 950 }} pagination={{ current: page, pageSize: 10, total: rows.data?.total ?? 0, showSizeChanger: false, onChange: setPage }}
        columns={[
          { title: 'Khách hàng', render: (_, row) => row.customer ? `${row.customer.customer_code} — ${row.customer.full_name}` : row.visit_id },
          { title: 'Lần mua sắm', width: 180, render: (_, row) => <Button type="link" style={{ padding: 0 }} onClick={() => navigate(`/visits?visit_id=${row.visit_id}`)}>{row.visit_started_at ? new Date(row.visit_started_at).toLocaleString('vi-VN') : 'Xem hành trình'}</Button> },
          { title: 'Chuỗi biểu cảm', width: 330, render: (_, row) => row.sequence.join(' → ') },
          { title: 'Điểm hành trình [0–1]', dataIndex: 'score', render: value => <Typography.Text strong>{format(value)}</Typography.Text> },
        ]}
        expandable={{ expandedRowRender: row => <Table size="small" rowKey="touchpoint_id" pagination={false} dataSource={row.breakdown} scroll={{ x: 780 }} columns={[
          { title: 'Điểm chạm', dataIndex: 'touchpoint_name' },
          { title: 'Biểu cảm', render: (_, point) => point.states.join(' → ') || 'Chưa quan sát' },
          { title: 'Điểm tại điểm chạm', dataIndex: 'point_score', render: format },
          { title: 'Trọng số gốc', dataIndex: 'weight', render: format },
          { title: 'Trọng số chuẩn hóa', dataIndex: 'normalized_weight', render: format },
          { title: 'Đóng góp vào J', dataIndex: 'contribution', render: format },
        ]} /> }}
      />
    </Card>
  </section>
}

export function JourneyScoringPanel() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string>()
  const runs = useQuery({ queryKey: ['journey-scoring-runs'], queryFn: () => api<JourneyScoringRun[]>('/journey-scoring-runs') })
  useEffect(() => {
    if (runs.data?.length && !runs.data.some(run => run.id === selectedId)) setSelectedId(runs.data[0].id)
  }, [runs.data, selectedId])
  const selected = runs.data?.find(run => run.id === selectedId)
  const create = useMutation({
    mutationFn: (values: { source_run_id: string }) => api<JourneyScoringRun>('/journey-scoring-runs', { method: 'POST', body: JSON.stringify({ ...values, source_type: 'CAMERA' }) }),
    onSuccess: result => {
      queryClient.setQueryData<JourneyScoringRun[]>(['journey-scoring-runs'], previous => [result, ...(previous ?? [])])
      setSelectedId(result.id)
      message.success(`Đã tính điểm ${result.scoring_summary.journey_count} hành trình`)
    },
    onError: (error: Error) => message.error(error.message),
  })
  return <Space direction="vertical" size={16} className="full-width">
    <JourneyScoringSettings />
    <Card title="Tính điểm chuỗi biểu cảm">
      <Form layout="vertical" onFinish={create.mutate}>
        <Row gutter={16}>
          <Col xs={24} md={18}><Form.Item name="source_run_id" label="Mã lần phát dữ liệu Camera" rules={[{ required: true, message: 'Nhập mã nguồn dữ liệu' }]}><Input /></Form.Item></Col>
          <Col xs={24} md={6}><Form.Item label=" "><Button type="primary" block htmlType="submit" loading={create.isPending}>Tính điểm hành trình</Button></Form.Item></Col>
        </Row>
      </Form>
    </Card>
    <Card title="Kết quả tính điểm đã lưu">
      <Select className="full-width journey-score-run-select" value={selectedId} onChange={setSelectedId} loading={runs.isLoading} placeholder="Chọn lần tính điểm"
        options={runs.data?.map(run => ({ value: run.id, label: `${new Date(run.created_at).toLocaleString('vi-VN')} · ${run.source_run_id} · ${run.scoring_summary.journey_count} hành trình` }))} />
      {runs.isError && <Alert type="error" message="Không tải được lịch sử tính điểm" description={(runs.error as Error).message} />}
      {!runs.isLoading && !runs.data?.length && <Typography.Paragraph>Chưa có kết quả tính điểm.</Typography.Paragraph>}
    </Card>
    {selected && <JourneyScoreResults key={selected.id} run={selected} />}
  </Space>
}
