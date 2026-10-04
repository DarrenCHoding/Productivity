// Jendela untuk mengedit tugas.

import { api } from '../api.js';
import { formatDuration } from '../dates.js';
import { icon } from '../icons.js';
import { el, toast } from '../ui.js';
import { categorySelect, dueDateInput, priorityToggle } from './task-fields.js';

/**
 * Buka jendela edit. Hasil: Promise yang bernilai true bila tugas diubah atau dihapus.
 */
export async function openTaskDialog(task) {
  let categories = [];
  try {
    categories = await api.listCategories();
  } catch (err) {
    toast(err.message, { error: true });
    return false;
  }

  return new Promise((resolve) => {
    let changed = false;

    const titleInput = el('input', {
      class: 'input', name: 'title', required: true, maxlength: '500',
      value: task.title, autocomplete: 'off',
    });
    const dueInput = dueDateInput(task.due_date);
    const priority = priorityToggle(task.priority);
    const category = categorySelect(categories, task.category_id);
    const errorBox = el('p', { class: 'form-error', role: 'alert' });

    async function save(event) {
      event.preventDefault();
      errorBox.textContent = '';
      try {
        await api.updateTask(task.id, {
          title: titleInput.value,
          due_date: dueInput.value || null,
          priority: priority.priority,
          category_id: category.categoryId,
        });
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
        el('div', { class: 'field-row' },
          el('label', { class: 'field' }, el('span', {}, 'Tenggat (opsional)'), dueInput),
          el('div', { class: 'field' }, el('span', {}, 'Prioritas'), priority),
        ),
        el('label', { class: 'field' }, el('span', {}, 'Kategori'), category),
        el('div', { class: 'dialog-focus' },
          el('span', {}, task.focus_seconds >= 60
            ? `Total fokus: ${formatDuration(task.focus_seconds)}`
            : 'Belum ada waktu fokus'),
          !task.done && el('button', {
            class: 'btn', type: 'button',
            onclick: () => {
              dialog.close();
              location.hash = `#/fokus?tugas=${task.id}`;
            },
          }, icon('timer', 18), 'Mulai fokus'),
        ),
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
