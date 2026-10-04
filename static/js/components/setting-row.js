// Satu baris pengaturan: ikon, judul, keterangan, dan tombol/isian di kanan.

import { icon } from '../icons.js';
import { el } from '../ui.js';

export function settingRow(iconName, title, description, action) {
  return el('div', { class: 'setting-row' },
    el('span', { class: 'setting-icon' }, icon(iconName, 20)),
    el('div', { class: 'setting-text' },
      el('div', { class: 'setting-title' }, title),
      el('p', {}, description),
    ),
    el('div', { class: 'setting-action' }, action),
  );
}
