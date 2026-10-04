// Halaman "Kategori": membuat, mengganti nama, dan menghapus kategori.

import { api } from '../api.js';
import { DATA_CHANGED, emit } from '../events.js';
import { icon } from '../icons.js';
import { attempt, el, toast } from '../ui.js';

function countText(category) {
  if (category.total_count === 0) return 'Belum ada tugas';
  if (category.open_count === 0) return `${category.total_count} tugas, semua selesai`;
  return `${category.open_count} tugas belum selesai`;
}

export const categoriesView = {
  path: 'kategori',
  title: 'Kategori',

  async render(container) {
    const listArea = el('div', { class: 'list-area' });

    async function load() {
      const categories = await attempt(() => api.listCategories());
      if (!categories) return;
      listArea.replaceChildren(
        categories.length
          ? el('ul', { class: 'task-list category-list' }, categories.map((c) => categoryRow(c, load)))
          : el('div', { class: 'empty' },
            el('p', { class: 'empty-title' }, 'Belum ada kategori.'),
            el('p', {}, 'Contoh: Kerja, Pribadi, Kuliah.'),
          ),
      );
      emit(DATA_CHANGED);
    }

    const nameInput = el('input', {
      class: 'input', maxlength: '50', autocomplete: 'off',
      placeholder: 'Nama kategori baru…', 'aria-label': 'Nama kategori baru',
    });

    async function add(event) {
      event.preventDefault();
      if (!nameInput.value.trim()) {
        nameInput.focus();
        return;
      }
      const created = await attempt(() => api.createCategory(nameInput.value));
      if (!created) return;
      toast(`Kategori "${created.name}" dibuat`);
      nameInput.value = '';
      nameInput.focus();
      load();
    }

    container.replaceChildren(
      el('header', { class: 'view-header' },
        el('h1', {}, 'Kategori'),
        el('p', { class: 'subtitle' }, 'Kelompokkan tugas, lalu filter daftar tugas per kategori.'),
      ),
      el('form', { class: 'quick-add', onsubmit: add },
        el('div', { class: 'quick-add-row' },
          nameInput,
          el('button', { class: 'btn primary', type: 'submit' }, icon('plus', 18), 'Tambah'),
        ),
      ),
      listArea,
    );
    await load();
  },
};

/** Satu baris kategori. Bisa berubah menjadi mode "ganti nama". */
function categoryRow(category, onChanged) {
  const row = el('li', { class: 'task category-row' });

  function showNormal() {
    row.replaceChildren(
      el('span', { class: 'category-icon' }, icon('tag', 18)),
      el('a', { class: 'task-body category-link', href: `#/semua?kategori=${category.id}`, title: 'Lihat tugas di kategori ini' },
        el('div', { class: 'task-title' }, category.name),
        el('div', { class: 'category-count' }, countText(category)),
      ),
      el('div', { class: 'task-actions always' },
        el('button', { class: 'icon-btn', type: 'button', title: 'Ganti nama', 'aria-label': `Ganti nama ${category.name}`, onclick: showRename },
          icon('edit', 18)),
        el('button', { class: 'icon-btn danger', type: 'button', title: 'Hapus', 'aria-label': `Hapus ${category.name}`, onclick: remove },
          icon('trash', 18)),
      ),
    );
  }

  function showRename() {
    const input = el('input', {
      class: 'input', maxlength: '50', value: category.name, autocomplete: 'off',
      'aria-label': 'Nama kategori',
    });
    async function save(event) {
      event.preventDefault();
      if (input.value.trim() === category.name) {
        showNormal();
        return;
      }
      const updated = await attempt(() => api.renameCategory(category.id, input.value));
      if (!updated) return;
      toast('Nama kategori diganti');
      onChanged();
    }
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') showNormal();
    });
    row.replaceChildren(
      el('form', { class: 'rename-form', onsubmit: save },
        input,
        el('button', { class: 'btn', type: 'button', onclick: showNormal }, 'Batal'),
        el('button', { class: 'btn primary', type: 'submit' }, 'Simpan'),
      ),
    );
    input.focus();
    input.select();
  }

  async function remove() {
    const note = category.total_count > 0
      ? `\n\n${category.total_count} tugas di kategori ini TIDAK ikut terhapus, hanya menjadi "tanpa kategori".`
      : '';
    if (!confirm(`Hapus kategori "${category.name}"?${note}`)) return;
    const ok = await attempt(() => api.deleteCategory(category.id).then(() => true));
    if (!ok) return;
    toast('Kategori dihapus');
    onChanged();
  }

  showNormal();
  return row;
}
