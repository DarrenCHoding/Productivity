// Tes mesin timer fokus (static/js/focus-timer.js).
// Jam dimajukan secara tiruan, jadi sesi 25 menit selesai dalam sekejap.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { flush, installFakeBrowser, loadFreshTimer } from './fake-browser.mjs';

const MINUTE = 60 * 1000;
const START = new Date(2026, 9, 4, 9, 0, 0).getTime();

/** Siapkan browser tiruan, jam tiruan, dan timer yang baru dibuka. */
async function setup(t, options) {
  const env = installFakeBrowser(options);
  t.mock.timers.enable({ apis: ['setTimeout', 'setInterval', 'Date'], now: START });
  const timer = await loadFreshTimer();
  await timer.init();
  return { env, timer, tick: async (ms) => { t.mock.timers.tick(ms); await flush(); } };
}

test('awal: fase fokus 25 menit, belum berjalan', async (t) => {
  const { timer } = await setup(t);
  const s = timer.getState();
  assert.equal(s.phase, 'work');
  assert.equal(s.status, 'idle');
  assert.equal(s.remaining, 25 * MINUTE);
});

test('durasi diambil dari pengaturan di server', async (t) => {
  const { timer } = await setup(t, { settings: { focus_work_minutes: 50, focus_break_minutes: 10 } });
  assert.equal(timer.getState().remaining, 50 * MINUTE);
});

test('sesi fokus selesai: dicatat ke server, lalu istirahat disiapkan (tidak langsung jalan)', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.setTask(1);
  timer.start();
  await tick(10 * MINUTE);
  assert.equal(timer.getState().remaining, 15 * MINUTE);
  await tick(15 * MINUTE + 100);

  assert.deepEqual(env.server.sessions, [{ task_id: 1, duration_seconds: 1500, completed: true }]);
  const s = timer.getState();
  assert.equal(s.phase, 'break');
  assert.equal(s.status, 'idle');
  assert.equal(s.remaining, 5 * MINUTE);
  assert.equal(s.taskId, 1);
  assert.ok(env.toasts.some((m) => m.includes('Sesi fokus 25 menit selesai')));
});

test('istirahat selesai: kembali ke fase fokus, tidak ada yang dicatat', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.skip(); // langsung ke istirahat
  timer.start();
  await tick(5 * MINUTE + 100);
  assert.equal(timer.getState().phase, 'work');
  assert.equal(timer.getState().status, 'idle');
  assert.equal(env.server.sessions.length, 0);
});

test('jeda menghentikan hitungan, lanjutkan meneruskannya', async (t) => {
  const { timer, tick } = await setup(t);
  timer.start();
  await tick(5 * MINUTE);
  timer.pause();
  await tick(30 * MINUTE); // lama dijeda: tidak dihitung
  assert.equal(timer.getState().status, 'paused');
  assert.equal(timer.getState().remaining, 20 * MINUTE);
  timer.start();
  await tick(5 * MINUTE);
  assert.equal(timer.getState().remaining, 15 * MINUTE);
});

test('berhenti setelah 12 menit: 12 menit dicatat sebagai sesi tidak selesai', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.setTask(2);
  timer.start();
  await tick(12 * MINUTE);
  timer.stop();
  await flush();
  assert.deepEqual(env.server.sessions, [{ task_id: 2, duration_seconds: 720, completed: false }]);
  assert.equal(timer.getState().phase, 'work');
  assert.equal(timer.getState().status, 'idle');
  assert.equal(timer.getState().remaining, 25 * MINUTE);
});

test('berhenti sebelum 1 menit: tidak dicatat', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.start();
  await tick(30 * 1000);
  timer.stop();
  await flush();
  assert.equal(env.server.sessions.length, 0);
});

test('lewati di tengah fokus: waktu yang sudah berjalan dicatat, lalu ke istirahat', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.start();
  await tick(5 * MINUTE);
  timer.skip();
  await flush();
  assert.deepEqual(env.server.sessions, [{ task_id: null, duration_seconds: 300, completed: false }]);
  assert.equal(timer.getState().phase, 'break');
});

