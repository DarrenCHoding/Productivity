// Pemberitahuan sederhana antarbagian aplikasi.
// Contoh: setelah daftar tugas dimuat ulang, menu samping ikut memperbarui angkanya.

const target = new EventTarget();

export function emit(name, detail) {
  target.dispatchEvent(new CustomEvent(name, { detail }));
}

/** Dengarkan pemberitahuan. Hasil: fungsi untuk berhenti mendengarkan. */
export function on(name, handler) {
  const listener = (event) => handler(event.detail);
  target.addEventListener(name, listener);
  return () => target.removeEventListener(name, listener);
}

// Nama-nama pemberitahuan yang dipakai.
export const DATA_CHANGED = 'data-changed';
export const FOCUS_LOGGED = 'focus-logged'; // satu sesi fokus baru saja dicatat
