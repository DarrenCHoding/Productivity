// Pemberitahuan sederhana antarbagian aplikasi.
// Contoh: setelah daftar tugas dimuat ulang, menu samping ikut memperbarui angkanya.

const target = new EventTarget();

export function emit(name, detail) {
  target.dispatchEvent(new CustomEvent(name, { detail }));
}

export function on(name, handler) {
  target.addEventListener(name, (event) => handler(event.detail));
}

// Nama-nama pemberitahuan yang dipakai.
export const DATA_CHANGED = 'data-changed';
