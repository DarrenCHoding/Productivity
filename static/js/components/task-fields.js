// Isian data tugas yang dipakai bersama oleh kolom tambah cepat dan jendela edit.

import { icon } from '../icons.js';
import { el } from '../ui.js';

/** Isian tanggal jatuh tempo. Baca nilainya lewat .value ('' = tanpa tanggal). */
export function dueDateInput(value = '') {
  return el('input', {
    class: 'input date-input', type: 'date', name: 'due_date', value: value || '',
    'aria-label': 'Tanggal jatuh tempo', title: 'Tanggal jatuh tempo',
  });
}

/**
 * Tombol "Penting" yang bisa ditekan nyala/mati.
 * Baca nilainya lewat .priority ('high' atau 'normal'); ubah lewat .setPriority().
 */
export function priorityToggle(value = 'normal') {
  const button = el('button', {
    class: 'btn toggle priority-toggle', type: 'button', title: 'Tandai sebagai penting',
  }, icon('flag', 18), 'Penting');

  button.setPriority = (priority) => {
    button.priority = priority;
    button.setAttribute('aria-pressed', priority === 'high' ? 'true' : 'false');
  };
  button.addEventListener('click', () => {
    button.setPriority(button.priority === 'high' ? 'normal' : 'high');
  });
  button.setPriority(value);
  return button;
}

/**
 * Pilihan kategori. Baca nilainya lewat .categoryId (nomor atau null).
 * @param categories  daftar kategori dari API
 */
export function categorySelect(categories, value = null) {
  const select = el('select', { class: 'input category-select', name: 'category_id', 'aria-label': 'Kategori' },
    el('option', { value: '' }, 'Tanpa kategori'),
    categories.map((c) => el('option', { value: String(c.id) }, c.name)),
  );
  select.value = value == null ? '' : String(value);
  Object.defineProperty(select, 'categoryId', {
    get: () => (select.value ? Number(select.value) : null),
  });
  return select;
}

/** Label pengulangan untuk ditampilkan. */
export const REPEAT_LABELS = {
  daily: 'Setiap hari',
  weekly: 'Setiap minggu',
  monthly: 'Setiap bulan',
};

/** Pilihan pengulangan. Baca nilainya lewat .repeat (null = tidak berulang). */
export function repeatSelect(value = null) {
  const select = el('select', { class: 'input', name: 'repeat', 'aria-label': 'Ulangi' },
    el('option', { value: '' }, 'Tidak berulang'),
    Object.entries(REPEAT_LABELS).map(([key, label]) => el('option', { value: key }, label)),
  );
  select.value = value || '';
  Object.defineProperty(select, 'repeat', { get: () => select.value || null });
  return select;
}
