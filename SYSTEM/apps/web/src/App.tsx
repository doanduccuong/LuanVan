import { useEffect, useMemo, useState } from 'react'
import {
  BarChartOutlined,
  DatabaseOutlined,
  EnvironmentOutlined,
  IdcardOutlined,
  LogoutOutlined,
  ProductOutlined,
  ShoppingCartOutlined,
  TeamOutlined
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  App as AntApp,
  Avatar,
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import ReactECharts from 'echarts-for-react'
import { Navigate, Route, Routes, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  api,
  Category,
  Customer,
  Order,
  Page,
  Product,
  runSimulation,
  SequenceAnalysisRun,
  SequenceAssignment,
  SequenceCluster,
  Touchpoint
} from './api'

const { Header, Sider, Content } = Layout
const money = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
const expressionLabels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
const expressionColors: Record<string, string> = { Angry: '#dc2626', Disgust: '#a16207', Fear: '#9333ea', Happy: '#16a34a', Sad: '#6366f1', Surprise: '#0ea5e9', Neutral: '#64748b' }
const revisionReasons: Record<string, string> = {
  MANUAL_REPROCESS: 'Xử lý lại bằng ảnh mới'
}

function Login() {
  const navigate = useNavigate()
  const { message } = AntApp.useApp()
  const login = useMutation({
    mutationFn: (values: { email: string; password: string }) =>
      api('/auth/login', { method: 'POST', body: JSON.stringify(values) }),
    onSuccess: () => navigate('/dashboard'),
    onError: (error: Error) => message.error(error.message)
  })
  return (
    <main className="login-page">
      <Card className="login-card" bordered={false}>
        <div className="brand-mark">TP</div>
        <Typography.Title level={2}>Touchpoint CRM</Typography.Title>
        <Typography.Paragraph type="secondary">Quản lý khách hàng và chuỗi biểu cảm theo khu vực</Typography.Paragraph>
        <Form layout="vertical" onFinish={login.mutate} initialValues={{ email: 'manager@example.com', password: 'demo1234' }}>
          <Form.Item name="email" label="Email" rules={[{ required: true }]}><Input size="large" /></Form.Item>
          <Form.Item name="password" label="Mật khẩu" rules={[{ required: true }]}><Input.Password size="large" /></Form.Item>
          <Button block size="large" type="primary" htmlType="submit" loading={login.isPending}>Đăng nhập</Button>
        </Form>
      </Card>
    </main>
  )
}

const menuItems = [
  { key: '/dashboard', icon: <BarChartOutlined />, label: 'Tổng quan' },
  { key: '/customers', icon: <TeamOutlined />, label: 'Khách hàng' },
  { key: '/faces', icon: <IdcardOutlined />, label: 'Dữ liệu khuôn mặt' },
  { key: '/products', icon: <ProductOutlined />, label: 'Sản phẩm' },
  { key: '/orders', icon: <ShoppingCartOutlined />, label: 'Mua hàng' },
  { key: '/touchpoints', icon: <EnvironmentOutlined />, label: 'Khu vực' },
  { key: '/visits', icon: <DatabaseOutlined />, label: 'Theo dõi mua sắm' },
  { key: '/reports', icon: <BarChartOutlined />, label: 'Phân tích biểu cảm' }
]

function Shell() {
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: user, isLoading, error } = useQuery({ queryKey: ['me'], queryFn: () => api<{ full_name: string; role: string }>('/auth/me') })
  if (isLoading) return <div className="center-page">Đang tải...</div>
  if (error || !user) return <Navigate to="/login" replace />
  const logout = async () => {
    await api('/auth/logout', { method: 'POST' })
    queryClient.clear()
    navigate('/login')
  }
  return (
    <Layout className="app-shell">
      <Sider width={250} className="sidebar">
        <div className="sidebar-brand"><span className="brand-mark small">TP</span><span>Touchpoint CRM</span></div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={menuItems} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header className="topbar">
          <div />
          <Space><span>{user.full_name}</span><Tag color="cyan">{user.role}</Tag><Button type="text" icon={<LogoutOutlined />} onClick={logout}>Đăng xuất</Button></Space>
        </Header>
        <Content className="content">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/faces" element={<Faces />} />
            <Route path="/products" element={<Products />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/touchpoints" element={<Touchpoints />} />
            <Route path="/visits" element={<Visits />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

function PageTitle({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return <Flex justify="space-between" align="start" className="page-heading"><div><Typography.Title level={2}>{title}</Typography.Title>{description && <Typography.Paragraph type="secondary">{description}</Typography.Paragraph>}</div>{action}</Flex>
}

function Dashboard() {
  const [touchpointId, setTouchpointId] = useState<string>()
  const [bucketMinutes, setBucketMinutes] = useState(15)
  const [timelineDay, setTimelineDay] = useState<string>()
  const customers = useQuery({ queryKey: ['customers', 'summary'], queryFn: () => api<Page<Customer>>('/customers?page_size=1') })
  const products = useQuery({ queryKey: ['products', 'summary'], queryFn: () => api<Page<Product>>('/products?page_size=1') })
  const orders = useQuery({ queryKey: ['orders', 'summary'], queryFn: () => api<Page<Order>>('/orders?page_size=100') })
  const visits = useQuery({ queryKey: ['visits'], queryFn: () => api<any[]>('/visits') })
  const distribution = useQuery({ queryKey: ['distribution'], queryFn: () => api<any[]>('/reports/expression-distribution') })
  const touchpoints = useQuery({ queryKey: ['touchpoints'], queryFn: () => api<Touchpoint[]>('/touchpoints') })
  useEffect(() => {
    if (!touchpointId && touchpoints.data?.length) setTouchpointId(touchpoints.data[0].id)
  }, [touchpointId, touchpoints.data])
  const timeline = useQuery({
    queryKey: ['expression-timeline', touchpointId, bucketMinutes],
    enabled: Boolean(touchpointId),
    queryFn: () => api<any[]>(`/reports/expression-timeline?touchpoint_id=${encodeURIComponent(touchpointId!)}&bucket_minutes=${bucketMinutes}`)
  })
  const chart = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: distribution.data?.map(row => `${row.touchpoint_name}\n${row.label}`) ?? [] },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: distribution.data?.map(row => row.count) ?? [], itemStyle: { color: '#0f766e' } }]
  }), [distribution.data])
  const timelineDays = useMemo(() => [...new Set((timeline.data ?? []).map(row => String(row.bucket_start).slice(0, 10)))].sort(), [timeline.data])
  useEffect(() => {
    if (timelineDays.length && (!timelineDay || !timelineDays.includes(timelineDay))) setTimelineDay(timelineDays[0])
  }, [timelineDay, timelineDays])
  const timelineRows = useMemo(() => (timeline.data ?? []).filter(row => String(row.bucket_start).startsWith(timelineDay ?? '')), [timeline.data, timelineDay])
  const timelineBuckets = useMemo(() => [...new Set(timelineRows.map(row => row.bucket_start))].sort(), [timelineRows])
  const timelineChart = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { top: 50, left: 48, right: 24, bottom: 48 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timelineBuckets.map(value => new Date(value).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }))
    },
    yAxis: { type: 'value', minInterval: 1, name: 'Số quan sát' },
    series: expressionLabels.map(label => ({
      name: label,
      type: 'line',
      stack: 'observations',
      areaStyle: { opacity: 0.13 },
      symbolSize: 7,
      itemStyle: { color: expressionColors[label] },
      data: timelineBuckets.map(bucket => timelineRows.find(row => row.bucket_start === bucket && row.label === label)?.count ?? 0)
    }))
  }), [timelineBuckets, timelineRows])
  const revenue = orders.data?.items.filter(order => order.status !== 'CANCELLED').reduce((sum, order) => sum + Number(order.total_amount), 0) ?? 0
  return <>
    <PageTitle title="Tổng quan" description="Dữ liệu đang được tính trực tiếp từ hệ thống" />
    <Row gutter={[16, 16]}>
      <Col xs={24} md={6}><Card><Statistic title="Khách hàng" value={customers.data?.total ?? 0} /></Card></Col>
      <Col xs={24} md={6}><Card><Statistic title="Sản phẩm" value={products.data?.total ?? 0} /></Card></Col>
      <Col xs={24} md={6}><Card><Statistic title="Lần mua sắm" value={visits.data?.length ?? 0} /></Card></Col>
      <Col xs={24} md={6}><Card><Statistic title="Doanh thu trong dữ liệu tải" value={revenue} formatter={value => money.format(Number(value))} /></Card></Col>
      <Col span={24}><Card><Tabs items={[
        {
          key: 'distribution',
          label: 'Phân bố theo khu vực',
          children: <>{distribution.data?.length ? <ReactECharts option={chart} style={{ height: 360 }} /> : <Empty description="Chưa có quan sát hợp lệ" />}</>
        },
        {
          key: 'timeline',
          label: 'Biến thiên theo thời gian và khu vực',
          children: <>
            <Flex gap={12} align="center" wrap="wrap" className="dashboard-filter-row">
              <Typography.Text strong>Khu vực:</Typography.Text>
              <Select value={touchpointId} onChange={setTouchpointId} className="dashboard-touchpoint-select" options={touchpoints.data?.map(row => ({ value: row.id, label: row.name }))} />
              <Typography.Text strong>Ngày:</Typography.Text>
              <Select value={timelineDay} onChange={setTimelineDay} options={timelineDays.map(value => ({ value, label: new Date(`${value}T00:00:00Z`).toLocaleDateString('vi-VN') }))} />
              <Typography.Text strong>Khoảng thời gian:</Typography.Text>
              <Select value={bucketMinutes} onChange={setBucketMinutes} options={[{ value: 5, label: '5 phút' }, { value: 15, label: '15 phút' }, { value: 30, label: '30 phút' }, { value: 60, label: '60 phút' }]} />
            </Flex>
            <Alert type="info" showIcon message="Biểu đồ nhóm các quan sát theo khu vực và thời gian; nguồn CAMERA hoặc SIMULATOR được lưu riêng trong từng bản ghi." className="dashboard-timeline-note" />
            {timeline.data?.length ? <ReactECharts option={timelineChart} style={{ height: 390 }} /> : <Empty description="Khu vực này chưa có quan sát hợp lệ" />}
          </>
        }
      ]} /></Card></Col>
    </Row>
  </>
}

