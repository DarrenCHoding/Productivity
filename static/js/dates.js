// Fungsi bantu tanggal. Tanggal disimpan sebagai teks 'YYYY-MM-DD' (zona waktu lokal).

function pad(n) {
  return String(n).padStart(2, '0');
}

/** Ubah objek Date menjadi 'YYYY-MM-DD' menurut waktu lokal. */
export function toISODate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Tanggal hari ini, 'YYYY-MM-DD'. */
export function todayISO() {
  return toISODate(new Date());
}

function parse(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** Tambah/kurangi hari: addDays('2026-10-04', 1) -> '2026-10-05'. */
export function addDays(iso, days) {
  const d = parse(iso);
  d.setDate(d.getDate() + days);
  return toISODate(d);
}

/** Selisih hari (b - a). */
export function daysBetween(a, b) {
  return Math.round((parse(b) - parse(a)) / 86400000);
}

/** Contoh: 'Sen, 6 Okt' (tahun ditampilkan bila bukan tahun ini). */
export function formatShort(iso) {
  const d = parse(iso);
  const options = { weekday: 'short', day: 'numeric', month: 'short' };
  if (d.getFullYear() !== new Date().getFullYear()) options.year = 'numeric';
  return d.toLocaleDateString('id-ID', options);
}

/** Contoh: 'Minggu, 4 Oktober 2026'. */
export function formatLong(iso) {
  return parse(iso).toLocaleDateString('id-ID', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });
}

/**
 * Keterangan deadline untuk ditampilkan.
 * Hasil: { label, state } dengan state 'overdue' | 'today' | 'tomorrow' | 'future'.
 */
export function describeDue(dueISO, today = todayISO()) {
  const diff = daysBetween(today, dueISO);
  if (diff < 0) {
    const late = -diff;
    return { state: 'overdue', label: late === 1 ? 'Kemarin · terlambat' : `Terlambat ${late} hari` };
  }
  if (diff === 0) return { state: 'today', label: 'Hari ini' };
  if (diff === 1) return { state: 'tomorrow', label: 'Besok' };
  return { state: 'future', label: formatShort(dueISO) };
}
