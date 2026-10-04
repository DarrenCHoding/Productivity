// Kolom "Tambah tugas" di bagian atas daftar.

import { api } from '../api.js';
import { icon } from '../icons.js';
import { attempt, el } from '../ui.js';

/**
 * @param onAdded  dipanggil setelah tugas berhasil ditambahkan
 */
export function quickAdd({ onAdded }) {
  const titleInput = el('input', {
    class: 'input', name: 'title', maxlength: '500', autocomplete: 'off',
    placeholder: 'Tambah tugas baru…', 'aria-label': 'Judul tugas baru',
  });

  async function submit(event) {
    event.preventDefault();
    if (!titleInput.value.trim()) {
      titleInput.focus();
      return;
    }
    const task = await attempt(() => api.createTask({ title: titleInput.value }));
    if (!task) return;
    titleInput.value = '';
    titleInput.focus();
    onAdded(task);
  }

  return el('form', { class: 'quick-add', onsubmit: submit },
    el('div', { class: 'quick-add-row' },
      titleInput,
      el('button', { class: 'btn primary', type: 'submit' }, icon('plus', 18), 'Tambah'),
    ),
  );
}
