// Semua komunikasi dengan server (API) dikumpulkan di file ini.
// Tampilan tidak memanggil fetch() langsung, cukup memakai fungsi di sini.

async function request(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error('Tidak bisa terhubung ke server. Pastikan server.py masih berjalan.');
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((data && data.error) || `Terjadi kesalahan (kode ${res.status}).`);
  }
  return data;
}

function query(params) {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') q.set(key, value);
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

export const api = {
  health: () => request('GET', '/api/health'),

  // Tugas
  listTasks: (params = {}) => request('GET', `/api/tasks${query(params)}`),
  createTask: (data) => request('POST', '/api/tasks', data),
  updateTask: (id, data) => request('PATCH', `/api/tasks/${id}`, data),
  deleteTask: (id) => request('DELETE', `/api/tasks/${id}`),

  // Kategori
  listCategories: () => request('GET', '/api/categories'),
  createCategory: (name) => request('POST', '/api/categories', { name }),
  renameCategory: (id, name) => request('PATCH', `/api/categories/${id}`, { name }),
  deleteCategory: (id) => request('DELETE', `/api/categories/${id}`),

  // Pengaturan
  getSettings: () => request('GET', '/api/settings'),
  updateSettings: (data) => request('PATCH', '/api/settings', data),

  // Timer fokus
  listFocusSessions: (params = {}) => request('GET', `/api/focus/sessions${query(params)}`),
  logFocusSession: (data) => request('POST', '/api/focus/sessions', data),
  deleteFocusSession: (id) => request('DELETE', `/api/focus/sessions/${id}`),
};

export { request, query };
