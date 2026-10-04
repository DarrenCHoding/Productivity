// Halaman "Hari ini".

import { el } from '../ui.js';

export const todayView = {
  path: 'hari-ini',
  title: 'Hari ini',

  async render(container) {
    container.replaceChildren(
      el('header', { class: 'view-header' },
        el('h1', {}, 'Hari ini'),
        el('p', { class: 'subtitle' }, new Date().toLocaleDateString('id-ID', {
          weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
        })),
      ),
      el('p', { class: 'empty' }, 'Belum ada tugas. Fitur tugas akan segera hadir.'),
    );
  },
};
