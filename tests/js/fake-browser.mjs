// "Browser tiruan" untuk menguji kode tampilan di Node.js:
// penyimpanan (localStorage), elemen notifikasi (toast), dan server palsu (fetch).

export function installFakeBrowser({ settings = {}, taskIds = [1, 2] } = {}) {
  const storage = new Map();
  globalThis.localStorage = {
    getItem: (key) => (storage.has(key) ? storage.get(key) : null),
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: (key) => storage.delete(key),
  };

  const toasts = [];
  const toastElement = {
    set textContent(value) { toasts.push(value); },
    get textContent() { return toasts.at(-1) ?? ''; },
    classList: { add() {}, remove() {}, toggle() {} },
  };
  globalThis.document = { getElementById: () => toastElement, visibilityState: 'visible' };
  globalThis.window = { addEventListener() {} };

  // Server palsu: hanya alamat yang dipakai timer fokus.
  const server = {
    settings: { focus_work_minutes: 25, focus_break_minutes: 5, ...settings },
    taskIds: new Set(taskIds),
    sessions: [],
    online: true,
  };
  globalThis.fetch = async (path, options = {}) => {
    if (!server.online) throw new TypeError('Failed to fetch');
    const method = options.method || 'GET';
    const body = options.body ? JSON.parse(options.body) : undefined;
    const reply = (status, data) => ({ status, ok: status < 400, json: async () => data });

    if (path === '/api/settings' && method === 'GET') return reply(200, { ...server.settings });
    if (path === '/api/settings' && method === 'PATCH') {
      Object.assign(server.settings, body);
      return reply(200, { ...server.settings });
    }
    if (path === '/api/focus/sessions' && method === 'POST') {
      if (body.task_id != null && !server.taskIds.has(body.task_id)) {
        return reply(400, { error: 'Tugas tidak ditemukan.' });
      }
      server.sessions.push(body);
      return reply(201, body);
    }
    return reply(404, { error: 'Alamat API tidak ditemukan.' });
  };

  return { storage, toasts, server };
}

/** Tunggu semua pekerjaan async (misalnya pengiriman ke server) selesai. */
export async function flush() {
  for (let i = 0; i < 10; i += 1) await new Promise((resolve) => setImmediate(resolve));
}

let instance = 0;

/**
 * Muat modul timer yang benar-benar baru, seperti saat halaman dimuat ulang.
 * Data di localStorage tetap ada; keadaan di memori mulai dari nol.
 */
export function loadFreshTimer() {
  instance += 1;
  return import(`../../static/js/focus-timer.js?muat-ulang=${instance}`);
}
