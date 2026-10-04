// Jendela untuk mengedit tugas.

import { api } from '../api.js';
import { el, toast } from '../ui.js';

/**
 * Buka jendela edit. Hasil: Promise yang bernilai true bila tugas diubah atau dihapus.
 */
export function openTaskDialog(task) {
  return new Promise((resolve) => {
    let changed = false;

    const titleInput = el('input', {
      class: 'input', name: 'title', required: true, maxlength: '500',
      value: task.title, autocomplete: 'off',
    });
    const errorBox = el('p', { class: 'form-error', role: 'alert' });

    async function save(event) {
      event.preventDefault();
      errorBox.textContent = '';
      try {
        await api.updateTask(task.id, { title: titleInput.value });
        changed = true;
        toast('Perubahan disimpan');
        dialog.close();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    }

    async function remove() {
      if (!confirm(`Hapus tugas "${task.title}"?`)) return;
      try {
        await api.deleteTask(task.id);
        changed = true;
        toast('Tugas dihapus');
        dialog.close();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    }

    const dialog = el('dialog', { class: 'dialog' },
      el('form', { onsubmit: save },
        el('h2', {}, 'Edit tugas'),
        el('label', { class: 'field' }, el('span', {}, 'Judul'), titleInput),
        errorBox,
        el('div', { class: 'dialog-actions' },
          el('button', { class: 'btn danger', type: 'button', onclick: remove }, 'Hapus'),
          el('span', { class: 'spacer' }),
          el('button', { class: 'btn', type: 'button', onclick: () => dialog.close() }, 'Batal'),
          el('button', { class: 'btn primary', type: 'submit' }, 'Simpan'),
        ),
      ),
    );

    // Klik di luar jendela = batal.
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener('close', () => {
      dialog.remove();
      resolve(changed);
    });

    document.body.append(dialog);
    dialog.showModal();
    titleInput.focus();
  });
}
