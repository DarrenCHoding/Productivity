// Mesin timer fokus (pomodoro). Tidak menggambar tampilan apa pun;
// halaman "Fokus" dan menu samping cukup "berlangganan" lewat subscribe().
//
// Cara kerja:
// - Ada dua fase: 'work' (fokus) dan 'break' (istirahat).
// - Statusnya 'idle' (belum mulai), 'running' (berjalan), atau 'paused' (dijeda).
// - Saat berjalan, yang disimpan adalah jam selesainya (endsAt), bukan hitungan
//   mundur. Jadi waktu tetap tepat walaupun tab browser tidak aktif.
// - Keadaan timer disimpan di browser (localStorage), sehingga timer tetap jalan
//   saat pindah halaman atau memuat ulang. Riwayat sesi disimpan di server.
// - Setelah fase fokus selesai (atau dihentikan setelah minimal 1 menit), lamanya
//   dicatat ke server. Fase berikutnya disiapkan, lalu menunggu tombol Mulai.

import { api } from './api.js';
import { formatDuration } from './dates.js';
import { DATA_CHANGED, FOCUS_LOGGED, emit } from './events.js';
import { toast } from './ui.js';

const STORAGE_KEY = 'productivity.focusTimer';
const MIN_LOGGED_SECONDS = 60; // sesi yang dihentikan sebelum 1 menit tidak dicatat

let settings = { focus_work_minutes: 25, focus_break_minutes: 5 };
let state = freshState('work', null);
let endTimeout = null;
let audio = null;
const listeners = new Set();

function phaseLength(phase) {
  const minutes = phase === 'work' ? settings.focus_work_minutes : settings.focus_break_minutes;
  return minutes * 60 * 1000;
}

function freshState(phase, taskId) {
  const total = phaseLength(phase);
  return { phase, status: 'idle', total, remaining: total, endsAt: null, taskId };
}

function remainingNow() {
  return state.status === 'running' ? Math.max(0, state.endsAt - Date.now()) : state.remaining;
}

// ----- Penyimpanan di browser -----

function save() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* abaikan */ }
}

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved && ['work', 'break'].includes(saved.phase) && ['idle', 'running', 'paused'].includes(saved.status)) {
      return saved;
    }
  } catch { /* abaikan */ }
  return null;
}

// ----- Pemberitahuan ke tampilan -----

/** Keadaan timer saat ini (salinan). */
export function getState() {
  return { ...state, remaining: remainingNow(), settings: { ...settings } };
}

/** Dengarkan perubahan timer. Hasil: fungsi untuk berhenti mendengarkan. */
export function subscribe(listener) {
  listeners.add(listener);
  listener(getState());
  return () => listeners.delete(listener);
}

function changed() {
  save();
  const snapshot = getState();
  for (const listener of listeners) listener(snapshot);
}

// ----- Bunyi & notifikasi -----

function unlockAudio() {
  // Browser hanya mengizinkan suara setelah pengguna menekan tombol,
  // jadi "mesin suara" disiapkan saat tombol Mulai ditekan.
  try {
    audio = audio || new (window.AudioContext || window.webkitAudioContext)();
    if (audio.state === 'suspended') audio.resume();
  } catch { /* browser tanpa dukungan suara */ }
}

function chime() {
  if (!audio) return;
  try {
    const start = audio.currentTime;
    [0, 0.25, 0.5].forEach((offset, i) => {
      const osc = audio.createOscillator();
      const gain = audio.createGain();
      osc.frequency.value = i === 2 ? 1046 : 880;
      gain.gain.setValueAtTime(0.0001, start + offset);
      gain.gain.exponentialRampToValueAtTime(0.25, start + offset + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + offset + 0.2);
      osc.connect(gain).connect(audio.destination);
      osc.start(start + offset);
      osc.stop(start + offset + 0.22);
    });
  } catch { /* abaikan */ }
}

function announce(message) {
  chime();
  toast(message);
  try {
    if ('Notification' in window && Notification.permission === 'granted' && document.visibilityState !== 'visible') {
      new Notification('Productivity', { body: message });
    }
  } catch { /* abaikan */ }
}

// ----- Mencatat sesi ke server -----

