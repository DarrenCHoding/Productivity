// Halaman "Pengaturan": cadangan & pemulihan data.

import { api } from '../api.js';
import { formatLong, formatTime } from '../dates.js';
import { icon } from '../icons.js';
import { attempt, el, toast } from '../ui.js';

// Pesan hasil pemulihan disimpan sebentar, karena halaman dimuat ulang setelah pemulihan.
const RESTORED_KEY = 'productivity.restoredMessage';

const KIND_LABEL = {
  harian: 'Cadangan harian',
  'sebelum-pemulihan': 'Sebelum pemulihan',
  'sebelum-pembaruan': 'Sebelum pembaruan aplikasi',
  lainnya: 'Cadangan',
};

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toLocaleString('id-ID', { maximumFractionDigits: 1 })} MB`;
}

/** Jalankan pemulihan setelah dikonfirmasi, lalu muat ulang seluruh aplikasi. */
async function confirmAndRestore(sourceLabel, action) {
  const ok = confirm(
    `Pulihkan data dari ${sourceLabel}?\n\n`
    + 'Seluruh data saat ini akan diganti dengan isi cadangan itu. '
    + 'Data saat ini disimpan dulu sebagai cadangan, jadi masih bisa dikembalikan.',
  );
  if (!ok) return;
  const result = await attempt(action);
  if (!result) return;
  try {
    sessionStorage.setItem(RESTORED_KEY,
      `Data berhasil dipulihkan (${result.summary}). Data sebelumnya disimpan sebagai ${result.safety_backup}.`);
  } catch { /* abaikan */ }
  // Muat ulang supaya semua bagian aplikasi (termasuk timer) memakai data yang baru.
  location.reload();
}

function restoredNotice() {
  let message = null;
  try {
    message = sessionStorage.getItem(RESTORED_KEY);
    sessionStorage.removeItem(RESTORED_KEY);
  } catch { /* abaikan */ }
  if (!message) return '';
  const notice = el('div', { class: 'notice success', role: 'status' },
    el('span', {}, message),
    el('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Tutup', onclick: () => notice.remove() }, '×'),
  );
  return notice;
}

function settingRow(iconName, title, description, action) {
  return el('div', { class: 'setting-row' },
    el('span', { class: 'setting-icon' }, icon(iconName, 20)),
    el('div', { class: 'setting-text' },
      el('div', { class: 'setting-title' }, title),
      el('p', {}, description),
    ),
    el('div', { class: 'setting-action' }, action),
  );
}

function backupSection() {
  const fileInput = el('input', {
    type: 'file', accept: '.db,application/octet-stream', class: 'visually-hidden',
    'aria-label': 'Pilih file cadangan',
  });
  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    fileInput.value = '';
    if (file) confirmAndRestore(`file "${file.name}"`, () => api.restoreBackup(file));
  });

  return el('section', { class: 'task-section' },
    el('h2', { class: 'section-title' }, 'Data & cadangan'),
    el('div', { class: 'settings-card' },
      settingRow('download', 'Unduh semua data',
        'Simpan seluruh data (tugas, kategori, riwayat fokus, dan pengaturan) ke satu file. '
        + 'Simpan file itu di tempat aman, misalnya flashdisk atau Google Drive.',
        el('a', { class: 'btn primary', href: api.exportUrl, download: '' }, icon('download', 18), 'Unduh data')),
      settingRow('upload', 'Pulihkan dari file',
        'Ganti seluruh data dengan isi file cadangan yang pernah Anda unduh. '
        + 'Data saat ini disimpan dulu sebagai cadangan.',
        el('label', { class: 'btn' }, icon('upload', 18), 'Pilih file…', fileInput)),
    ),
  );
}

async function automaticSection() {
  const listing = await attempt(() => api.listBackups());
  if (!listing) return '';

  const rows = listing.files.map((file) => {
    const day = file.created_at.slice(0, 10);
    const when = `${formatLong(day)}, pukul ${formatTime(file.created_at)}`;
    return el('li', { class: 'task backup-row' },
      el('span', { class: 'category-icon' }, icon('history', 18)),
      el('div', { class: 'task-body' },
        el('div', { class: 'task-title' }, KIND_LABEL[file.kind] || KIND_LABEL.lainnya),
        el('div', { class: 'category-count' }, `${when} · ${formatSize(file.size)}`),
      ),
      el('button', {
        class: 'btn', type: 'button',
        onclick: () => confirmAndRestore(`cadangan ${when}`, () => api.restoreAutomaticBackup(file.name)),
      }, 'Pulihkan'),
    );
  });

  return el('section', { class: 'task-section' },
    el('h2', { class: 'section-title' }, 'Cadangan otomatis',
      el('span', { class: 'section-count' }, listing.files.length || '')),
    el('p', { class: 'section-note' },
      'Setiap hari aplikasi menyimpan salinan data secara otomatis (7 hari terakhir). Lokasinya di komputer ini: ',
      el('code', {}, listing.folder)),
    rows.length
      ? el('ul', { class: 'task-list' }, rows)
      : el('p', { class: 'empty' }, 'Belum ada cadangan otomatis. Cadangan pertama dibuat saat aplikasi dijalankan.'),
  );
}

export const settingsView = {
  path: 'pengaturan',
  title: 'Pengaturan',

  async render(container) {
    container.replaceChildren(
      el('header', { class: 'view-header' },
        el('h1', {}, 'Pengaturan'),
        el('p', { class: 'subtitle' }, 'Cadangan data dan pengaturan aplikasi.'),
      ),
      restoredNotice(),
      backupSection(),
      await automaticSection(),
    );
    if (container.querySelector('.notice')) toast('Data berhasil dipulihkan');
  },
};
