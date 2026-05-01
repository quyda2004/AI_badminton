const API = 'http://localhost:8000'

// ── TOKEN ──────────────────────────────────────────
const getToken = () => localStorage.getItem('token')
const getUser  = () => JSON.parse(localStorage.getItem('user') || 'null')
const setAuth  = (token, user) => { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)) }
const clearAuth = () => { localStorage.removeItem('token'); localStorage.removeItem('user') }

// ── API CLIENT ─────────────────────────────────────
async function api(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  })

  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw { status: res.status, detail: data.detail || 'Lỗi không xác định' }
  return data
}

// ── ALERT ──────────────────────────────────────────
function showAlert(id, msg, type = 'error') {
  const el = document.getElementById(id)
  el.textContent = msg
  el.className = `alert alert-${type} show`
  setTimeout(() => el.classList.remove('show'), 4000)
}

// ── SECTION / NAV ──────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'))
  document.querySelectorAll('.nav-links button').forEach(b => b.classList.remove('active'))
  document.getElementById(`section-${name}`).classList.add('active')
  document.getElementById(`nav-${name}`)?.classList.add('active')
}

// ── AUTH ───────────────────────────────────────────
function showTab(tab) {
  document.getElementById('form-login').style.display    = tab === 'login'    ? 'block' : 'none'
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none'
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab))
}

document.getElementById('form-login').addEventListener('submit', async e => {
  e.preventDefault()
  try {
    const token = await api('POST', '/auth/login', {
      email:    document.getElementById('login-email').value,
      password: document.getElementById('login-password').value,
    })
    localStorage.setItem('token', token.access_token) // lưu trước để /auth/me dùng được
    const user = await api('GET', '/auth/me', null)
    setAuth(token.access_token, user)
    afterLogin(user)
  } catch (err) {
    showAlert('alert-auth', err.detail)
  }
})

document.getElementById('form-register').addEventListener('submit', async e => {
  e.preventDefault()
  try {
    await api('POST', '/auth/register', {
      email:     document.getElementById('reg-email').value,
      password:  document.getElementById('reg-password').value,
      full_name: document.getElementById('reg-name').value,
      phone:     document.getElementById('reg-phone').value || null,
    })
    showAlert('alert-auth', 'Đăng ký thành công! Mời đăng nhập.', 'success')
    showTab('login')
  } catch (err) {
    showAlert('alert-auth', err.detail)
  }
})

function afterLogin(user) {
  document.getElementById('user-info').textContent = `👤 ${user.full_name} (${user.role})`
  document.getElementById('nav-auth').style.display = 'none'
  document.getElementById('btn-logout').style.display = 'inline-block'
  document.getElementById('nav-courts').style.display   = 'inline-block'
  document.getElementById('nav-bookings').style.display = 'inline-block'
  if (user.role === 'admin') document.getElementById('nav-admin').style.display = 'inline-block'
  showSection('courts')
  loadCourts()
}

document.getElementById('btn-logout').addEventListener('click', () => {
  clearAuth()
  location.reload()
})

// ── COURTS ─────────────────────────────────────────
let selectedCourtId = null
let selectedSlot    = null

async function loadCourts() {
  const courts = await api('GET', '/courts')
  const grid = document.getElementById('courts-grid')
  grid.innerHTML = courts.map(c => `
    <div class="court-card">
      <h4>${c.name}</h4>
      <div class="type">${c.type}</div>
      <div class="price">${c.price_per_hour.toLocaleString('vi-VN')}đ / giờ</div>
      <span class="badge badge-${c.status}">${c.status}</span>
      <br><br>
      <button class="btn btn-primary btn-sm" onclick="openBookingModal('${c.id}', '${c.name}', ${c.price_per_hour})">
        Đặt sân
      </button>
    </div>
  `).join('')
}

// ── BOOKING MODAL ──────────────────────────────────
async function openBookingModal(courtId, courtName, price) {
  selectedCourtId = courtId
  selectedSlot    = null
  document.getElementById('modal-court-name').textContent = courtName
  document.getElementById('modal-court-price').textContent = `${price.toLocaleString('vi-VN')}đ / giờ`
  document.getElementById('booking-date').value = ''
  document.getElementById('slots-container').innerHTML = '<div class="loading">Chọn ngày để xem slot trống</div>'
  document.getElementById('modal-booking').classList.add('show')
}

document.getElementById('booking-date').addEventListener('change', async e => {
  const date = e.target.value
  if (!date) return
  document.getElementById('slots-container').innerHTML = '<div class="loading">Đang tải...</div>'
  try {
    const slots = await api('GET', `/courts/${selectedCourtId}/availability?date=${date}`)
    document.getElementById('slots-container').innerHTML = `
      <div class="slots-grid">
        ${slots.map(s => `
          <div class="slot ${s.available ? 'available' : 'unavailable'}"
               onclick="${s.available ? `selectSlot('${date}', '${s.start}', '${s.end}', this)` : ''}">
            ${s.start}<br>${s.end}
          </div>
        `).join('')}
      </div>
    `
  } catch {
    document.getElementById('slots-container').innerHTML = '<div class="loading">Lỗi tải slot</div>'
  }
})

function selectSlot(date, start, end, el) {
  document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'))
  el.classList.add('selected')
  selectedSlot = { date, start, end }
}

