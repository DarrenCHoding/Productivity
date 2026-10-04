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