function Customers() {
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<Customer | null>(null)
  const { message } = AntApp.useApp()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['customers', search], queryFn: () => api<Page<Customer>>(`/customers?page_size=100&search=${encodeURIComponent(search)}`) })
  const orders = useQuery({ queryKey: ['customer-orders', selected?.id], enabled: Boolean(selected), queryFn: () => api<Order[]>(`/customers/${selected!.id}/orders`) })
  const create = useMutation({ mutationFn: (values: any) => api('/customers', { method: 'POST', body: JSON.stringify(values) }), onSuccess: () => { setOpen(false); queryClient.invalidateQueries({ queryKey: ['customers'] }); message.success('Đã tạo khách hàng') }, onError: (e: Error) => message.error(e.message) })
  const columns: ColumnsType<Customer> = [
    { title: 'Ảnh', width: 68, render: (_, row) => <Avatar size={42} src={row.profile_image_url}>{row.full_name.slice(0, 1)}</Avatar> },
    { title: 'Mã', dataIndex: 'customer_code' }, { title: 'Họ tên', dataIndex: 'full_name' }, { title: 'Số điện thoại', dataIndex: 'phone' },
    { title: 'Khuôn mặt', render: (_, row) => <Tag color={row.face_consent ? 'green' : 'default'}>{row.face_consent ? 'Đã đồng ý' : 'Chưa đồng ý'}</Tag> },
    { title: '', render: (_, row) => <Button type="link" onClick={() => setSelected(row)}>Hồ sơ</Button> }
  ]
  return <>
    <PageTitle title="Khách hàng" description="Hồ sơ CRM và lịch sử mua hàng" action={<Button type="primary" onClick={() => setOpen(true)}>Thêm khách hàng</Button>} />
    <Card><Input.Search placeholder="Tìm theo mã, tên hoặc số điện thoại" allowClear onSearch={setSearch} className="table-search" /><Table rowKey="id" loading={query.isLoading} columns={columns} dataSource={query.data?.items} /></Card>
    <Modal title="Thêm khách hàng" open={open} footer={null} onCancel={() => setOpen(false)} destroyOnHidden><Form layout="vertical" onFinish={create.mutate}>
      <Form.Item name="customer_code" label="Mã khách hàng" rules={[{ required: true }]}><Input /></Form.Item>
      <Form.Item name="full_name" label="Họ tên" rules={[{ required: true }]}><Input /></Form.Item>
      <Form.Item name="phone" label="Số điện thoại"><Input /></Form.Item>
      <Form.Item name="email" label="Email"><Input /></Form.Item>
      <Button type="primary" htmlType="submit" loading={create.isPending}>Lưu</Button>
    </Form></Modal>
    <Drawer title={selected?.full_name} width={720} open={Boolean(selected)} onClose={() => setSelected(null)}>
      {selected && <><Flex gap={16} align="center" className="customer-profile"><Avatar size={88} src={selected.profile_image_url}>{selected.full_name.slice(0, 1)}</Avatar><div><Typography.Title level={3}>{selected.full_name}</Typography.Title><Typography.Text type="secondary">{selected.customer_code}</Typography.Text></div></Flex><Descriptions bordered column={1} items={[{ key: 'code', label: 'Mã', children: selected.customer_code }, { key: 'phone', label: 'Điện thoại', children: selected.phone || '—' }, { key: 'email', label: 'Email', children: selected.email || '—' }]} />
      <Typography.Title level={4} className="section-title">Lịch sử mua hàng</Typography.Title><OrderTable orders={orders.data ?? []} loading={orders.isLoading} /></>}
    </Drawer>
  </>
}

