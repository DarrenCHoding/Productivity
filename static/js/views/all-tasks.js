// Halaman "Semua tugas": semua tugas yang belum selesai, ditambah bagian "Selesai".

import { api } from '../api.js';
import { categoryFilter, readCategoryFilter } from '../components/category-filter.js';
import { quickAdd } from '../components/quick-add.js';
import { doneSection, taskList } from '../components/task-list.js';
import { DATA_CHANGED, emit } from '../events.js';
import { attempt, el } from '../ui.js';

export const allTasksView = {
  path: 'semua',
  title: 'Semua tugas',

  async badge() {
    const tasks = await api.listTasks({ status: 'open' });
    return tasks.length;
  },

  async render(container, params) {
    const categories = (await attempt(() => api.listCategories())) || [];
    const filter = readCategoryFilter(params, categories);
    const listArea = el('div', { class: 'list-area' });

    async function load() {
      const tasks = await attempt(() => api.listTasks({ status: 'all', category: filter.query }));
      if (!tasks) return;
      const open = tasks.filter((t) => !t.done);
      const done = tasks.filter((t) => t.done);
      listArea.replaceChildren(
        taskList(open, {
          onChanged: load,
          emptyText: done.length
            ? 'Semua tugas sudah selesai.'
            : filter.label ? `Tidak ada tugas di "${filter.label}".` : 'Belum ada tugas. Tambahkan tugas pertama Anda di atas.',
        }),
        doneSection(done, { onChanged: load }) || '',
      );
      emit(DATA_CHANGED);
    }

    container.replaceChildren(
      el('header', { class: 'view-header' }, el('h1', {}, 'Semua tugas')),
      categoryFilter('semua', categories, filter.value),
      quickAdd({ onAdded: load, categories, defaultCategory: filter.defaultCategory }),
      listArea,
    );
    await load();
  },
};
