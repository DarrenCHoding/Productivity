// Satu baris tugas di daftar, beserta aksinya (selesai, edit, hapus).

import { api } from '../api.js';
import { describeDue, formatLong } from '../dates.js';
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

  const due = task.due_date ? describeDue(task.due_date) : null;
  const overdue = !task.done && due?.state === 'overdue';
  const important = task.priority === 'high';

  const classes = ['task'];
  if (task.done) classes.push('done');
  if (overdue) classes.push('overdue');
  if (important) classes.push('important');

  return el('li', { class: classes.join(' ') },
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
      (due || important) && el('div', { class: 'task-meta' },
        important && el('span', { class: 'chip chip-important' }, icon('flag', 14), 'Penting'),
        due && el('span', {
          class: `chip chip-due due-${task.done ? 'done' : due.state}`,
          title: `Jatuh tempo: ${formatLong(task.due_date)}`,
        }, icon('calendar', 14), due.label),
      ),
    ),
    el('div', { class: 'task-actions' },
      el('button', { class: 'icon-btn', type: 'button', title: 'Edit', 'aria-label': 'Edit tugas', onclick: edit },
        icon('edit', 18)),
      el('button', { class: 'icon-btn danger', type: 'button', title: 'Hapus', 'aria-label': 'Hapus tugas', onclick: remove },
        icon('trash', 18)),
    ),
  );
}