function Faces() {
  const { message } = AntApp.useApp()
  const customers = useQuery({ queryKey: ['customers', 'faces'], queryFn: () => api<Page<Customer>>('/customers?page_size=100') })
  const [customerId, setCustomerId] = useState<string>()
  const [searchResult, setSearchResult] = useState<any>()
  const consent = useMutation({ mutationFn: () => api(`/customers/${customerId}/face-consent`, { method: 'PUT', body: JSON.stringify({ consent: true }) }), onSuccess: () => message.success('Đã ghi nhận đồng ý'), onError: (e: Error) => message.error(e.message) })
  const sendFile = async (path: string, file: File) => { const form = new FormData(); form.append('image', file); return api(path, { method: 'POST', body: form }) }
  return <>
    <PageTitle title="Dữ liệu khuôn mặt" description="Đăng ký mẫu và tìm khách hàng bằng ảnh" />
    <Tabs items={[
      { key: 'enroll', label: 'Đăng ký khuôn mặt', children: <Card><Space direction="vertical" size="large" className="full-width"><Select className="wide-select" placeholder="Chọn khách hàng" value={customerId} onChange={setCustomerId} options={customers.data?.items.map(c => ({ value: c.id, label: `${c.customer_code} — ${c.full_name}` }))} /><Space><Button disabled={!customerId} onClick={() => consent.mutate()}>Ghi nhận đồng ý</Button><Upload beforeUpload={async file => { if (!customerId) return false; try { await sendFile(`/customers/${customerId}/face-templates`, file); message.success('Đã tạo mẫu khuôn mặt') } catch (e) { message.error((e as Error).message) } return false }} showUploadList={false}><Button type="primary" disabled={!customerId}>Chọn ảnh đăng ký</Button></Upload></Space></Space></Card> },
      { key: 'search', label: 'Tìm bằng ảnh', children: <Card><Upload beforeUpload={async file => { try { const result = await sendFile('/customers/search-by-face', file); setSearchResult(result) } catch (e) { message.error((e as Error).message) } return false }} showUploadList={false}><Button type="primary">Chọn ảnh cần tìm</Button></Upload>{searchResult && <Alert className="result-alert" type={searchResult.status === 'MATCHED' ? 'success' : 'warning'} message={searchResult.status === 'MATCHED' ? `Tìm thấy: ${searchResult.customer.full_name}` : `Kết quả: ${searchResult.status}`} description={searchResult.distance != null ? `Khoảng cách: ${searchResult.distance.toFixed(4)}` : undefined} />}</Card> }
    ]} />
  </>
}

function Products() {
  const { message } = AntApp.useApp(); const queryClient = useQueryClient(); const [open, setOpen] = useState(false); const [categoryOpen, setCategoryOpen] = useState(false)
  const categories = useQuery({ queryKey: ['categories'], queryFn: () => api<Category[]>('/product-categories') })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api<Page<Product>>('/products?page_size=100') })
  const createCategory = useMutation({ mutationFn: (v: any) => api('/product-categories', { method: 'POST', body: JSON.stringify(v) }), onSuccess: () => { setCategoryOpen(false); queryClient.invalidateQueries({ queryKey: ['categories'] }) }, onError: (e: Error) => message.error(e.message) })
  const createProduct = useMutation({ mutationFn: (v: any) => api('/products', { method: 'POST', body: JSON.stringify(v) }), onSuccess: () => { setOpen(false); queryClient.invalidateQueries({ queryKey: ['products'] }); message.success('Đã tạo sản phẩm') }, onError: (e: Error) => message.error(e.message) })
  const columns: ColumnsType<Product> = [{ title: 'Mã', dataIndex: 'sku' }, { title: 'Tên sản phẩm', dataIndex: 'name' }, { title: 'Nhóm', render: (_, row) => row.category?.name ?? '—' }, { title: 'Giá hiện tại', render: (_, row) => money.format(Number(row.current_price)) }, { title: 'Trạng thái', render: (_, row) => <Tag color={row.status === 'ACTIVE' ? 'green' : 'default'}>{row.status}</Tag> }]
  return <><PageTitle title="Sản phẩm" description="Danh mục sản phẩm sử dụng trong lịch sử mua hàng" action={<Space><Button onClick={() => setCategoryOpen(true)}>Thêm nhóm</Button><Button type="primary" onClick={() => setOpen(true)}>Thêm sản phẩm</Button></Space>} /><Card><Table rowKey="id" loading={products.isLoading} columns={columns} dataSource={products.data?.items} /></Card>
    <Modal title="Thêm nhóm sản phẩm" open={categoryOpen} footer={null} onCancel={() => setCategoryOpen(false)}><Form layout="vertical" onFinish={createCategory.mutate}><Form.Item name="category_code" label="Mã nhóm" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="name" label="Tên nhóm" rules={[{ required: true }]}><Input /></Form.Item><Button type="primary" htmlType="submit">Lưu</Button></Form></Modal>
    <Modal title="Thêm sản phẩm" open={open} footer={null} onCancel={() => setOpen(false)}><Form layout="vertical" onFinish={createProduct.mutate}><Form.Item name="sku" label="Mã sản phẩm" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="name" label="Tên sản phẩm" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="category_id" label="Nhóm" rules={[{ required: true }]}><Select options={categories.data?.map(c => ({ value: c.id, label: c.name }))} /></Form.Item><Form.Item name="current_price" label="Giá hiện tại" rules={[{ required: true }]}><InputNumber min={0} className="full-width" /></Form.Item><Button type="primary" htmlType="submit">Lưu</Button></Form></Modal>
  </>
}

function OrderTable({ orders, loading }: { orders: Order[]; loading?: boolean }) {
  const [selected, setSelected] = useState<Order | null>(null)
  const columns: ColumnsType<Order> = [{ title: 'Mã đơn', dataIndex: 'external_code' }, { title: 'Thời gian', render: (_, row) => new Date(row.ordered_at).toLocaleString('vi-VN') }, { title: 'Tổng tiền', render: (_, row) => money.format(Number(row.total_amount)) }, { title: 'Trạng thái', dataIndex: 'status' }, { title: '', render: (_, row) => <Button type="link" onClick={() => setSelected(row)}>Chi tiết</Button> }]
  return <><Table rowKey="id" pagination={false} loading={loading} columns={columns} dataSource={orders} /><Drawer title={`Đơn ${selected?.external_code ?? ''}`} width={640} open={Boolean(selected)} onClose={() => setSelected(null)}>{selected && <Table rowKey="id" pagination={false} dataSource={selected.items} columns={[{ title: 'Mã', dataIndex: 'product_code_snapshot' }, { title: 'Sản phẩm', dataIndex: 'product_name_snapshot' }, { title: 'SL', dataIndex: 'quantity' }, { title: 'Đơn giá', render: (_, row) => money.format(Number(row.unit_price)) }, { title: 'Thành tiền', render: (_, row) => money.format(Number(row.line_total)) }]} />}</Drawer></>
}