test('tugas tidak bisa diganti saat timer berjalan, bisa saat dijeda', async (t) => {
  const { timer } = await setup(t);
  timer.setTask(1);
  timer.start();
  assert.equal(timer.setTask(2), false);
  assert.equal(timer.getState().taskId, 1);
  timer.pause();
  assert.equal(timer.setTask(2), true);
  assert.equal(timer.getState().taskId, 2);
});

test('muat ulang halaman: timer tetap berjalan dengan sisa waktu yang benar', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.setTask(1);
  timer.start();
  await tick(10 * MINUTE);

  const reloaded = await loadFreshTimer(); // localStorage tetap, memori mulai dari nol
  await reloaded.init();
  const s = reloaded.getState();
  assert.equal(s.status, 'running');
  assert.equal(s.taskId, 1);
  assert.equal(s.remaining, 15 * MINUTE);

  // Halaman lama dan baru sama-sama menunggu waktu habis: sesi tetap dicatat sekali saja.
  await tick(15 * MINUTE + 100);
  assert.equal(env.server.sessions.length, 1);
});

test('waktu habis saat aplikasi tertutup: sesi dicatat saat aplikasi dibuka lagi', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.start();
  await tick(1000);
  t.mock.timers.reset(); // "tutup" aplikasi: tidak ada timer yang berjalan lagi
  t.mock.timers.enable({ apis: ['setTimeout', 'setInterval', 'Date'], now: START + 2 * 60 * MINUTE });

  const reopened = await loadFreshTimer();
  await reopened.init();
  await flush();
  assert.deepEqual(env.server.sessions, [{ task_id: null, duration_seconds: 1500, completed: true }]);
  assert.equal(reopened.getState().phase, 'break');
});

test('tugasnya terhapus selama sesi: waktu tetap dicatat tanpa tugas', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.setTask(1);
  timer.start();
  env.server.taskIds.delete(1);
  await tick(25 * MINUTE + 100);
  assert.deepEqual(env.server.sessions, [{ task_id: null, duration_seconds: 1500, completed: true }]);
});

test('server mati saat sesi selesai: muncul pesan error, timer tetap lanjut ke istirahat', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.start();
  env.server.online = false;
  await tick(25 * MINUTE + 100);
  assert.equal(timer.getState().phase, 'break');
  assert.ok(env.toasts.some((m) => m.startsWith('Sesi fokus gagal dicatat')));
});

test('ubah durasi: langsung berlaku bila belum mulai, berlaku sesi berikutnya bila sedang berjalan', async (t) => {
  const { env, timer, tick } = await setup(t);
  await timer.updateSettings({ focus_work_minutes: 40 });
  assert.equal(timer.getState().remaining, 40 * MINUTE);
  assert.equal(env.server.settings.focus_work_minutes, 40);

  timer.start();
  await tick(10 * MINUTE);
  await timer.updateSettings({ focus_work_minutes: 15 });
  assert.equal(timer.getState().remaining, 30 * MINUTE); // sesi berjalan tidak berubah
  await tick(30 * MINUTE + 100);
  assert.equal(env.server.sessions[0].duration_seconds, 40 * 60);
});

test('dua tab: bila tab lain sudah menyelesaikan sesi, tab ini tidak mencatat lagi', async (t) => {
  const { env, timer, tick } = await setup(t);
  timer.start();
  await tick(MINUTE);
  // Tab lain menyelesaikan sesi lebih dulu dan menyimpan keadaan barunya.
  const saved = JSON.parse(env.storage.get('productivity.focusTimer'));
  env.storage.set('productivity.focusTimer', JSON.stringify({ ...saved, phase: 'break', status: 'idle', endsAt: null }));
  await tick(25 * MINUTE);
  assert.equal(env.server.sessions.length, 0);
  assert.equal(timer.getState().phase, 'break');
});
