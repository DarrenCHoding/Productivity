// Daftar tugas, dan bagian "Selesai" yang bisa dibuka-tutup.

import { icon } from '../icons.js';
import { el } from '../ui.js';
import { taskItem } from './task-item.js';

export function taskList(tasks, { onChanged, emptyText }) {
  if (tasks.length === 0) {
    return emptyText ? el('p', { class: 'empty' }, emptyText) : el('div');
  }
  return el('ul', { class: 'task-list' }, tasks.map((task) => taskItem(task, { onChanged })));
}

/** Bagian berjudul berisi daftar tugas. */
export function taskSection(title, tasks, { onChanged, tone }) {
  if (tasks.length === 0) return null;
  return el('section', { class: `task-section${tone ? ` tone-${tone}` : ''}` },
    el('h2', { class: 'section-title' }, title, el('span', { class: 'section-count' }, tasks.length)),
    taskList(tasks, { onChanged }),
  );
}

/** Bagian tugas yang sudah selesai; status buka/tutup diingat browser. */
export function doneSection(tasks, { onChanged, title = 'Selesai' }) {
  if (tasks.length === 0) return null;
  const storageKey = 'productivity.doneSectionOpen';
  let open = false;
  try { open = localStorage.getItem(storageKey) === '1'; } catch { /* abaikan */ }

  const section = el('section', { class: `task-section done-section${open ? ' open' : ''}` });
  const toggle = el('button', {
    class: 'section-toggle', type: 'button', 'aria-expanded': String(open),
    onclick: () => {
      open = !open;
      section.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
      try { localStorage.setItem(storageKey, open ? '1' : '0'); } catch { /* abaikan */ }
    },
  }, icon('chevron', 16), title, el('span', { class: 'section-count' }, tasks.length));

  section.append(toggle, taskList(tasks, { onChanged }));
  return section;
}