function Orders() {
  const orders = useQuery({ queryKey: ['orders'], queryFn: () => api<Page<Order>>('/orders?page_size=100') })
  return <><PageTitle title="Lịch sử mua hàng" description="Đơn hàng giữ lại tên và giá sản phẩm tại thời điểm mua" /><Card><OrderTable orders={orders.data?.items ?? []} loading={orders.isLoading} /></Card></>
}

function Touchpoints() {
  const { message } = AntApp.useApp(); const queryClient = useQueryClient(); const [open, setOpen] = useState(false)
  const query = useQuery({ queryKey: ['touchpoints'], queryFn: () => api<Touchpoint[]>('/touchpoints') })
  const create = useMutation({ mutationFn: (v: any) => api('/touchpoints', { method: 'POST', body: JSON.stringify(v) }), onSuccess: () => { setOpen(false); queryClient.invalidateQueries({ queryKey: ['touchpoints'] }) }, onError: (e: Error) => message.error(e.message) })
  return <><PageTitle title="Khu vực" description="Danh sách các khu vực được xác định trước trong một cửa hàng" action={<Button type="primary" onClick={() => setOpen(true)}>Thêm khu vực</Button>} /><Card><Table rowKey="id" dataSource={query.data} loading={query.isLoading} columns={[{ title: 'Thứ tự', dataIndex: 'sequence_order' }, { title: 'Mã', dataIndex: 'touchpoint_code' }, { title: 'Tên khu vực', dataIndex: 'name' }, { title: 'Trạng thái', render: (_, row) => <Tag color={row.active ? 'green' : 'default'}>{row.active ? 'Hoạt động' : 'Đã tắt'}</Tag> }]} /></Card><Modal title="Thêm khu vực" open={open} footer={null} onCancel={() => setOpen(false)}><Form layout="vertical" onFinish={create.mutate}><Form.Item name="touchpoint_code" label="Mã" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="name" label="Tên" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="sequence_order" label="Thứ tự" rules={[{ required: true }]}><InputNumber min={0} /></Form.Item><Button type="primary" htmlType="submit">Lưu</Button></Form></Modal></>
}

