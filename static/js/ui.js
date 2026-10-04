// Fungsi bantu kecil untuk membuat tampilan.

/**
 * Buat elemen HTML.
 *   el('button', { class: 'btn', onclick: fn }, 'Simpan')
 * Teks selalu dimasukkan sebagai teks biasa (aman dari kode berbahaya).
 */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith('on') && typeof value === 'function') {
      node.addEventListener(key.slice(2), value);
    } else if (key === 'class') {
      node.className = value;
    } else if (key in node && typeof value !== 'string') {
      node[key] = value;
    } else {
      node.setAttribute(key, value === true ? '' : value);
    }
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

let toastTimer;

/** Tampilkan pesan singkat di bawah layar. */
export function toast(message, { error = false } = {}) {
  const box = document.getElementById('toast');
  box.textContent = message;
  box.classList.toggle('error', error);
  box.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => box.classList.remove('show'), error ? 4000 : 2200);
}

/** Jalankan aksi; kalau gagal, tampilkan pesan error. */
export async function attempt(action) {
  try {
    return await action();
  } catch (err) {
    toast(err.message, { error: true });
    return undefined;
  }
}
