// Halaman "Fokus": timer pomodoro, pilihan tugas, riwayat sesi hari ini, dan durasi.

import { api } from '../api.js';
import { formatClock, formatDuration, formatTime, todayISO } from '../dates.js';
import { FOCUS_LOGGED, on } from '../events.js';
import * as timer from '../focus-timer.js';
import { icon } from '../icons.js';
import { attempt, el, toast } from '../ui.js';

const RING_RADIUS = 104;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;

const PHASE_LABEL = { work: 'Waktu fokus', break: 'Istirahat' };
const STATUS_LABEL = { idle: 'Siap dimulai', running: 'Berjalan', paused: 'Dijeda' };

function svg(tag, attrs) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

export const focusView = {
  path: 'fokus',
  title: 'Fokus',

  /** Dipanggil sekali saat aplikasi dibuka: timer harus siap di halaman mana pun. */
  init() {
    return timer.init();
  },

  /** Sisa waktu di menu samping & judul tab selama timer berjalan atau dijeda. */
  liveStatus(update) {
    timer.subscribe((s) => update(s.status === 'idle' ? '' : formatClock(s.remaining)));
  },

  async render(container, params) {
    // Dibuka dari tombol "Fokus" di jendela edit tugas: #/fokus?tugas=12
    const requestedTask = Number(params.get('tugas')) || null;
    if (requestedTask) {
      history.replaceState(null, '', '#/fokus');
      if (timer.getState().taskId !== requestedTask && !timer.setTask(requestedTask)) {
        toast('Timer sedang berjalan untuk tugas lain. Jeda atau hentikan dulu untuk mengganti tugas.', { error: true });
      }
    }

    const openTasks = (await attempt(() => api.listTasks({ status: 'open' }))) || [];

    // --- Lingkaran timer ---
    const progress = svg('circle', {
      class: 'ring-progress', cx: 120, cy: 120, r: RING_RADIUS,
      'stroke-dasharray': RING_LENGTH, 'stroke-dashoffset': 0,
    });
    const ring = svg('svg', { class: 'ring', viewBox: '0 0 240 240', 'aria-hidden': 'true' });
    ring.append(svg('circle', { class: 'ring-track', cx: 120, cy: 120, r: RING_RADIUS }), progress);

    const phaseLabel = el('span', { class: 'phase-pill' });
    const clock = el('div', { class: 'clock', role: 'timer', 'aria-live': 'off' });
    const statusLabel = el('div', { class: 'clock-status' });

    // --- Tombol ---
    const mainButton = el('button', { class: 'btn primary big', type: 'button' });
    const skipButton = el('button', { class: 'btn', type: 'button', onclick: () => timer.skip() },
      icon('skip', 18), 'Lewati');
    const stopButton = el('button', { class: 'btn', type: 'button', onclick: () => timer.stop() },
      icon('stop', 18), 'Berhenti');

    // --- Pilihan tugas ---
    const taskSelect = el('select', { class: 'input', 'aria-label': 'Tugas yang dikerjakan' });
    const taskTotal = el('p', { class: 'focus-task-total' });
    let taskTotals = new Map(openTasks.map((t) => [t.id, t.focus_seconds]));

    function fillTaskOptions(selectedId) {
      const options = [el('option', { value: '' }, 'Tanpa tugas')];
      const ids = new Set(openTasks.map((t) => t.id));
      for (const t of openTasks) options.push(el('option', { value: String(t.id) }, t.title));
      // Tugas yang dipilih sudah selesai/dihapus: tetap tampilkan supaya pilihan tidak hilang.
      if (selectedId && !ids.has(selectedId)) {
        options.push(el('option', { value: String(selectedId) }, '(tugas yang sudah selesai)'));
      }
      taskSelect.replaceChildren(...options);
      taskSelect.value = selectedId ? String(selectedId) : '';
    }

    taskSelect.addEventListener('change', () => {
      timer.setTask(taskSelect.value ? Number(taskSelect.value) : null);
    });

    // --- Menggambar ulang setiap detik ---
    function update(s) {
      const fraction = s.total ? s.remaining / s.total : 0;
      progress.setAttribute('stroke-dashoffset', String(RING_LENGTH * (1 - fraction)));
      card.classList.toggle('is-break', s.phase === 'break');
      card.classList.toggle('is-running', s.status === 'running');
      phaseLabel.textContent = PHASE_LABEL[s.phase];
      clock.textContent = formatClock(s.remaining);
      statusLabel.textContent = STATUS_LABEL[s.status];

      const label = s.status === 'running' ? 'Jeda' : s.status === 'paused' ? 'Lanjutkan' : 'Mulai';
      mainButton.replaceChildren(icon(s.status === 'running' ? 'pause' : 'play', 20), label);
      mainButton.onclick = s.status === 'running' ? timer.pause : timer.start;
      stopButton.disabled = s.status === 'idle' && s.phase === 'work';

      if (taskSelect.value !== (s.taskId ? String(s.taskId) : '') || !taskSelect.options.length) {
        fillTaskOptions(s.taskId);
      }
      taskSelect.disabled = s.status === 'running';
      taskSelect.title = s.status === 'running' ? 'Jeda timer dulu untuk mengganti tugas' : '';
      const total = s.taskId ? taskTotals.get(s.taskId) : null;
      taskTotal.textContent = total ? `Total fokus untuk tugas ini: ${formatDuration(total)}` : '';
    }

    const card = el('section', { class: 'focus-card' },
      phaseLabel,
      el('div', { class: 'ring-wrap' }, ring, el('div', { class: 'ring-center' }, clock, statusLabel)),
      el('div', { class: 'focus-controls' }, mainButton),
      el('div', { class: 'focus-controls secondary' }, skipButton, stopButton),
      el('label', { class: 'field focus-task' }, el('span', {}, 'Sedang mengerjakan'), taskSelect),
      taskTotal,
    );

    // --- Riwayat hari ini ---
    const historyArea = el('div');

    async function loadHistory() {
      const today = todayISO();
      const sessions = await attempt(() => api.listFocusSessions({ date: today }));
      if (!sessions) return;
      const total = sessions.reduce((sum, s) => sum + s.duration_seconds, 0);
      historyArea.replaceChildren(
        el('h2', { class: 'section-title' }, 'Hari ini',
          el('span', { class: 'section-count' },
            sessions.length ? `${sessions.length} sesi · ${formatDuration(total)}` : '')),
        sessions.length
          ? el('ul', { class: 'task-list session-list' }, sessions.map((s) => sessionRow(s, loadHistory)))
          : el('p', { class: 'empty' }, 'Belum ada sesi fokus hari ini.'),
      );
    }

    // Total per tugas ikut diperbarui setelah sesi baru dicatat.
    async function refreshTotals() {
      const tasks = await attempt(() => api.listTasks({ status: 'all' }));
      if (tasks) taskTotals = new Map(tasks.map((t) => [t.id, t.focus_seconds]));
      update(timer.getState());
    }

    container.replaceChildren(
      el('header', { class: 'view-header' },
        el('h1', {}, 'Fokus'),
        el('p', { class: 'subtitle' }, 'Kerja fokus, lalu istirahat sejenak. Timer tetap berjalan walau Anda pindah halaman.'),
      ),
      card,
      el('section', { class: 'task-section' }, historyArea),
      settingsSection(),
      notificationHint(),
    );

    const stopTimerUpdates = timer.subscribe(update);
    const stopListening = on(FOCUS_LOGGED, () => {
      loadHistory();
      refreshTotals();
    });
    await loadHistory();

    // Dipanggil saat pindah ke halaman lain.
    return () => {
      stopTimerUpdates();
      stopListening();
    };
  },
};