function Visits() {
  const [searchParams] = useSearchParams()
  const [selected, setSelected] = useState<any>()
  const [selectedObservation, setSelectedObservation] = useState<any>()
  const [simulationResult, setSimulationResult] = useState<any>()
  const { message } = AntApp.useApp()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['visits'], queryFn: () => api<any[]>('/visits') })
  const detail = useQuery({ queryKey: ['visit', selected?.id], enabled: Boolean(selected), queryFn: () => api<any>(`/visits/${selected.id}`) })
  const analysis = useQuery({ queryKey: ['visit-analysis', selected?.id], enabled: Boolean(selected), queryFn: () => api<any>(`/visits/${selected.id}/analysis`) })
  const revisions = useQuery({ queryKey: ['observation-revisions', selectedObservation?.id], enabled: Boolean(selectedObservation), queryFn: () => api<any[]>(`/observations/${selectedObservation.id}/revisions`) })
  const simulate = useMutation({
    mutationFn: () => runSimulation(),
    onSuccess: result => {
      setSimulationResult(result)
      queryClient.invalidateQueries()
      message.success('Đã tạo dữ liệu mô phỏng cho đúng 100 khách hàng')
    },
    onError: (error: Error) => message.error(error.message)
  })
  const reprocess = async (file: File) => {
    const form = new FormData()
    form.append('image', file)
    form.append('reason', 'MANUAL_REPROCESS')
    try {
      const updated = await api<any>(`/observations/${selectedObservation.id}/reprocess`, { method: 'POST', body: form })
      setSelectedObservation({ ...updated, touchpoint: selectedObservation.touchpoint })
      queryClient.invalidateQueries({ queryKey: ['visit', selected?.id] })
      queryClient.invalidateQueries({ queryKey: ['observation-revisions', selectedObservation.id] })
      message.success('Đã xử lý lại; kết quả trước được lưu trong lịch sử')
    } catch (error) { message.error((error as Error).message) }
    return false
  }
  useEffect(() => {
    if (!query.data?.length) return
    const requestedVisit = searchParams.get('visit_id')
    if (requestedVisit && selected?.id !== requestedVisit) {
      const match = query.data.find(row => row.id === requestedVisit)
      if (match) setSelected(match)
      return
    }
    if (!selected) setSelected(query.data[0])
  }, [query.data, searchParams, selected])
  const observations = detail.data?.observations ?? []
  const ordersInVisit = detail.data?.orders ?? []
  const flagMap = Object.fromEntries((analysis.data?.observation_flags ?? []).map((row: any) => [row.observation_id, row.flags]))
  const labelColors: Record<string, string> = { Happy: '#16a34a', Neutral: '#64748b', Surprise: '#0ea5e9', Sad: '#6366f1', Angry: '#dc2626', Fear: '#9333ea', Disgust: '#a16207' }
  const journeyChart = useMemo(() => ({
    tooltip: { trigger: 'item' },
    animationDuration: 500,
    xAxis: { type: 'value', show: false, min: -0.5, max: Math.max(1, observations.length - 0.5) },
    yAxis: { type: 'value', show: false, min: -0.5, max: 0.5 },
    series: [{
      type: 'graph', coordinateSystem: 'cartesian2d', roam: false, symbolSize: 58,
      data: observations.map((item: any, index: number) => ({
        name: `${item.touchpoint?.name}\n${item.expression_label ?? 'Không có nhãn'}`,
        value: [index, 0], x: index, y: 0,
        itemStyle: { color: labelColors[item.expression_label] ?? '#94a3b8' },
        label: { show: true, position: 'bottom', distance: 14, formatter: `${item.touchpoint?.name}\n${item.expression_label ?? 'Không có nhãn'}` }
      })),
      links: observations.slice(1).map((_: any, index: number) => ({ source: index, target: index + 1 })),
      lineStyle: { color: '#94a3b8', width: 3 }, edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 10
    }]
  }), [observations])
  const expressionCounts = observations.reduce((acc: Record<string, number>, item: any) => { const key = item.expression_label ?? 'Không có nhãn'; acc[key] = (acc[key] ?? 0) + 1; return acc }, {})
  const expressionChart = { tooltip: { trigger: 'item' }, legend: { bottom: 0 }, series: [{ type: 'pie', radius: ['42%', '70%'], data: Object.entries(expressionCounts).map(([name, value]) => ({ name, value, itemStyle: { color: labelColors[name] } })) }] }
  const uniqueCustomers = new Set((query.data ?? []).map(row => row.customer_id)).size
  return <>
    <PageTitle title="Theo dõi quá trình mua sắm" description="Xem thứ tự khu vực, biểu cảm và đơn hàng trong từng lần mua sắm" action={<Button type="primary" loading={simulate.isPending} onClick={() => simulate.mutate()}>Tạo dữ liệu mô phỏng</Button>} />
    <Alert showIcon type="info" className="result-alert" message="Nguồn dữ liệu được đánh dấu riêng" description="Quan sát Camera đi qua dịch vụ thị giác; quan sát Simulator chỉ dùng để trình diễn luồng và không được xem là kết quả đánh giá mô hình." />
    {simulationResult && <Alert closable onClose={() => setSimulationResult(undefined)} type="success" className="result-alert" message={`Lần chạy ${simulationResult.run_id}`} description={`100 khách hàng, ${simulationResult.visit_count} lần mua sắm, ${simulationResult.observation_count} quan sát và ${simulationResult.order_count} đơn hàng.`} />}
    <Row gutter={[16, 16]} className="stat-row">
      <Col span={8}><Card><Statistic title="Khách hàng có dữ liệu" value={uniqueCustomers} /></Card></Col>
      <Col span={8}><Card><Statistic title="Lần mua sắm" value={query.data?.length ?? 0} /></Card></Col>
      <Col span={8}><Card><Statistic title="Quan sát trong lần đang xem" value={observations.length} /></Card></Col>
    </Row>
    <Tabs items={[
      { key: 'identified', label: 'Lần mua sắm', children: <Row gutter={[16, 16]}>
        <Col span={9}><Card title="Danh sách lần mua sắm"><Table size="small" pagination={{ pageSize: 8 }} rowKey="id" rowClassName={row => row.id === selected?.id ? 'selected-row' : ''} onRow={row => ({ onClick: () => setSelected(row) })} dataSource={query.data} loading={query.isLoading} columns={[{ title: 'Khách hàng', render: (_, row) => <Space><Avatar size={30} src={row.customer?.profile_image_url} />{row.customer?.full_name}</Space> }, { title: 'Thời gian', render: (_, row) => new Date(row.started_at).toLocaleDateString('vi-VN') }, { title: 'Trạng thái', render: (_, row) => <Tag color={row.status === 'CLOSED' ? 'green' : 'blue'}>{row.status === 'CLOSED' ? 'Đã kết thúc' : 'Đang hoạt động'}</Tag> }]} /></Card></Col>
        <Col span={15}><Card title={selected ? `${selected.customer?.full_name} — ${new Date(selected.started_at).toLocaleString('vi-VN')}` : 'Chọn một lần mua sắm'}>
          {(analysis.data?.missing_touchpoints ?? []).length > 0 && <Alert type="warning" showIcon message={`Thiếu dữ liệu tại: ${analysis.data.missing_touchpoints.map((row: any) => row.name).join(', ')}`} />}
          {observations.length ? <ReactECharts option={journeyChart} style={{ height: 310 }} /> : <Empty description="Chưa có dữ liệu" />}
        </Card></Col>
        <Col span={15} offset={9}><Row gutter={16}><Col span={14}><Card title="Chi tiết theo thời gian">{observations.map((item: any) => <Card size="small" className="timeline-card observation-card" key={item.id} onClick={() => setSelectedObservation(item)}><Flex justify="space-between"><strong>{item.touchpoint?.name}</strong><span>{new Date(item.observed_at).toLocaleTimeString('vi-VN')}</span></Flex><Space wrap><Tag color={labelColors[item.expression_label] ?? 'default'}>{item.expression_label ?? 'Không có nhãn'}</Tag><Tag>{item.source_type === 'SIMULATOR' ? 'Mô phỏng' : 'Camera'}</Tag><span>{item.expression_confidence != null ? `${(Number(item.expression_confidence) * 100).toFixed(1)}%` : '—'}</span>{(flagMap[item.id] ?? []).map((flag: string) => <Tag color="warning" key={flag}>{flag}</Tag>)}</Space></Card>)}</Card></Col><Col span={10}><Space direction="vertical" size={16} className="full-width"><Card title="Phân bố nhãn trong lần"><ReactECharts option={expressionChart} style={{ height: 280 }} /></Card><Card title="Đơn hàng liên quan">{ordersInVisit.length ? <OrderTable orders={ordersInVisit} /> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Không phát sinh đơn hàng" />}</Card></Space></Col></Row></Col>
      </Row> },
    ]} />
    <Drawer title="Chi tiết bản ghi quan sát" width={680} open={Boolean(selectedObservation)} onClose={() => setSelectedObservation(undefined)}>
      {selectedObservation && <Space direction="vertical" size="large" className="full-width">
        <Descriptions bordered column={1} items={[
          { key: 'event-id', label: 'Mã sự kiện', children: selectedObservation.event_id },
          { key: 'face-index', label: 'Khuôn mặt trong ảnh', children: Number(selectedObservation.face_index) + 1 },
          { key: 'time', label: 'Thời gian ghi nhận', children: new Date(selectedObservation.observed_at).toLocaleString('vi-VN') },
          { key: 'area', label: 'Khu vực', children: selectedObservation.touchpoint?.name ?? selectedObservation.touchpoint_id },
          { key: 'box', label: 'Khung bao', children: selectedObservation.bounding_box?.map((value: number) => Math.round(value)).join(', ') ?? '—' },
          { key: 'detection-score', label: 'Tin cậy phát hiện', children: selectedObservation.detection_score != null ? `${(Number(selectedObservation.detection_score) * 100).toFixed(1)}%` : '—' },
          { key: 'expression', label: 'Biểu cảm', children: selectedObservation.expression_label ?? 'Không có kết quả' },
          { key: 'confidence', label: 'Mức tin cậy', children: selectedObservation.expression_confidence != null ? `${(Number(selectedObservation.expression_confidence) * 100).toFixed(2)}%` : '—' },
          { key: 'image-status', label: 'Trạng thái ảnh', children: selectedObservation.image_status },
          { key: 'expression-status', label: 'Trạng thái phân loại', children: selectedObservation.expression_status },
          { key: 'identity-status', label: 'Trạng thái nhận dạng', children: selectedObservation.identity_status },
          { key: 'models', label: 'Mô hình', children: <>{selectedObservation.detector_version ?? '—'}<br />{selectedObservation.emotion_model_version ?? '—'}<br />{selectedObservation.recognition_model_version ?? '—'}</> }
        ]} />
        <Card title="Xử lý lại và lịch sử thay đổi"><Upload beforeUpload={reprocess} showUploadList={false}><Button>Chọn ảnh để xử lý lại</Button></Upload><Table className="revision-table" size="small" pagination={false} rowKey="id" dataSource={revisions.data} columns={[{ title: 'Lần', dataIndex: 'revision_number' }, { title: 'Lý do', render: (_, row) => revisionReasons[row.reason] ?? row.reason }, { title: 'Kết quả trước', render: (_, row) => `${row.snapshot.expression_label ?? '—'} / ${row.snapshot.identity_status}` }, { title: 'Thời gian', render: (_, row) => new Date(row.created_at).toLocaleString('vi-VN') }]} /></Card>
      </Space>}
    </Drawer>
  </>
}

function ExpressionSequence({ sequence }: { sequence: string[] }) {
  if (!sequence?.length) return <Typography.Text type="secondary">Không có chuỗi</Typography.Text>
  return <Flex gap={5} wrap="wrap" align="center" className="sequence-strip">
    {sequence.map((label, index) => <span className="sequence-state" key={`${label}-${index}`}>
      {index > 0 && <span className="sequence-arrow">→</span>}
      <Tag color={expressionColors[label] ?? 'default'}>{label}</Tag>
    </span>)}
  </Flex>
}

