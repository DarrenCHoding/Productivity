// Halaman "Hari ini": tugas yang jatuh tempo hari ini dan yang terlambat,
// tugas penting di atas. Tugas yang diselesaikan hari ini tampil di bagian bawah.

import { api } from '../api.js';
import { categoryFilter, readCategoryFilter } from '../components/category-filter.js';
import { quickAdd } from '../components/quick-add.js';
import { doneSection, taskList } from '../components/task-list.js';
import { formatLong, todayISO } from '../dates.js';
import { DATA_CHANGED, emit } from '../events.js';
import { attempt, el, toast } from '../ui.js';

function summaryText(open, today) {
  if (open.length === 0) return '';
  const overdue = open.filter((t) => t.due_date < today).length;
  const parts = [`${open.length} tugas`];
  if (overdue) parts.push(`${overdue} terlambat`);
  return parts.join(' · ');
}

export const todayView = {
  path: 'hari-ini',
  title: 'Hari ini',

  /** Angka di menu samping: jumlah tugas hari ini + terlambat yang belum selesai. */
  async badge() {
    const tasks = await api.listTasks({ view: 'today', status: 'open', today: todayISO() });
    return tasks.length;
  },

  async render(container, params) {
    const categories = (await attempt(() => api.listCategories())) || [];
    const filter = readCategoryFilter(params, categories);
    const today = todayISO();
    const summary = el('p', { class: 'subtitle summary' });
    const listArea = el('div', { class: 'list-area' });

    async function load() {
      const tasks = await attempt(() => api.listTasks({ view: 'today', today, category: filter.query }));
      if (!tasks) return;
      const open = tasks.filter((t) => !t.done);
      const done = tasks.filter((t) => t.done);
      summary.textContent = summaryText(open, today);
      listArea.replaceChildren(
        open.length
          ? taskList(open, { onChanged: load })
          : el('div', { class: 'empty' },
            el('p', { class: 'empty-title' }, done.length
              ? 'Semua tugas hari ini sudah selesai!'
              : filter.label ? `Tidak ada tugas hari ini di "${filter.label}".` : 'Tidak ada tugas untuk hari ini.'),
            el('p', {}, 'Tugas tanpa deadline atau dengan deadline nanti ada di ',
              el('a', { href: '#/semua' }, 'Semua tugas'), '.'),
          ),
        doneSection(done, { onChanged: load, title: 'Selesai hari ini' }) || '',
      );
      emit(DATA_CHANGED);
    }

    container.replaceChildren(
      el('header', { class: 'view-header' },
        el('h1', {}, 'Hari ini'),
        el('p', { class: 'subtitle' }, formatLong(today)),
        summary,
      ),
      // Tugas baru di halaman ini otomatis bertenggat hari ini (bisa diganti).
      categoryFilter('hari-ini', categories, filter.value),
      quickAdd({
        defaultDue: today,
        categories,
        defaultCategory: filter.defaultCategory,
        onAdded: (task) => {
          if (!task.due_date || task.due_date > today) {
            toast('Tugas ditambahkan. Karena tenggatnya bukan hari ini, tugas ada di “Semua tugas”.');
          }
          load();
        },
      }),
      listArea,
    );
    await load();
  },
};
