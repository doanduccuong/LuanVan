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
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { api, Category, Customer, Order, Page, Product, runSimulation, Touchpoint } from './api'

const { Header, Sider, Content } = Layout
const money = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' })
const expressionLabels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
const expressionColors: Record<string, string> = { Angry: '#dc2626', Disgust: '#a16207', Fear: '#9333ea', Happy: '#16a34a', Sad: '#6366f1', Surprise: '#0ea5e9', Neutral: '#64748b' }

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
        <Typography.Paragraph type="secondary">Quản lý khách hàng và hành trình biểu cảm tại điểm chạm</Typography.Paragraph>
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
  { key: '/touchpoints', icon: <EnvironmentOutlined />, label: 'Điểm chạm' },
  { key: '/visits', icon: <DatabaseOutlined />, label: 'Theo dõi hành trình' },
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
      <Col xs={24} md={6}><Card><Statistic title="Lượt ghé thăm" value={visits.data?.length ?? 0} /></Card></Col>
      <Col xs={24} md={6}><Card><Statistic title="Doanh thu trong dữ liệu tải" value={revenue} formatter={value => money.format(Number(value))} /></Card></Col>
      <Col span={24}><Card><Tabs items={[
        {
          key: 'distribution',
          label: 'Phân bố theo điểm chạm',
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
            <Alert type="info" showIcon message="Biểu đồ nhóm các quan sát trong cùng khu vực theo từng khoảng thời gian; dữ liệu hiện tại do dịch vụ mô phỏng tạo." className="dashboard-timeline-note" />
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
  return <><PageTitle title="Điểm chạm" description="Hệ thống chỉ phục vụ một cửa hàng" action={<Button type="primary" onClick={() => setOpen(true)}>Thêm điểm chạm</Button>} /><Card><Table rowKey="id" dataSource={query.data} loading={query.isLoading} columns={[{ title: 'Thứ tự', dataIndex: 'sequence_order' }, { title: 'Mã', dataIndex: 'touchpoint_code' }, { title: 'Tên điểm chạm', dataIndex: 'name' }, { title: 'Trạng thái', render: (_, row) => <Tag color={row.active ? 'green' : 'default'}>{row.active ? 'Hoạt động' : 'Đã tắt'}</Tag> }]} /></Card><Modal title="Thêm điểm chạm" open={open} footer={null} onCancel={() => setOpen(false)}><Form layout="vertical" onFinish={create.mutate}><Form.Item name="touchpoint_code" label="Mã" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="name" label="Tên" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="sequence_order" label="Thứ tự" rules={[{ required: true }]}><InputNumber min={0} /></Form.Item><Button type="primary" htmlType="submit">Lưu</Button></Form></Modal></>
}

function Visits() {
  const [selected, setSelected] = useState<any>()
  const [simulationResult, setSimulationResult] = useState<any>()
  const { message } = AntApp.useApp()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['visits'], queryFn: () => api<any[]>('/visits') })
  const detail = useQuery({ queryKey: ['visit', selected?.id], enabled: Boolean(selected), queryFn: () => api<any>(`/visits/${selected.id}`) })
  const simulate = useMutation({
    mutationFn: () => runSimulation(),
    onSuccess: result => {
      setSimulationResult(result)
      queryClient.invalidateQueries()
      message.success('Đã tạo dữ liệu mô phỏng cho đúng 100 khách hàng')
    },
    onError: (error: Error) => message.error(error.message)
  })
  useEffect(() => {
    if (!selected && query.data?.length) setSelected(query.data[0])
  }, [query.data, selected])
  const observations = detail.data?.observations ?? []
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
    <PageTitle title="Theo dõi hành trình khách hàng" description="Quan sát thứ tự điểm chạm và nhãn biểu cảm của từng lượt ghé thăm" action={<Button type="primary" loading={simulate.isPending} onClick={() => simulate.mutate()}>Tạo dữ liệu mô phỏng</Button>} />
    <Alert showIcon type="info" className="result-alert" message="Dữ liệu mô phỏng được đánh dấu riêng" description="Nhãn biểu cảm do dịch vụ mô phỏng tạo để trình diễn luồng hệ thống, không phải kết quả đánh giá mô hình nhận dạng." />
    {simulationResult && <Alert closable onClose={() => setSimulationResult(undefined)} type="success" className="result-alert" message={`Lần chạy ${simulationResult.run_id}`} description={`100 khách hàng, ${simulationResult.visit_count} lượt ghé thăm, ${simulationResult.observation_count} quan sát và ${simulationResult.order_count} đơn hàng.`} />}
    <Row gutter={[16, 16]} className="stat-row">
      <Col span={8}><Card><Statistic title="Khách hàng có hành trình" value={uniqueCustomers} /></Card></Col>
      <Col span={8}><Card><Statistic title="Lượt ghé thăm" value={query.data?.length ?? 0} /></Card></Col>
      <Col span={8}><Card><Statistic title="Điểm chạm trong hành trình đang xem" value={observations.length} /></Card></Col>
    </Row>
    <Row gutter={[16, 16]}>
      <Col span={9}><Card title="Danh sách lượt ghé thăm"><Table size="small" pagination={{ pageSize: 8 }} rowKey="id" rowClassName={row => row.id === selected?.id ? 'selected-row' : ''} onRow={row => ({ onClick: () => setSelected(row) })} dataSource={query.data} loading={query.isLoading} columns={[{ title: 'Khách hàng', render: (_, row) => <Space><Avatar size={30} src={row.customer?.profile_image_url} />{row.customer?.full_name}</Space> }, { title: 'Thời gian', render: (_, row) => new Date(row.started_at).toLocaleDateString('vi-VN') }, { title: 'Trạng thái', render: (_, row) => <Tag color={row.status === 'CLOSED' ? 'green' : 'blue'}>{row.status}</Tag> }]} /></Card></Col>
      <Col span={15}><Card title={selected ? `${selected.customer?.full_name} — ${new Date(selected.started_at).toLocaleString('vi-VN')}` : 'Chọn một lượt ghé thăm'}>{observations.length ? <ReactECharts option={journeyChart} style={{ height: 310 }} /> : <Empty description="Chưa có dữ liệu hành trình" />}</Card></Col>
      <Col span={15} offset={9}><Row gutter={16}><Col span={14}><Card title="Chi tiết theo thời gian">{observations.map((item: any) => <Card size="small" className="timeline-card" key={item.id}><Flex justify="space-between"><strong>{item.touchpoint?.name}</strong><span>{new Date(item.observed_at).toLocaleTimeString('vi-VN')}</span></Flex><Space><Tag color={labelColors[item.expression_label] ?? 'default'}>{item.expression_label ?? 'Không có nhãn'}</Tag><Tag>{item.source_type === 'SIMULATOR' ? 'Mô phỏng' : 'Camera'}</Tag><span>{item.expression_confidence != null ? `${(Number(item.expression_confidence) * 100).toFixed(1)}%` : '—'}</span></Space></Card>)}</Card></Col><Col span={10}><Card title="Phân bố nhãn trong lượt"><ReactECharts option={expressionChart} style={{ height: 300 }} /></Card></Col></Row></Col>
    </Row>
  </>
}