function SequenceAnalysisPanel() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { message } = AntApp.useApp()
  const [form] = Form.useForm()
  const [selectedRunId, setSelectedRunId] = useState<string>()
  const [clusterFilter, setClusterFilter] = useState<number>()
  const runs = useQuery({
    queryKey: ['sequence-analyses'],
    queryFn: () => api<SequenceAnalysisRun[]>('/sequence-analyses')
  })
  useEffect(() => {
    if (!selectedRunId && runs.data?.length) setSelectedRunId(runs.data[0].id)
  }, [runs.data, selectedRunId])
  const run = useQuery({
    queryKey: ['sequence-analysis', selectedRunId],
    enabled: Boolean(selectedRunId),
    queryFn: () => api<SequenceAnalysisRun>(`/sequence-analyses/${selectedRunId}`)
  })
  const clusters = useQuery({
    queryKey: ['sequence-clusters', selectedRunId],
    enabled: Boolean(selectedRunId && run.data?.status === 'COMPLETED'),
    queryFn: () => api<SequenceCluster[]>(`/sequence-analyses/${selectedRunId}/clusters`)
  })
  const assignments = useQuery({
    queryKey: ['sequence-assignments', selectedRunId, clusterFilter],
    enabled: Boolean(selectedRunId && run.data?.status === 'COMPLETED'),
    queryFn: () => api<Page<SequenceAssignment>>(`/sequence-analyses/${selectedRunId}/assignments?page_size=200${clusterFilter ? `&cluster_id=${clusterFilter}` : ''}`)
  })
  const create = useMutation({
    mutationFn: (values: any) => api<SequenceAnalysisRun>('/sequence-analyses', {
      method: 'POST',
      body: JSON.stringify({ ...values, k_max: values.k_max || undefined })
    }),
    onSuccess: result => {
      setSelectedRunId(result.id)
      setClusterFilter(undefined)
      queryClient.invalidateQueries({ queryKey: ['sequence-analyses'] })
      queryClient.setQueryData(['sequence-analysis', result.id], result)
      message.success(`Đã phân cụm ${result.used_visit_count} chuỗi thành ${result.selected_k} cụm`)
    },
    onError: (error: Error) => message.error(error.message)
  })
  const renameCluster = useMutation({
    mutationFn: ({ clusterId, displayName }: { clusterId: number; displayName?: string }) =>
      api<SequenceCluster>(`/sequence-analyses/${selectedRunId}/clusters/${clusterId}`, {
        method: 'PATCH', body: JSON.stringify({ display_name: displayName || null })
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sequence-clusters', selectedRunId] })
      message.success('Đã lưu tên diễn giải của cụm')
    },
    onError: (error: Error) => message.error(error.message)
  })
  const aswChart = useMemo(() => ({
    tooltip: { trigger: 'axis' },
    grid: { top: 30, left: 52, right: 24, bottom: 48 },
    xAxis: { type: 'category', name: 'Số cụm K', data: (run.data?.candidate_metrics ?? []).map(row => `K=${row.k}`) },
    yAxis: { type: 'value', name: 'ASW', min: -1, max: 1 },
    series: [{
      type: 'line',
      smooth: false,
      symbolSize: 11,
      data: (run.data?.candidate_metrics ?? []).map(row => ({
        value: row.asw,
        itemStyle: { color: row.accepted ? (row.k === run.data?.selected_k ? '#0f766e' : '#64748b') : '#dc2626' },
        label: { show: row.k === run.data?.selected_k, position: 'top', formatter: 'Được chọn' }
      }))
    }]
  }), [run.data])
  const statusColor: Record<string, string> = { COMPLETED: 'green', RUNNING: 'blue', FAILED: 'red' }
  const runOptions = (runs.data ?? []).map(item => ({
    value: item.id,
    label: `${new Date(item.created_at).toLocaleString('vi-VN')} · ${item.source_type}/${item.source_run_id} · ${item.status}`
  }))
  const clusterOptions = (clusters.data ?? []).map(item => ({
    value: item.cluster_id,
    label: item.display_name || `Cụm ${item.cluster_id}`
  }))
  return <Space direction="vertical" size={16} className="full-width">
    <Alert
      showIcon
      type="info"
      message="Đầu ra là các kiểu diễn biến biểu cảm tương tự"
      description="Hệ thống dùng nhãn biểu cảm dự đoán theo thứ tự điểm chạm, tính khoảng cách Optimal Matching rồi dùng PAM để tạo cụm. Mỗi cụm có một medoid là chuỗi thật đại diện. Cụm không tự động có nghĩa là hài lòng hoặc không hài lòng; tên diễn giải phải dựa trên chuỗi đại diện và dữ liệu đối chứng nếu có."
    />
    <Card title="Tạo lần phân tích">
      <Form form={form} layout="vertical" initialValues={{ source_type: 'CAMERA', min_states: 3, min_cluster_size_abs: 2, min_cluster_ratio: 0.05, k_min: 2, asw_tolerance: 0.02, random_state: 42 }} onFinish={create.mutate}>
        <Row gutter={16}>
          <Col xs={24} md={6}><Form.Item name="source_type" label="Nguồn dữ liệu" rules={[{ required: true }]}><Select options={[{ value: 'CAMERA', label: 'Camera/KDEF' }, { value: 'SIMULATOR', label: 'Mô phỏng có kiểm soát' }]} /></Form.Item></Col>
          <Col xs={24} md={10}><Form.Item name="source_run_id" label="Mã lần phát dữ liệu" rules={[{ required: true, message: 'Nhập mã lần phát dữ liệu' }]}><Input placeholder="Ví dụ: kdef-20261008-..." /></Form.Item></Col>
          <Col xs={12} md={4}><Form.Item name="k_max" label="K tối đa (tùy chọn)"><InputNumber min={2} className="full-width" /></Form.Item></Col>
          <Col xs={12} md={4}><Form.Item label=" "><Button block type="primary" htmlType="submit" loading={create.isPending}>Chạy phân tích</Button></Form.Item></Col>
        </Row>
      </Form>
    </Card>
    <Card title="Kết quả đã lưu">
      <Select
        className="sequence-run-select"
        placeholder="Chọn một lần phân tích"
        loading={runs.isLoading}
        value={selectedRunId}
        options={runOptions}
        onChange={value => { setSelectedRunId(value); setClusterFilter(undefined) }}
      />
      {runs.isError && <Alert className="result-alert" type="error" showIcon message="Không tải được lịch sử phân tích" description={(runs.error as Error).message} />}
      {!runs.isLoading && !runs.data?.length && <Empty description="Chưa có lần phân tích nào" />}
    </Card>
    {run.isError && <Alert type="error" showIcon message="Không tải được kết quả" description={(run.error as Error).message} />}
    {run.data && <>
      <Flex gap={8} wrap="wrap" align="center">
        <Tag color={statusColor[run.data.status]}>{run.data.status}</Tag>
        <Typography.Text type="secondary">Nguồn: {run.data.source_type} / {run.data.source_run_id}</Typography.Text>
        <Typography.Text type="secondary">Thuật toán: {run.data.algorithm_version}</Typography.Text>
      </Flex>
      {run.data.status === 'FAILED' && <Alert type="error" showIcon message="Lần phân tích thất bại" description={run.data.error_detail} />}
      {run.data.status === 'COMPLETED' && <>
        <Row gutter={[16, 16]}>
          <Col xs={12} lg={6}><Card><Statistic title="Chuỗi hợp lệ" value={run.data.used_visit_count} /></Card></Col>
          <Col xs={12} lg={6}><Card><Statistic title="Chuỗi bị loại" value={run.data.excluded_visit_count} /></Card></Col>
          <Col xs={12} lg={6}><Card><Statistic title="Số cụm được chọn" value={run.data.selected_k ?? '—'} prefix="K=" /></Card></Col>
          <Col xs={12} lg={6}><Card><Statistic title="Average Silhouette Width" value={run.data.average_silhouette_width ?? 0} precision={3} /></Card></Col>
        </Row>
        <Card title="Chọn số cụm bằng Average Silhouette Width" extra={<Typography.Text type="secondary">Điểm cao hơn cho thấy các chuỗi gần cụm của mình hơn các cụm khác</Typography.Text>}>
          {(run.data.candidate_metrics ?? []).length ? <ReactECharts option={aswChart} style={{ height: 330 }} /> : <Empty description="Không có phương án K" />}
          <Table
            size="small"
            pagination={false}
            rowKey="k"
            dataSource={run.data.candidate_metrics}
            columns={[
              { title: 'K', dataIndex: 'k' },
              { title: 'ASW', render: (_, row) => Number(row.asw).toFixed(3) },
              { title: 'Cụm nhỏ nhất', dataIndex: 'min_cluster_size' },
              { title: 'Ngưỡng tối thiểu', dataIndex: 'required_min_cluster_size' },
              { title: 'Hợp lệ', render: (_, row) => <Tag color={row.accepted ? 'green' : 'red'}>{row.accepted ? 'Có' : 'Không'}</Tag> },
              { title: 'Quyết định', render: (_, row) => row.k === run.data?.selected_k ? <Tag color="cyan">Được chọn</Tag> : '—' }
            ]}
          />
        </Card>
        <section className="cluster-summary-section">
          <Typography.Title level={4} className="section-title">Cụm và chuỗi đại diện (medoid)</Typography.Title>
          <Row gutter={[16, 16]}>
            {(clusters.data ?? []).map(cluster => <Col xs={24} lg={12} key={cluster.id}>
            <Card
              className={clusterFilter === cluster.cluster_id ? 'cluster-card cluster-card-selected' : 'cluster-card'}
              title={cluster.display_name || `Cụm ${cluster.cluster_id}`}
              extra={<Button type="link" onClick={() => setClusterFilter(cluster.cluster_id)}>Xem {cluster.size} chuỗi</Button>}
            >
              <ExpressionSequence sequence={cluster.medoid_sequence} />
              <Descriptions size="small" column={2} className="cluster-metrics" items={[
                { key: 'size', label: 'Số chuỗi', children: cluster.size },
                { key: 'proportion', label: 'Tỷ lệ', children: `${(cluster.proportion * 100).toFixed(1)}%` },
                { key: 'silhouette', label: 'Silhouette TB', children: cluster.mean_silhouette.toFixed(3) },
                { key: 'distance', label: 'Khoảng cách trung vị', children: cluster.median_distance.toFixed(3) }
              ]} />
              <Form layout="inline" className="cluster-name-form" initialValues={{ displayName: cluster.display_name ?? '' }} onFinish={({ displayName }) => renameCluster.mutate({ clusterId: cluster.cluster_id, displayName })}>
                <Form.Item name="displayName"><Input placeholder="Tên diễn giải sau khi xem medoid" /></Form.Item>
                <Button htmlType="submit" loading={renameCluster.isPending}>Lưu tên</Button>
              </Form>
            </Card>
            </Col>)}
          </Row>
        </section>
        <Card
          title="Các lượt mua sắm trong cụm"
          extra={<Space><Select allowClear placeholder="Tất cả cụm" value={clusterFilter} options={clusterOptions} onChange={setClusterFilter} className="cluster-filter" /><Button disabled={!clusterFilter} onClick={() => setClusterFilter(undefined)}>Bỏ lọc</Button></Space>}
        >
          <Table
            rowKey="id"
            loading={assignments.isLoading}
            dataSource={assignments.data?.items}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 900 }}
            columns={[
              { title: 'Khách hàng', render: (_, row) => row.customer ? `${row.customer.customer_code} — ${row.customer.full_name}` : '—' },
              { title: 'Thời gian', render: (_, row) => row.visit_started_at ? new Date(row.visit_started_at).toLocaleString('vi-VN') : '—' },
              { title: 'Chuỗi dự đoán', width: 390, render: (_, row) => <ExpressionSequence sequence={row.sequence} /> },
              { title: 'Cụm', render: (_, row) => clusterOptions.find(item => item.value === row.cluster_id)?.label ?? `Cụm ${row.cluster_id}` },
              { title: 'Khoảng cách tới medoid', render: (_, row) => row.distance_to_medoid.toFixed(3) },
              { title: 'Silhouette', render: (_, row) => row.silhouette.toFixed(3) },
              { title: '', fixed: 'right', render: (_, row) => <Button type="link" onClick={() => navigate(`/visits?visit_id=${row.visit_id}`)}>Xem hành trình</Button> }
            ]}
          />
        </Card>
        {!!run.data.warnings?.length && <Alert type="warning" showIcon message="Cảnh báo tiền xử lý" description={<ul>{run.data.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul>} />}
      </>}
    </>}
  </Space>
}

