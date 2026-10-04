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
};

export { request, query };
