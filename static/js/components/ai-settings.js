// Bagian "Fitur AI" di halaman Pengaturan: nyala/mati, pilihan model,
// batas pemakaian bulanan, pemakaian bulan ini, dan uji koneksi.

import { api } from '../api.js';
import { icon } from '../icons.js';
import { attempt, el, toast } from '../ui.js';
import { aiBadge, modelName } from './ai-badge.js';
import { settingRow } from './setting-row.js';

const MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
  'Agustus', 'September', 'Oktober', 'November', 'Desember'];

function dollars(value, digits = 2) {
  return `$${Number(value).toLocaleString('id-ID', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

function monthLabel(month) {
  const [year, m] = month.split('-').map(Number);
  return `${MONTHS[m - 1]} ${year}`;
}

/** Petunjuk perbaikan untuk tiap masalah. */
const PROBLEM_HELP = {
  no_key: 'Lihat README.md bagian "Fitur AI" untuk cara membuat API key dan menaruhnya di file .env.',
  no_sdk: 'Lihat README.md bagian "Fitur AI", langkah memasang paket.',
  old_python: 'Pasang Python versi terbaru dari python.org. Fitur lain tetap bisa dipakai.',
};

export function aiSection() {
  const section = el('section', { class: 'task-section ai-settings' });
  let lastAnswer = null; // jawaban uji koneksi terakhir, tetap tampil setelah bagian ini digambar ulang

  async function load() {
    const status = await attempt(() => api.aiStatus());
    if (!status) return;
    section.replaceChildren(
      el('h2', { class: 'section-title' }, 'Fitur AI'),
      el('p', { class: 'section-note' },
        'Opsional. Memakai Claude dari Anthropic dan butuh API key berbayar. '
        + 'Semua fitur lain tetap bekerja penuh tanpa AI.'),
      statusLine(status),
      el('div', { class: 'settings-card' },
        toggleRow(status, load),
        ...Object.entries(status.tiers).map(([tier, info]) => modelRow(tier, info, status.models, load)),
        limitRow(status, load),
      ),
      usageBox(status),
      testBox(status, lastAnswer, (answer) => { lastAnswer = answer; load(); }),
      el('p', { class: 'section-note ai-privacy' },
        'Yang dikirim ke Anthropic hanya data yang dibutuhkan untuk tiap permintaan, bukan seluruh data Anda. '
        + 'API key disimpan di file .env di komputer ini dan tidak pernah dikirim ke browser. '
        + 'Hasil AI selalu ditandai "Usulan AI" dan tidak mengubah data apa pun tanpa persetujuan Anda.'),
    );
  }

  load();
  return section;
}

function statusLine(status) {
  if (status.ready) {
    return el('div', { class: 'ai-status ok' }, el('span', { class: 'dot' }), 'Siap dipakai');
  }
  const help = PROBLEM_HELP[status.problem.code];
  return el('div', { class: `ai-status ${status.problem.code === 'disabled' ? 'off' : 'warn'}` },
    el('span', { class: 'dot' }),
    el('div', {},
      el('div', {}, status.problem.message),
      help && el('div', { class: 'ai-help' }, help),
    ),
  );
}

async function saveSetting(values, message, reload) {
  const ok = await attempt(() => api.updateSettings(values).then(() => true));
  if (!ok) return;
  if (message) toast(message);
  reload();
}

function toggleRow(status, reload) {
  const toggle = el('input', {
    type: 'checkbox', class: 'switch', role: 'switch', checked: status.enabled,
    'aria-label': 'Nyalakan fitur AI',
  });
  toggle.addEventListener('change', () => saveSetting(
    { ai_enabled: toggle.checked },
    toggle.checked ? 'Fitur AI dinyalakan' : 'Fitur AI dimatikan',
    reload,
  ));
  return settingRow('sparkle', 'Nyalakan fitur AI',
    'Bila dimatikan, aplikasi tidak pernah menghubungi layanan AI.', toggle);
}

function modelRow(tier, info, models, reload) {
  const select = el('select', { class: 'input', 'aria-label': info.label },
    models.map((m) => el('option', { value: m.id }, m.label)));
  const chosen = models.find((m) => m.id === info.model);
  select.value = info.model;
  select.addEventListener('change', () => saveSetting(
    { [tier === 'simple' ? 'ai_model_simple' : 'ai_model_smart']: select.value },
    `Model untuk ${info.label.toLowerCase()} diganti`,
    reload,
  ));
  const description = tier === 'simple'
    ? 'Pekerjaan ringan yang sering, jadi sebaiknya model yang murah.'
    : 'Pekerjaan yang butuh penalaran, misalnya menyusun rencana.';
  const price = chosen
    ? ` Harga model ini per 1 juta token: ${dollars(chosen.input)} masukan, ${dollars(chosen.output)} keluaran.`
    : '';
  return settingRow(tier === 'simple' ? 'flag' : 'timer', info.label, description + price, select);
}

function limitRow(status, reload) {
  const input = el('input', {
    class: 'input limit-input', type: 'number', min: '0.5', max: '500', step: '0.5',
    value: String(status.limit_usd), inputmode: 'decimal', 'aria-label': 'Batas bulanan dalam dolar AS',
  });
  const form = el('form', {
    class: 'limit-form',
    onsubmit: (event) => {
      event.preventDefault();
      saveSetting({ ai_monthly_limit_usd: Number(input.value) }, 'Batas bulanan disimpan', reload);
    },
  }, el('span', { class: 'prefix' }, '$'), input, el('button', { class: 'btn', type: 'submit' }, 'Simpan'));
  return settingRow('history', 'Batas pemakaian per bulan',
    'Bila perkiraan biaya bulan ini mencapai batas, fitur AI berhenti sampai awal bulan depan.', form);
}

function usageBox(status) {
  const u = status.usage;
  const fraction = status.limit_usd ? Math.min(1, u.cost_usd / status.limit_usd) : 0;
  return el('div', { class: 'ai-usage' },
    el('div', { class: 'ai-usage-head' },
      el('span', {}, `Pemakaian ${monthLabel(u.month)}`),
      el('strong', {}, `${dollars(u.cost_usd, u.cost_usd < 1 ? 4 : 2)} dari ${dollars(status.limit_usd)}`),
    ),
    el('div', { class: `meter${fraction >= 1 ? ' full' : fraction >= 0.8 ? ' high' : ''}`, role: 'progressbar',
      'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': String(Math.round(fraction * 100)) },
    el('span', { style: `width:${(fraction * 100).toFixed(1)}%` })),
    el('div', { class: 'ai-usage-detail' },
      `${u.requests} permintaan${u.failed ? ` (${u.failed} gagal)` : ''} · `
      + `${u.input_tokens.toLocaleString('id-ID')} token masuk · ${u.output_tokens.toLocaleString('id-ID')} token keluar`),
    el('div', { class: 'ai-help' },
      'Ini perkiraan dari jumlah token. Tagihan resmi ada di platform.claude.com (menu Usage).'),
  );
}

function answerView(answer) {
  return el('div', { class: 'ai-answer' },
    aiBadge(answer.model, 'Jawaban AI'),
    el('p', {}, answer.text),
    el('div', { class: 'ai-help' }, `${modelName(answer.model)} · biaya ${dollars(answer.cost_usd, 4)}`),
  );
}

function testBox(status, lastAnswer, onAnswer) {
  const result = el('div', { class: 'ai-test-result' }, lastAnswer ? answerView(lastAnswer) : '');
  const button = el('button', { class: 'btn', type: 'button', disabled: !status.ready }, icon('sparkle', 18), 'Uji koneksi');
  button.addEventListener('click', async () => {
    button.disabled = true;
    result.replaceChildren(el('span', { class: 'ai-help' }, 'Menghubungi AI…'));
    try {
      onAnswer(await api.aiTest('simple')); // gambar ulang: pemakaian bulan ini ikut diperbarui
    } catch (err) {
      result.replaceChildren(el('p', { class: 'form-error' }, err.message));
    } finally {
      button.disabled = false;
    }
  });
  return el('div', { class: 'ai-test' },
    button,
    el('span', { class: 'ai-help' }, 'Mengirim satu permintaan kecil (kurang dari $0,01) untuk memastikan API key bekerja.'),
    result,
  );
}
