// Pusat aplikasi: daftar halaman (view), navigasi, dan penyegaran tampilan.
//
// Menambah halaman baru (misalnya timer fokus):
//   1. Buat file static/js/views/timer.js yang mengekspor objek view:
//        { path, title, render(container, params), badge() (opsional, angka di menu) }
//      `params` berisi bagian setelah "?" di alamat, misalnya #/semua?kategori=3.
//   2. Import di bawah dan tambahkan ke daftar VIEWS.

import { todayISO } from './dates.js';
import { DATA_CHANGED, on } from './events.js';
import { el } from './ui.js';
import { allTasksView } from './views/all-tasks.js';
import { categoriesView } from './views/categories.js';
import { todayView } from './views/today.js';

const VIEWS = [todayView, allTasksView, categoriesView];
const DEFAULT_PATH = VIEWS[0].path;

const navList = document.getElementById('nav');
const viewContainer = document.getElementById('view');
const badges = new Map(); // path -> elemen angka di menu

function currentPath() {
  const hash = location.hash.replace(/^#\/?/, '');
  return hash.split('?')[0] || DEFAULT_PATH;
}

function currentParams() {
  const query = location.hash.split('?')[1] || '';
  return new URLSearchParams(query);
}

function buildNav() {
  navList.replaceChildren(
    ...VIEWS.map((view) => {
      const count = el('span', { class: 'count' });
      badges.set(view.path, count);
      return el('li', {},
        el('a', { href: `#/${view.path}`, 'data-path': view.path },
          el('span', {}, view.title),
          count,
        ),
      );
    }),
  );
}

function highlightNav() {
  const path = currentPath();
  for (const link of navList.querySelectorAll('a')) {
    const active = link.dataset.path === path;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
}

async function updateBadges() {
  await Promise.all(VIEWS.filter((v) => v.badge).map(async (view) => {
    try {
      const n = await view.badge();
      badges.get(view.path).textContent = n > 0 ? n : '';
    } catch {
      // Angka di menu tidak penting; abaikan bila gagal.
    }
  }));
}

let renderedDate = todayISO();
let renderToken = 0;

async function renderView() {
  const view = VIEWS.find((v) => v.path === currentPath());
  if (!view) {
    location.replace(`#/${DEFAULT_PATH}`);
    return;
  }
  renderedDate = todayISO();
  document.title = `${view.title} · Productivity`;
  highlightNav();

  // Halaman disiapkan di luar layar dulu, lalu ditampilkan setelah datanya siap.
  // Bila pengguna sudah pindah ke halaman lain sebelum selesai, hasilnya dibuang.
  const token = ++renderToken;
  const page = el('div', { class: 'page' });
  await view.render(page, currentParams());
  if (token === renderToken) viewContainer.replaceChildren(page);
}

/** Muat ulang halaman yang sedang dibuka. */
export function refresh() {
  return renderView();
}

window.addEventListener('hashchange', () => {
  renderView();
  viewContainer.focus({ preventScroll: true });
});

// Kalau aplikasi dibiarkan terbuka melewati tengah malam, segarkan saat dibuka lagi
// supaya "Hari ini" dan label terlambat sesuai tanggal baru.
function refreshIfNewDay() {
  if (todayISO() !== renderedDate) renderView();
}
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') refreshIfNewDay();
});
setInterval(refreshIfNewDay, 60 * 1000);

on(DATA_CHANGED, updateBadges);

buildNav();
renderView();