function Reports() {
  const [activeTab, setActiveTab] = useState('distribution')
  const [touchpointId, setTouchpointId] = useState<string>()
  const [timeRange, setTimeRange] = useState<any>(null)
  const [representative, setRepresentative] = useState('highest_confidence')
  const periodQuery = timeRange?.[0] && timeRange?.[1] ? `&from=${encodeURIComponent(timeRange[0].toISOString())}&to=${encodeURIComponent(timeRange[1].toISOString())}` : ''
  const areaQuery = touchpointId ? `&touchpoint_id=${encodeURIComponent(touchpointId)}` : ''
  const distribution = useQuery({ queryKey: ['distribution', touchpointId, periodQuery], queryFn: () => api<any[]>(`/reports/expression-distribution?${areaQuery.replace(/^&/, '')}${periodQuery}`) })
  const changes = useQuery({ queryKey: ['changes', representative, periodQuery], queryFn: () => api<any[]>(`/reports/expression-changes?representative=${representative}${periodQuery}`) })
  const quality = useQuery({ queryKey: ['quality-summary', touchpointId, periodQuery], queryFn: () => api<any>(`/reports/data-quality-summary?${areaQuery.replace(/^&/, '')}${periodQuery}`) })
  const touchpoints = useQuery({ queryKey: ['touchpoints'], queryFn: () => api<Touchpoint[]>('/touchpoints') })
  const labels = expressionLabels
  const touchpointNames = Object.fromEntries((touchpoints.data ?? []).map(row => [row.id, row.name]))
  const distributionChart = useMemo(() => ({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, legend: { top: 0 }, grid: { top: 48, left: 48, right: 20, bottom: 70 },
    xAxis: { type: 'category', data: (touchpoints.data ?? []).map(row => row.name), axisLabel: { rotate: 15 } }, yAxis: { type: 'value', minInterval: 1 },
    series: labels.map(label => ({ name: label, type: 'bar', stack: 'count', data: (touchpoints.data ?? []).map(tp => distribution.data?.find(row => row.touchpoint_id === tp.id && row.label === label)?.count ?? 0) }))
  }), [distribution.data, touchpoints.data])
  const changeChart = useMemo(() => {
    const nodes = new Map<string, { name: string }>()
    const links = (changes.data ?? []).map(row => {
      const source = `${touchpointNames[row.from_touchpoint_id] ?? row.from_touchpoint_id}: ${row.from_label}`
      const target = `${touchpointNames[row.to_touchpoint_id] ?? row.to_touchpoint_id}: ${row.to_label}`
      nodes.set(source, { name: source }); nodes.set(target, { name: target })
      return { source, target, value: row.count }
    })
    return { tooltip: { trigger: 'item' }, series: [{ type: 'sankey', data: [...nodes.values()], links, emphasis: { focus: 'adjacency' }, lineStyle: { color: 'gradient', curveness: 0.5 } }] }
  }, [changes.data, touchpoints.data])
  const qualityChart = useMemo(() => ({ tooltip: { trigger: 'item' }, legend: { bottom: 0 }, series: [{ type: 'pie', radius: ['38%', '70%'], data: (quality.data?.statuses ?? []).map((row: any) => ({ name: `${row.image_status} / ${row.expression_status}`, value: row.count })) }] }), [quality.data])
  const reportFilters = <Card size="small" className="report-filter-card"><Flex gap={12} wrap="wrap" align="center"><strong>Phạm vi:</strong><Select allowClear placeholder="Tất cả khu vực" value={touchpointId} onChange={setTouchpointId} options={touchpoints.data?.map(row => ({ value: row.id, label: row.name }))} className="report-area-select" /><DatePicker.RangePicker showTime onChange={setTimeRange} /></Flex></Card>
  return <><PageTitle title="Phân tích biểu cảm" description="Thống kê bảy nhãn biểu cảm theo khu vực và phân cụm chuỗi theo hành trình" />{activeTab !== 'sequence' && reportFilters}<Tabs activeKey={activeTab} onChange={setActiveTab} items={[
    { key: 'distribution', label: 'Phân bố tại khu vực', children: <><Card title="Số quan sát theo khu vực và nhãn"><ReactECharts option={distributionChart} style={{ height: 430 }} /></Card><Card className="table-card"><Table rowKey={row => `${row.touchpoint_id}-${row.label}`} dataSource={distribution.data} columns={[{ title: 'Khu vực', dataIndex: 'touchpoint_name' }, { title: 'Nhãn', dataIndex: 'label' }, { title: 'Số quan sát', dataIndex: 'count' }, { title: 'Tỷ lệ trong khu vực', render: (_, row) => `${(row.percentage * 100).toFixed(1)}%` }]} /></Card></> },
    { key: 'changes', label: 'Thay đổi giữa các khu vực', children: <><Card size="small" className="change-method"><Space><strong>Cách chọn bản ghi đại diện khi có nhiều ảnh liên tiếp tại cùng khu vực:</strong><Select value={representative} onChange={setRepresentative} options={[{ value: 'highest_confidence', label: 'Mức tin cậy cao nhất' }, { value: 'first', label: 'Bản ghi đầu tiên' }, { value: 'last', label: 'Bản ghi cuối cùng' }]} /></Space></Card><Card title="Luồng thay đổi nhãn giữa hai khu vực liên tiếp"><ReactECharts option={changeChart} style={{ height: 520 }} /></Card><Card className="table-card"><Table rowKey={(_, index) => String(index)} dataSource={changes.data} columns={[{ title: 'Khu vực trước', render: (_, row) => touchpointNames[row.from_touchpoint_id] ?? row.from_touchpoint_id }, { title: 'Khu vực sau', render: (_, row) => touchpointNames[row.to_touchpoint_id] ?? row.to_touchpoint_id }, { title: 'Nhãn trước', dataIndex: 'from_label' }, { title: 'Nhãn sau', dataIndex: 'to_label' }, { title: 'Số lần', dataIndex: 'count' }, { title: 'Tỷ lệ trong cặp khu vực', render: (_, row) => `${(row.percentage * 100).toFixed(1)}%` }]} /></Card></> },
    { key: 'quality', label: 'Chất lượng dữ liệu', children: <><Row gutter={[16, 16]} className="quality-stat-row"><Col xs={12} lg={6}><Card><Statistic title="Khung hình / khuôn mặt" value={`${quality.data?.summary?.capture_events ?? 0} / ${quality.data?.summary?.observations ?? 0}`} /></Card></Col><Col xs={12} lg={6}><Card><Statistic title="Khung hình đến chậm" value={quality.data?.summary?.late_arrivals ?? 0} /></Card></Col><Col xs={12} lg={6}><Card><Statistic title="Xung đột thời gian" value={quality.data?.summary?.time_conflicts ?? 0} /></Card></Col><Col xs={12} lg={6}><Card><Statistic title="Khu vực bị thiếu" value={quality.data?.summary?.missing_touchpoints ?? 0} /></Card></Col></Row><Row gutter={[16, 16]}><Col xs={24} xl={14}><Card title="Tỷ lệ trạng thái xử lý"><ReactECharts option={qualityChart} style={{ height: 410 }} /></Card></Col><Col xs={24} xl={10}><Space direction="vertical" className="full-width"><Card title="Chi tiết trạng thái"><Table pagination={false} rowKey={(_, index) => String(index)} dataSource={quality.data?.statuses} columns={[{ title: 'Ảnh', dataIndex: 'image_status' }, { title: 'Biểu cảm', dataIndex: 'expression_status' }, { title: 'Danh tính', dataIndex: 'identity_status' }, { title: 'Số sự kiện/quan sát', dataIndex: 'count' }]} /></Card><Card title="Yêu cầu đầu vào không hợp lệ"><Table pagination={false} rowKey="issue_code" dataSource={quality.data?.ingestion_issues} columns={[{ title: 'Lỗi', dataIndex: 'issue_code' }, { title: 'Số yêu cầu', dataIndex: 'count' }]} /></Card></Space></Col></Row></> },
    { key: 'sequence', label: 'Phân cụm chuỗi', children: <SequenceAnalysisPanel /> }
  ]} /></>
}

export default function App() {
  return <AntApp><Routes><Route path="/login" element={<Login />} /><Route path="/*" element={<Shell />} /></Routes></AntApp>
}