function Reports() {
  const distribution = useQuery({ queryKey: ['distribution'], queryFn: () => api<any[]>('/reports/expression-distribution') })
  const changes = useQuery({ queryKey: ['changes'], queryFn: () => api<any[]>('/reports/expression-changes') })
  const quality = useQuery({ queryKey: ['quality'], queryFn: () => api<any[]>('/reports/data-quality') })
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
  const qualityChart = useMemo(() => ({ tooltip: { trigger: 'item' }, legend: { bottom: 0 }, series: [{ type: 'pie', radius: ['38%', '70%'], data: (quality.data ?? []).map(row => ({ name: `${row.image_status} / ${row.expression_status}`, value: row.count })) }] }), [quality.data])
  return <><PageTitle title="Phân tích biểu cảm" description="Kết quả mô tả nhãn quan sát được, không phải điểm hài lòng" /><Tabs items={[
    { key: 'distribution', label: 'Phân bố tại điểm chạm', children: <><Card title="Số quan sát theo điểm chạm và nhãn"><ReactECharts option={distributionChart} style={{ height: 430 }} /></Card><Card className="table-card"><Table rowKey={row => `${row.touchpoint_id}-${row.label}`} dataSource={distribution.data} columns={[{ title: 'Điểm chạm', dataIndex: 'touchpoint_name' }, { title: 'Nhãn', dataIndex: 'label' }, { title: 'Số quan sát', dataIndex: 'count' }, { title: 'Tỷ lệ trong điểm chạm', render: (_, row) => `${(row.percentage * 100).toFixed(1)}%` }]} /></Card></> },
    { key: 'changes', label: 'Thay đổi giữa điểm chạm', children: <><Card title="Luồng thay đổi nhãn giữa hai điểm chạm liên tiếp"><ReactECharts option={changeChart} style={{ height: 520 }} /></Card><Card className="table-card"><Table rowKey={(_, index) => String(index)} dataSource={changes.data} columns={[{ title: 'Điểm trước', render: (_, row) => touchpointNames[row.from_touchpoint_id] ?? row.from_touchpoint_id }, { title: 'Điểm sau', render: (_, row) => touchpointNames[row.to_touchpoint_id] ?? row.to_touchpoint_id }, { title: 'Nhãn trước', dataIndex: 'from_label' }, { title: 'Nhãn sau', dataIndex: 'to_label' }, { title: 'Số lượt', dataIndex: 'count' }]} /></Card></> },
    { key: 'quality', label: 'Chất lượng dữ liệu', children: <Row gutter={16}><Col span={14}><Card title="Tỷ lệ trạng thái xử lý"><ReactECharts option={qualityChart} style={{ height: 410 }} /></Card></Col><Col span={10}><Card title="Chi tiết trạng thái"><Table pagination={false} rowKey={(_, index) => String(index)} dataSource={quality.data} columns={[{ title: 'Ảnh', dataIndex: 'image_status' }, { title: 'Biểu cảm', dataIndex: 'expression_status' }, { title: 'Danh tính', dataIndex: 'identity_status' }, { title: 'Số bản ghi', dataIndex: 'count' }]} /></Card></Col></Row> }
  ]} /></>
}

export default function App() {
  return <AntApp><Routes><Route path="/login" element={<Login />} /><Route path="/*" element={<Shell />} /></Routes></AntApp>
}