document.getElementById('btn-confirm-booking').addEventListener('click', async () => {
  if (!selectedSlot) return showAlert('alert-booking-modal', 'Chọn slot giờ trước nhé!')
  const { date, start, end } = selectedSlot
  const startTime = `${date}T${start}:00+00:00`
  const endTime   = `${date}T${end}:00+00:00`
  try {
    await api('POST', '/bookings', { court_id: selectedCourtId, start_time: startTime, end_time: endTime })
    closeModal('modal-booking')
    showSection('bookings')
    loadBookings()
    showAlert('alert-bookings', 'Đặt sân thành công!', 'success')
  } catch (err) {
    showAlert('alert-booking-modal', err.detail)
  }
})

// ── MY BOOKINGS ────────────────────────────────────
async function loadBookings() {
  document.getElementById('bookings-table-body').innerHTML = '<tr><td colspan="6" class="loading">Đang tải...</td></tr>'
  try {
    const bookings = await api('GET', '/bookings')
    if (!bookings.length) {
      document.getElementById('bookings-table-body').innerHTML = '<tr><td colspan="6" class="loading">Chưa có booking nào</td></tr>'
      return
    }
    document.getElementById('bookings-table-body').innerHTML = bookings.map(b => `
      <tr>
        <td>${b.court_id}</td>
        <td>${fmtDateTime(b.start_time)}</td>
        <td>${fmtDateTime(b.end_time)}</td>
        <td><span class="badge badge-${b.status}">${b.status}</span></td>
        <td>${b.total_price.toLocaleString('vi-VN')}đ</td>
        <td>
          ${b.status === 'confirmed' ? `
            <button class="btn btn-warning btn-sm" onclick="openReschedule('${b.id}')">Đổi lịch</button>
            <button class="btn btn-danger btn-sm"  onclick="cancelBooking('${b.id}')">Huỷ</button>
          ` : '—'}
        </td>
      </tr>
    `).join('')
  } catch (err) {
    showAlert('alert-bookings', err.detail)
  }
}

async function cancelBooking(id) {
  if (!confirm('Bạn chắc muốn huỷ booking này không?')) return
  try {
    await api('PUT', `/bookings/${id}/cancel`)
    loadBookings()
    showAlert('alert-bookings', 'Huỷ booking thành công!', 'success')
  } catch (err) {
    showAlert('alert-bookings', err.detail)
  }
}

// ── RESCHEDULE MODAL ───────────────────────────────
let rescheduleId = null

function openReschedule(id) {
  rescheduleId = id
  document.getElementById('reschedule-start').value = ''
  document.getElementById('reschedule-end').value   = ''
  document.getElementById('modal-reschedule').classList.add('show')
}

document.getElementById('btn-confirm-reschedule').addEventListener('click', async () => {
  const start = document.getElementById('reschedule-start').value
  const end   = document.getElementById('reschedule-end').value
  if (!start || !end) return showAlert('alert-reschedule', 'Nhập đủ ngày giờ nhé!')
  try {
    await api('PUT', `/bookings/${rescheduleId}/reschedule`, {
      new_start_time: new Date(start).toISOString(),
      new_end_time:   new Date(end).toISOString(),
    })
    closeModal('modal-reschedule')
    loadBookings()
    showAlert('alert-bookings', 'Đổi lịch thành công!', 'success')
  } catch (err) {
    showAlert('alert-reschedule', err.detail)
  }
})

// ── ADMIN ──────────────────────────────────────────
async function loadAdmin() {
  try {
    const stats = await api('GET', '/admin/stats')
    document.getElementById('stat-bookings').textContent       = stats.total_bookings
    document.getElementById('stat-revenue').textContent        = stats.total_revenue.toLocaleString('vi-VN') + 'đ'
    document.getElementById('stat-courts').textContent         = stats.active_courts
    document.getElementById('stat-users').textContent          = stats.total_users
    document.getElementById('stat-bookings-today').textContent = stats.bookings_today

    const bookings = await api('GET', '/admin/bookings')
    document.getElementById('admin-table-body').innerHTML = bookings.map(b => `
      <tr>
        <td>${b.id.substring(0,8)}...</td>
        <td>${b.user_id}</td>
        <td>${b.court_id}</td>
        <td>${fmtDateTime(b.start_time)}</td>
        <td><span class="badge badge-${b.status}">${b.status}</span></td>
        <td>${b.total_price.toLocaleString('vi-VN')}đ</td>
      </tr>
    `).join('')
  } catch (err) {
    showAlert('alert-admin', err.detail)
  }
}

// ── UTILS ──────────────────────────────────────────
function fmtDateTime(iso) {
  return new Date(iso).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' })
}

function closeModal(id) {
  document.getElementById(id).classList.remove('show')
}

// ── INIT ───────────────────────────────────────────
;(function init() {
  const user = getUser()
  if (user && getToken()) {
    afterLogin(user)
  } else {
    showSection('auth')
    showTab('login')
  }

  document.getElementById('nav-courts').addEventListener('click', () => { showSection('courts'); loadCourts() })
  document.getElementById('nav-bookings').addEventListener('click', () => { showSection('bookings'); loadBookings() })
  document.getElementById('nav-admin')?.addEventListener('click', () => { showSection('admin'); loadAdmin() })
  document.getElementById('nav-auth').addEventListener('click', () => showSection('auth'))
})()
