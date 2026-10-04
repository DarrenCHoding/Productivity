// Kolom "Tambah tugas" di bagian atas daftar.

import { api } from '../api.js';
import { icon } from '../icons.js';
import { attempt, el } from '../ui.js';
import { dueDateInput, priorityToggle } from './task-fields.js';

/**
 * @param onAdded     dipanggil setelah tugas berhasil ditambahkan
 * @param defaultDue  tanggal awal yang terisi (misalnya hari ini di halaman "Hari ini")
 */
export function quickAdd({ onAdded, defaultDue = '' }) {
  const titleInput = el('input', {
    class: 'input title-input', name: 'title', maxlength: '500', autocomplete: 'off',
    placeholder: 'Tambah tugas baru…', 'aria-label': 'Judul tugas baru',
  });
  const dueInput = dueDateInput(defaultDue);
  const priority = priorityToggle('normal');

  async function submit(event) {
    event.preventDefault();
    if (!titleInput.value.trim()) {
      titleInput.focus();
      return;
    }
    const task = await attempt(() => api.createTask({
      title: titleInput.value,
      due_date: dueInput.value || null,
      priority: priority.priority,
    }));
    if (!task) return;
    titleInput.value = '';
    dueInput.value = defaultDue;
    priority.setPriority('normal');
    titleInput.focus();
    onAdded(task);
  }

  return el('form', { class: 'quick-add', onsubmit: submit },
    el('div', { class: 'quick-add-row' },
      titleInput,
      el('button', { class: 'btn primary', type: 'submit' }, icon('plus', 18), 'Tambah'),
    ),
    el('div', { class: 'quick-add-options' },
      el('label', { class: 'inline-field' }, icon('calendar', 18), dueInput),
      priority,
    ),
  );
}
