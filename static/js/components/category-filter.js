// Deretan tombol filter kategori: Semua · Kerja · Pribadi · … · Tanpa kategori.
// Filter disimpan di alamat halaman, misalnya #/semua?kategori=3,
// sehingga bisa di-bookmark dan tetap ada saat halaman dimuat ulang.

import { icon } from '../icons.js';
import { el } from '../ui.js';

/**
 * Baca filter dari alamat halaman.
 * Hasil: { value, query, label, defaultCategory }
 *   value: null (semua) | 'none' (tanpa kategori) | nomor kategori
 */
export function readCategoryFilter(params, categories) {
  const raw = params.get('kategori');
  if (raw === 'none') {
    return { value: 'none', query: 'none', label: 'Tanpa kategori', defaultCategory: null };
  }
  const found = categories.find((c) => String(c.id) === raw);
  if (found) {
    return { value: found.id, query: String(found.id), label: found.name, defaultCategory: found.id };
  }
  return { value: null, query: undefined, label: null, defaultCategory: null };
}

export function categoryFilter(path, categories, active) {
  if (categories.length === 0) return null;

  const chip = (label, value) => {
    const href = value == null ? `#/${path}` : `#/${path}?kategori=${value}`;
    const isActive = active === value;
    return el('a', {
      class: `filter-chip${isActive ? ' active' : ''}`,
      href,
      'aria-current': isActive ? 'true' : null,
    }, label);
  };

  return el('nav', { class: 'category-filter', 'aria-label': 'Filter kategori' },
    chip('Semua', null),
    categories.map((c) => chip(c.name, c.id)),
    chip('Tanpa kategori', 'none'),
    el('a', { class: 'filter-chip subtle', href: '#/kategori', title: 'Kelola kategori' },
      icon('settings', 16), 'Atur'),
  );
}
