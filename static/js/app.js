// Pusat aplikasi: daftar halaman (view), navigasi, dan penyegaran tampilan.
//
// Menambah halaman baru (misalnya timer fokus):
//   1. Buat file static/js/views/timer.js yang mengekspor objek view
//      { path, title, render(container) }.
//   2. Import di bawah dan tambahkan ke daftar VIEWS.

import { el } from './ui.js';
import { allTasksView } from './views/all-tasks.js';
import { todayView } from './views/today.js';

const VIEWS = [todayView, allTasksView];
const DEFAULT_PATH = VIEWS[0].path;

const navList = document.getElementById('nav');
const viewContainer = document.getElementById('view');

function currentPath() {
  const hash = location.hash.replace(/^#\/?/, '');
  return hash.split('?')[0] || DEFAULT_PATH;
}

function renderNav() {
  const path = currentPath();
  navList.replaceChildren(
    ...VIEWS.map((view) =>
      el('li', {},
        el('a', { href: `#/${view.path}`, class: view.path === path ? 'active' : '' },
          el('span', {}, view.title),
        ),
      ),
    ),
  );
}

async function renderView() {
  const view = VIEWS.find((v) => v.path === currentPath());
  if (!view) {
    location.hash = `#/${DEFAULT_PATH}`;
    return;
  }
  document.title = `${view.title} · Productivity`;
  renderNav();
  await view.render(viewContainer);
}

/** Panggil setelah data berubah supaya tampilan ikut diperbarui. */
export function refresh() {
  return renderView();
}

window.addEventListener('hashchange', () => {
  renderView();
  viewContainer.focus({ preventScroll: true });
});

renderView();