function sessionRow(session, onChanged) {
  async function remove() {
    if (!confirm('Hapus sesi ini dari riwayat?')) return;
    const ok = await attempt(() => api.deleteFocusSession(session.id).then(() => true));
    if (ok) onChanged();
  }
  return el('li', { class: 'task session-row' },
    el('span', { class: 'session-time' }, formatTime(session.ended_at)),
    el('div', { class: 'task-body' },
      el('div', { class: 'task-title' }, session.task_title || 'Tanpa tugas'),
      el('div', { class: 'category-count' },
        formatDuration(session.duration_seconds),
        session.completed ? '' : ' · dihentikan lebih awal'),
    ),
    el('div', { class: 'task-actions' },
      el('button', { class: 'icon-btn danger', type: 'button', title: 'Hapus dari riwayat', 'aria-label': 'Hapus sesi', onclick: remove },
        icon('trash', 18)),
    ),
  );
}

function settingsSection() {
  const { settings } = timer.getState();
  const workInput = el('input', {
    class: 'input', type: 'number', min: '1', max: '180', step: '1', required: true,
    value: String(settings.focus_work_minutes), inputmode: 'numeric',
  });
  const breakInput = el('input', {
    class: 'input', type: 'number', min: '1', max: '60', step: '1', required: true,
    value: String(settings.focus_break_minutes), inputmode: 'numeric',
  });

  async function save(event) {
    event.preventDefault();
    const ok = await attempt(() => timer.updateSettings({
      focus_work_minutes: Number(workInput.value),
      focus_break_minutes: Number(breakInput.value),
    }).then(() => true));
    if (!ok) return;
    const running = timer.getState().status !== 'idle';
    toast(running ? 'Durasi disimpan. Berlaku mulai sesi berikutnya.' : 'Durasi disimpan');
  }

  return el('details', { class: 'task-section focus-settings' },
    el('summary', { class: 'section-toggle' }, icon('chevron', 16), 'Atur durasi'),
    el('form', { class: 'settings-form', onsubmit: save },
      el('label', { class: 'field' }, el('span', {}, 'Fokus (menit)'), workInput),
      el('label', { class: 'field' }, el('span', {}, 'Istirahat (menit)'), breakInput),
      el('button', { class: 'btn primary', type: 'submit' }, 'Simpan'),
    ),
  );
}

/** Ajakan menyalakan notifikasi, supaya tetap diberi tahu saat bekerja di jendela lain. */
function notificationHint() {
  if (!('Notification' in window) || !window.isSecureContext || Notification.permission !== 'default') return '';
  const hint = el('p', { class: 'focus-hint' },
    'Ingin diberi tahu saat timer selesai walau sedang di jendela lain? ',
    el('button', {
      class: 'link-btn', type: 'button',
      onclick: async () => {
        await Notification.requestPermission();
        hint.remove();
      },
    }, 'Aktifkan notifikasi'),
  );
  return hint;
}