async function logSession(seconds, completed, taskId) {
  seconds = Math.round(seconds);
  if (seconds < MIN_LOGGED_SECONDS) return;
  try {
    try {
      await api.logFocusSession({ task_id: taskId, duration_seconds: seconds, completed });
    } catch (err) {
      // Tugasnya mungkin sudah dihapus: tetap catat waktunya, tanpa tugas.
      if (taskId == null) throw err;
      await api.logFocusSession({ task_id: null, duration_seconds: seconds, completed });
    }
    emit(FOCUS_LOGGED);
    emit(DATA_CHANGED);
  } catch (err) {
    toast(`Sesi fokus gagal dicatat: ${err.message}`, { error: true });
  }
}

// ----- Jadwal selesai -----

function schedule() {
  clearTimeout(endTimeout);
  if (state.status === 'running') {
    endTimeout = setTimeout(checkFinished, Math.max(0, state.endsAt - Date.now()) + 50);
  }
}

function checkFinished() {
  if (state.status !== 'running' || remainingNow() > 0) return;

  // Bila aplikasi terbuka di beberapa tab, hanya satu tab yang boleh mencatat.
  const stored = load();
  if (stored && (stored.status !== 'running' || stored.endsAt !== state.endsAt)) {
    adopt(stored);
    return;
  }

  const finished = state;
  if (finished.phase === 'work') {
    state = freshState('break', finished.taskId);
    changed();
    logSession(finished.total / 1000, true, finished.taskId);
    announce(`Sesi fokus ${formatDuration(finished.total / 1000)} selesai. Waktunya istirahat!`);
  } else {
    state = freshState('work', finished.taskId);
    changed();
    announce('Istirahat selesai. Siap fokus lagi?');
  }
}

function adopt(saved) {
  state = saved;
  schedule();
  changed();
}

// ----- Tombol-tombol -----

export function start() {
  unlockAudio();
  if (state.status === 'running') return;
  state = { ...state, status: 'running', endsAt: Date.now() + state.remaining };
  schedule();
  changed();
}

export function pause() {
  if (state.status !== 'running') return;
  state = { ...state, status: 'paused', remaining: remainingNow(), endsAt: null };
  schedule();
  changed();
}

/** Hentikan dan kembali ke awal fase fokus. Waktu fokus yang sudah berjalan tetap dicatat. */
export function stop() {
  const current = { ...state, remaining: remainingNow() };
  state = freshState('work', current.taskId);
  schedule();
  changed();
  if (current.phase === 'work' && current.status !== 'idle') {
    const elapsed = (current.total - current.remaining) / 1000;
    if (elapsed >= MIN_LOGGED_SECONDS) toast(`${formatDuration(elapsed)} fokus dicatat`);
    logSession(elapsed, false, current.taskId);
  }
}

/** Lewati ke fase berikutnya. */
export function skip() {
  const current = { ...state, remaining: remainingNow() };
  state = freshState(current.phase === 'work' ? 'break' : 'work', current.taskId);
  schedule();
  changed();
  if (current.phase === 'work' && current.status !== 'idle') {
    logSession((current.total - current.remaining) / 1000, false, current.taskId);
  }
}

/** Kaitkan timer ke tugas (atau null). Hanya bisa saat timer tidak berjalan. */
export function setTask(taskId) {
  if (state.status === 'running') return false;
  state = { ...state, taskId };
  changed();
  return true;
}

/** Simpan durasi baru. Bila timer belum dimulai, tampilannya langsung ikut berubah. */
export async function updateSettings(values) {
  settings = await api.updateSettings(values);
  if (state.status === 'idle') state = freshState(state.phase, state.taskId);
  changed();
}

// ----- Mulai -----

let started = false;

/** Dipanggil sekali saat aplikasi dibuka. */
export async function init() {
  if (started) return;
  started = true;
  try {
    settings = await api.getSettings();
  } catch { /* pakai nilai bawaan */ }

  const saved = load();
  state = saved || freshState('work', null);
  if (state.status === 'idle') state = freshState(state.phase, state.taskId);

  // Tab lain mengubah timer: ikuti.
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return;
    const other = load();
    if (other) {
      state = other;
      schedule();
      for (const listener of listeners) listener(getState());
    }
  });

  // Perbarui tampilan tiap detik selama berjalan.
  setInterval(() => {
    if (state.status !== 'running') return;
    if (remainingNow() <= 0) checkFinished();
    else for (const listener of listeners) listener(getState());
  }, 1000);

  schedule();
  changed();
  // Timer sempat selesai saat aplikasi ditutup: selesaikan sekarang.
  checkFinished();
}
