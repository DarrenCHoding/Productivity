// Satu baris tugas di daftar, beserta aksinya (selesai, edit, hapus).

import { api } from '../api.js';
import { icon } from '../icons.js';
import { attempt, el, toast } from '../ui.js';
import { openTaskDialog } from './task-dialog.js';

/**
 * @param task       data tugas dari API
 * @param onChanged  dipanggil setelah tugas berubah/dihapus, supaya daftar dimuat ulang
 */
export function taskItem(task, { onChanged }) {
  async function toggleDone() {
    const updated = await attempt(() => api.updateTask(task.id, { done: !task.done }));
    if (!updated) return;
    toast(updated.done ? 'Tugas selesai' : 'Tugas dikembalikan ke belum selesai');
    onChanged();
  }

  async function edit() {
    if (await openTaskDialog(task)) onChanged();
  }

  async function remove() {
    if (!confirm(`Hapus tugas "${task.title}"?`)) return;
    const ok = await attempt(() => api.deleteTask(task.id).then(() => true));
    if (!ok) return;
    toast('Tugas dihapus');
    onChanged();
  }

  return el('li', { class: `task${task.done ? ' done' : ''}` },
    el('button', {
      class: 'check',
      type: 'button',
      title: task.done ? 'Tandai belum selesai' : 'Tandai selesai',
      'aria-label': task.done ? 'Tandai belum selesai' : 'Tandai selesai',
      'aria-pressed': task.done ? 'true' : 'false',
      onclick: toggleDone,
    }, icon('check', 16)),
    el('div', { class: 'task-body', onclick: edit },
      el('div', { class: 'task-title' }, task.title),
    ),
    el('div', { class: 'task-actions' },
      el('button', { class: 'icon-btn', type: 'button', title: 'Edit', 'aria-label': 'Edit tugas', onclick: edit },
        icon('edit', 18)),
      el('button', { class: 'icon-btn danger', type: 'button', title: 'Hapus', 'aria-label': 'Hapus tugas', onclick: remove },
        icon('trash', 18)),
    ),
  );
}
